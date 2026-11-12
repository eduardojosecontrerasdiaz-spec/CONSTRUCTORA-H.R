import argparse
import logging
import sys
import sqlalchemy as sa
from flask import current_app

from app import create_app
from app.config.database import db
from app.services.precio_service import actualizar_precios_proveedor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("actualizar_precios_task")

PROVEEDOR_VALIDO = "easy_colombia"


def adquirir_bloqueo_proveedor(proveedor):
    """Adquiere un bloqueo nominal en MariaDB/MySQL usando una conexión dedicada con timeout 0.
    La rama SQLite funciona exclusivamente en pruebas unitarias mediante current_app.testing.
    Fuera de testing, SQLite es rechazado para evitar simular bloqueos en producción.
    """
    engine = db.engine
    lock_name = f"constructora_hr_precio_update_{proveedor.lower()}"
    
    if engine.dialect.name == 'sqlite':
        if not current_app or not current_app.testing:
            logger.error("SQLite no está permitido fuera del entorno de pruebas unitarias para control de exclusión mutua.")
            return None, None
        conn = engine.connect()
        return conn, 1

    conn = engine.connect()
    try:
        res = conn.execute(
            sa.text("SELECT GET_LOCK(:name, 0)"),
            {"name": lock_name}
        ).scalar()
        
        if res == 1:
            return conn, 1
        elif res == 0:
            conn.close()
            return None, 0
        else:
            conn.close()
            return None, None
    except Exception as exc:
        logger.error("Excepción técnica al adquirir GET_LOCK para proveedor '%s': %s", proveedor, exc)
        try:
            conn.close()
        except Exception:
            pass
        return None, None


def liberar_bloqueo_proveedor(conn, proveedor):
    """Libera el bloqueo nominal utilizando la misma conexión dedicada."""
    if conn is None:
        return False
    engine = db.engine
    lock_name = f"constructora_hr_precio_update_{proveedor.lower()}"

    if engine.dialect.name == 'sqlite':
        try:
            conn.close()
        except Exception:
            pass
        return True

    try:
        res = conn.execute(
            sa.text("SELECT RELEASE_LOCK(:name)"),
            {"name": lock_name}
        ).scalar()
        
        if res == 1:
            logger.info("Bloqueo '%s' liberado exitosamente.", lock_name)
            conn.close()
            return True
        else:
            logger.warning("RELEASE_LOCK para '%s' retornó un estado inusual (%s).", lock_name, res)
            conn.close()
            return False
    except Exception as exc:
        logger.error("Error crítico liberando bloqueo para proveedor '%s': %s. Invalidando conexión.", proveedor, exc)
        try:
            conn.invalidate()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        return False


def run_task(proveedor="easy_colombia"):
    """Función lógica de la tarea que gestiona códigos de salida y garantiza liberación de bloqueos."""
    prov_limpio = str(proveedor).strip().lower()
    if prov_limpio != PROVEEDOR_VALIDO:
        logger.error("Proveedor no contemplado en esta etapa: '%s'. El único proveedor soportado es '%s'.", proveedor, PROVEEDOR_VALIDO)
        return 1

    logger.info("Iniciando tarea de actualización de precios para el proveedor: '%s'", prov_limpio)
    conn_lock = None
    exit_code = 0
    try:
        conn_lock, lock_status = adquirir_bloqueo_proveedor(prov_limpio)
        
        if lock_status == 0:
            logger.info("Otra ejecución de actualización para el proveedor '%s' ya tiene el bloqueo. Omitiendo ejecución.", prov_limpio)
            return 0
        
        if lock_status is None:
            logger.error("Error técnico al intentar adquirir el bloqueo GET_LOCK para el proveedor '%s'.", prov_limpio)
            return 1

        logger.info("Bloqueo adquirido exitosamente para proveedor '%s'. Ejecutando actualización.", prov_limpio)
        resumen = actualizar_precios_proveedor(prov_limpio)
        logger.info("Actualización finalizada. Resumen: %s", resumen)

        if resumen.get("errores", 0) > 0:
            logger.error("La tarea finalizó con %s error(es) técnico(s) en el lote.", resumen["errores"])
            exit_code = 1
        else:
            exit_code = 0

    except Exception as exc:
        logger.critical("Error crítico durante la ejecución de la tarea de actualización para '%s': %s", prov_limpio, exc, exc_info=True)
        exit_code = 1
    finally:
        liberado = liberar_bloqueo_proveedor(conn_lock, prov_limpio)
        if not liberado and conn_lock is not None:
            logger.error("La liberación del bloqueo no pudo confirmarse adecuadamente. Forzando código de error 1.")
            exit_code = 1
        try:
            db.session.remove()
        except Exception:
            pass
        logger.info("Recursos liberados y sesión scoped cerrada para la tarea de '%s'.", prov_limpio)

    return exit_code


def main():
    parser = argparse.ArgumentParser(description="Ejecutor independiente de actualización de precios para Constructora H.R.")
    parser.add_argument("--proveedor", type=str, default=PROVEEDOR_VALIDO, choices=[PROVEEDOR_VALIDO], help=f"Identificador del proveedor (único permitido: {PROVEEDOR_VALIDO})")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        exit_code = run_task(args.proveedor)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()