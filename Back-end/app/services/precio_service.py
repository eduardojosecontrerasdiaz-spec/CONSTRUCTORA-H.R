from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import logging
import time
import urllib.error

from app.config.database import db
from app.models.material import Material
from app.models.material_proveedor import MaterialProveedor
from app.models.historial_precio_material import HistorialPrecioMaterial
from app.scrapers.scraper_manager import ScraperManager
from app.scrapers.base_scraper import ScraperConnectionError, ScraperHTTPError


logger = logging.getLogger(__name__)

MAX_PRECISION_12_4 = Decimal("99999999.9999")
MAX_PRECISION_14_2 = Decimal("999999999999.99")


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def _validar_identificador(valor, nombre):
    if isinstance(valor, bool):
        raise ValueError(f"{nombre} debe ser un entero positivo.")

    try:
        identificador = int(valor)
    except (ValueError, TypeError, OverflowError):
        raise ValueError(f"{nombre} debe ser un entero positivo.")

    if identificador <= 0 or str(valor).strip() != str(identificador):
        raise ValueError(f"{nombre} debe ser un entero positivo.")

    return identificador


def _validar_indices_paginacion(from_index, to_index):
    if (
        isinstance(from_index, bool)
        or not isinstance(from_index, int)
        or from_index < 0
    ):
        raise ValueError(
            "El índice 'from_index' debe ser un entero mayor o igual a 0."
        )

    if (
        isinstance(to_index, bool)
        or not isinstance(to_index, int)
        or to_index < from_index
    ):
        raise ValueError(
            "El índice 'to_index' debe ser un entero mayor o igual a 'from_index'."
        )

    num_resultados = (to_index - from_index) + 1

    if num_resultados > 50:
        raise ValueError(
            "Cada consulta está limitada a un máximo de 50 resultados."
        )

    return from_index, to_index


def _obtener_codigo_http(exc):
    """
    Obtiene el código HTTP de una excepción del scraper.

    Respeta el contrato original de ScraperHTTPError, que no necesita
    recibir status_code como argumento.

    Inspecciona las excepciones encadenadas mediante __cause__
    y __context__ para encontrar urllib.error.HTTPError.
    """

    status_code = getattr(exc, "status_code", None)

    if status_code is not None:
        return status_code

    pendientes = [exc]
    visitados = set()

    while pendientes:
        actual = pendientes.pop()

        if actual is None or id(actual) in visitados:
            continue

        visitados.add(id(actual))

        if isinstance(actual, urllib.error.HTTPError):
            return actual.code

        pendientes.append(getattr(actual, "__cause__", None))
        pendientes.append(getattr(actual, "__context__", None))

    return None


# ============================================================
# BÚSQUEDA DE PRODUCTOS
# ============================================================

def buscar_productos_proveedor(
    proveedor,
    termino_busqueda,
    from_index=0,
    to_index=10
):
    if not isinstance(proveedor, str) or not proveedor.strip():
        raise ValueError(
            "El identificador del proveedor debe ser una cadena de texto no vacía."
        )

    if not isinstance(termino_busqueda, str) or not termino_busqueda.strip():
        raise ValueError(
            "El término de búsqueda debe ser una cadena de texto no vacía."
        )

    _validar_indices_paginacion(from_index, to_index)

    manager = ScraperManager()

    try:
        resultados = manager.search(
            proveedor.strip().lower(),
            termino_busqueda.strip(),
            from_index=from_index,
            to_index=to_index
        )

        return resultados

    except Exception as exc:
        logger.error(
            "Error al buscar productos en proveedor '%s': %s",
            proveedor,
            exc
        )

        raise RuntimeError(
            f"Error al buscar productos en el proveedor '{proveedor}': {str(exc)}"
        ) from exc


# ============================================================
# ASOCIAR PRODUCTO CON MATERIAL
# ============================================================

def asociar_producto_material(
    id_material,
    producto,
    termino_busqueda,
    factor_conversion=None
):
    id_mat = _validar_identificador(
        id_material,
        "El identificador del material"
    )

    if not isinstance(producto, dict):
        raise ValueError(
            "Los datos del producto deben ser un diccionario."
        )

    if not isinstance(termino_busqueda, str) or not termino_busqueda.strip():
        raise ValueError("El término de búsqueda es obligatorio.")

    proveedor = producto.get("proveedor")
    sku = producto.get("sku")
    nombre_producto = producto.get("nombre")

    if not proveedor or not str(proveedor).strip():
        raise ValueError("El proveedor del producto es obligatorio.")

    if not sku or not str(sku).strip():
        raise ValueError("El SKU del producto es obligatorio.")

    if not nombre_producto or not str(nombre_producto).strip():
        raise ValueError("El nombre del producto es obligatorio.")

    proveedor_str = str(proveedor).strip().lower()
    sku_str = str(sku).strip()

    try:
        material = db.session.get(Material, id_mat)

        if material is None:
            raise ValueError(
                "El material interno indicado no existe."
            )

        existente = MaterialProveedor.query.filter_by(
            proveedor=proveedor_str,
            sku=sku_str
        ).first()

        if existente is not None:
            raise ValueError(
                "El producto con este proveedor y SKU ya se encuentra asociado."
            )

    except ValueError:
        db.session.rollback()
        raise

    except Exception as exc:
        db.session.rollback()

        logger.error(
            "Error de BD al asociar producto al material %s: %s",
            id_mat,
            exc
        )

        raise RuntimeError(
            "Error al consultar la base de datos durante la asociación."
        ) from exc

    # Validación del factor de conversión

    dec_factor = None

    if factor_conversion is not None:
        try:
            dec_factor = Decimal(str(factor_conversion))

            if (
                not dec_factor.is_finite()
                or dec_factor <= Decimal("0.0000")
            ):
                raise ValueError(
                    "El factor de conversión debe ser un número positivo y finito."
                )

            dec_factor = dec_factor.quantize(
                Decimal("0.0001"),
                rounding=ROUND_HALF_UP
            )

        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(
                "El factor de conversión debe ser un número válido, positivo y finito."
            )

        if dec_factor > MAX_PRECISION_12_4:
            raise ValueError(
                "El factor de conversión excede el límite permitido para Numeric(12,4)."
            )

    # Validación del multiplicador del proveedor

    raw_mult = (
        producto.get("multiplicador")
        if producto.get("multiplicador") is not None
        else producto.get("multiplicador_proveedor")
    )

    multiplicador = None

    if raw_mult is not None:

        if isinstance(raw_mult, bool):
            raise ValueError(
                "El multiplicador del proveedor no puede ser un booleano."
            )

        try:
            multiplicador = Decimal(str(raw_mult))

        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(
                "El multiplicador del proveedor debe ser un número válido."
            )

        if not multiplicador.is_finite():
            raise ValueError(
                "El multiplicador del proveedor debe ser un número finito."
            )

        try:
            multiplicador = multiplicador.quantize(
                Decimal("0.0001"),
                rounding=ROUND_HALF_UP
            )
        except InvalidOperation:
            raise ValueError(
                "El multiplicador del proveedor excede la precisión permitida."
            )

        if (
            multiplicador <= Decimal("0.0000")
            or multiplicador > MAX_PRECISION_12_4
        ):
            raise ValueError(
                "El multiplicador del proveedor debe ser positivo y estar dentro del rango Numeric(12,4)."
            )

    # Creación de la asociación

    try:
        material_proveedor = MaterialProveedor(
            id_material=id_mat,
            proveedor=proveedor_str,
            sku=sku_str,
            referencia=(
                str(producto.get("referencia")).strip()
                if producto.get("referencia")
                else None
            ),
            termino_busqueda=termino_busqueda.strip(),
            nombre_producto=str(nombre_producto).strip(),
            marca=(
                str(producto.get("marca")).strip()
                if producto.get("marca")
                else None
            ),
            enlace=(
                str(producto.get("enlace")).strip()
                if producto.get("enlace")
                else None
            ),
            unidad_proveedor=(
                str(producto.get("unidad")).strip()
                if producto.get("unidad")
                else None
            ),
            multiplicador_proveedor=multiplicador,
            factor_conversion=dec_factor,
            activo=True
        )

        db.session.add(material_proveedor)
        db.session.commit()

        return material_proveedor

    except ValueError:
        db.session.rollback()
        raise

    except Exception as exc:
        db.session.rollback()

        logger.error(
            "Error inesperado al asociar producto: %s",
            exc
        )

        raise RuntimeError(
            "Error inesperado al asociar el producto al material."
        ) from exc


# ============================================================
# ACTUALIZACIÓN INDIVIDUAL DE PRECIO
# ============================================================

def actualizar_precio_material_proveedor(id_material_proveedor):

    id_mp = _validar_identificador(
        id_material_proveedor,
        "El identificador de la asociación MaterialProveedor"
    )

    # --------------------------------------------------------
    # FASE 1: LECTURA INDEPENDIENTE
    # --------------------------------------------------------

    session_read = db.session.session_factory()

    try:
        mp = session_read.get(MaterialProveedor, id_mp)

        if mp is None or not mp.activo:
            return {
                "status": "no_encontrado",
                "mensaje": "La asociación no existe o no está activa."
            }

        mp_data = {
            "id_material_proveedor": mp.id_material_proveedor,
            "proveedor": mp.proveedor,
            "sku": mp.sku,
            "termino_busqueda": mp.termino_busqueda,
            "factor_conversion": mp.factor_conversion,
            "activo": mp.activo
        }

    except Exception as exc:
        session_read.rollback()

        logger.error(
            "Error de BD al consultar asociación ID %s: %s",
            id_mp,
            exc
        )

        raise RuntimeError(
            "Error al consultar la base de datos para obtener la asociación."
        ) from exc

    finally:
        session_read.close()

    # --------------------------------------------------------
    # FASE 2: CONSULTA HTTP SIN SESIONES ABIERTAS
    # --------------------------------------------------------

    manager = ScraperManager()

    max_intentos = 3
    intentos = 0
    resultados = None
    ultimo_error = None

    while intentos < max_intentos:

        intentos += 1

        try:
            resultados = manager.search(
                mp_data["proveedor"],
                mp_data["termino_busqueda"],
                from_index=0,
                to_index=49
            )

            ultimo_error = None
            break

        except Exception as exc:

            ultimo_error = exc
            reintentar = False

            if isinstance(exc, ScraperConnectionError):
                reintentar = True

            elif isinstance(exc, ScraperHTTPError):

                status_code = _obtener_codigo_http(exc)

                if status_code in (500, 502, 503, 504):
                    reintentar = True

            if not reintentar or intentos >= max_intentos:

                logger.error(
                    "Fallo definitivo o no reintentable al consultar proveedor "
                    "'%s' (intento %s/%s): %s",
                    mp_data["proveedor"],
                    intentos,
                    max_intentos,
                    exc
                )

                break

            logger.warning(
                "Fallo transitorio reintentable al consultar proveedor "
                "'%s' (intento %s/%s): %s. Reintentando...",
                mp_data["proveedor"],
                intentos,
                max_intentos,
                exc
            )

            time.sleep(1 * intentos)

    if ultimo_error is not None:

        raise RuntimeError(
            f"Error al consultar el proveedor '{mp_data['proveedor']}' "
            f"tras {intentos} intentos: {str(ultimo_error)}"
        ) from ultimo_error

    # --------------------------------------------------------
    # FASE 3: ESCRITURA INDEPENDIENTE
    # --------------------------------------------------------

    session_write = db.session.session_factory()

    try:

        query = (
            session_write.query(MaterialProveedor)
            .filter_by(id_material_proveedor=id_mp)
        )

        dialect_name = db.engine.dialect.name

        if dialect_name in ("mysql", "mariadb"):
            query = query.with_for_update()

        mp_actual = query.first()

        # Verificar que la asociación no haya cambiado durante
        # la solicitud HTTP.

        if (
            mp_actual is None
            or not mp_actual.activo
            or mp_actual.proveedor != mp_data["proveedor"]
            or mp_actual.sku != mp_data["sku"]
            or mp_actual.factor_conversion != mp_data["factor_conversion"]
        ):

            logger.warning(
                "Asociación ID %s cambió, fue desactivada o su factor "
                "de conversión fue modificado antes de persistir.",
                id_mp
            )

            session_write.rollback()

            return {
                "status": "omitido",
                "motivo": "asociacion_inactiva_o_modificada",
                "mensaje": (
                    "La asociación ya no está activa, fue modificada "
                    "o su factor de conversión cambió."
                )
            }

        # ----------------------------------------------------
        # FILTRAR COINCIDENCIAS EXACTAS DE SKU Y PROVEEDOR
        # ----------------------------------------------------

        ofertas_coincidentes = []

        for prod in resultados:

            if not isinstance(prod, dict):
                continue

            p_proveedor = str(
                prod.get("proveedor", "")
            ).strip().lower()

            p_sku = str(
                prod.get("sku", "")
            ).strip()

            if (
                p_proveedor == mp_data["proveedor"]
                and p_sku == mp_data["sku"]
            ):
                ofertas_coincidentes.append(prod)

        if not ofertas_coincidentes:

            session_write.rollback()

            return {
                "status": "sin_coincidencia",
                "mensaje": (
                    "No se encontró una coincidencia exacta "
                    "de proveedor y SKU."
                )
            }

        # ----------------------------------------------------
        # PROCESAR OFERTAS Y GUARDAR HISTORIAL
        # ----------------------------------------------------

        registros_guardados = 0

        for oferta in ofertas_coincidentes:

            raw_precio = oferta.get("precio")

            if raw_precio is None:
                continue

            try:
                precio = Decimal(
                    str(raw_precio)
                ).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                )

            except (InvalidOperation, ValueError, TypeError):
                continue

            if (
                not precio.is_finite()
                or precio <= Decimal("0.00")
                or precio > MAX_PRECISION_14_2
            ):
                continue

            # Precio de lista

            raw_precio_lista = oferta.get("precio_lista")
            precio_lista = None

            if raw_precio_lista is not None:

                try:
                    pl = Decimal(
                        str(raw_precio_lista)
                    ).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )

                    if (
                        pl.is_finite()
                        and Decimal("0.00") < pl <= MAX_PRECISION_14_2
                    ):
                        precio_lista = pl

                except (InvalidOperation, ValueError, TypeError):
                    pass

            # Disponibilidad

            disponibilidad = None
            raw_disp = oferta.get("disponibilidad")

            if raw_disp is not None and not isinstance(raw_disp, bool):

                try:

                    if isinstance(raw_disp, int):

                        if raw_disp >= 0:
                            disponibilidad = raw_disp

                    else:

                        s_disp = str(raw_disp).strip()

                        if (
                            "." not in s_disp
                            and "e" not in s_disp.lower()
                        ):

                            d_int = int(s_disp)

                            if d_int >= 0:
                                disponibilidad = d_int

                except (ValueError, TypeError):
                    disponibilidad = None

            # Información del vendedor

            vendedor = (
                str(oferta.get("vendedor")).strip()
                if oferta.get("vendedor")
                else None
            )

            seller_id = (
                str(oferta.get("seller_id")).strip()
                if oferta.get("seller_id")
                else None
            )

            seller_default = oferta.get("seller_default")

            if not isinstance(seller_default, bool):
                seller_default = None

            enlace = (
                str(oferta.get("enlace")).strip()
                if oferta.get("enlace")
                else None
            )

            # ------------------------------------------------
            # PRECIO POR UNIDAD DEL MATERIAL
            # ------------------------------------------------

            precio_por_unidad_material = None

            if mp_actual.factor_conversion is not None:

                try:

                    calculo = precio / mp_actual.factor_conversion

                    p_unidad = calculo.quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )

                    if (
                        p_unidad.is_finite()
                        and Decimal("0.00") < p_unidad <= MAX_PRECISION_14_2
                    ):
                        precio_por_unidad_material = p_unidad

                except (
                    InvalidOperation,
                    ValueError,
                    TypeError,
                    ZeroDivisionError
                ):
                    precio_por_unidad_material = None

            # ------------------------------------------------
            # CREAR REGISTRO HISTÓRICO
            # ------------------------------------------------

            historial = HistorialPrecioMaterial(
                id_material_proveedor=mp_actual.id_material_proveedor,
                precio=precio,
                precio_lista=precio_lista,
                disponibilidad=disponibilidad,
                vendedor=vendedor,
                seller_id=seller_id,
                seller_default=seller_default,
                precio_por_unidad_material=precio_por_unidad_material,
                enlace=enlace
            )

            session_write.add(historial)

            registros_guardados += 1

        # ----------------------------------------------------
        # COMPROBAR REGISTROS GUARDADOS
        # ----------------------------------------------------

        if registros_guardados == 0:

            session_write.rollback()

            return {
                "status": "sin_precio_valido",
                "mensaje": (
                    "Se encontró el SKU pero ninguna oferta "
                    "tenía un precio válido."
                )
            }

        # ----------------------------------------------------
        # COMMIT DE LA TRANSACCIÓN
        # ----------------------------------------------------

        session_write.commit()

        return {
            "status": "actualizado",
            "registros_guardados": registros_guardados
        }

    except Exception as exc:

        session_write.rollback()

        logger.error(
            "Error transaccional o de persistencia al actualizar historial "
            "para asociación ID %s: %s",
            id_mp,
            exc
        )

        raise RuntimeError(
            "Error al persistir el historial de precios."
        ) from exc

    finally:
        session_write.close()


# ============================================================
# ACTUALIZACIÓN MASIVA POR PROVEEDOR
# ============================================================

def actualizar_precios_proveedor(proveedor):

    if not isinstance(proveedor, str) or not proveedor.strip():
        raise ValueError(
            "El identificador del proveedor debe ser una cadena válida."
        )

    prov_key = proveedor.strip().lower()

    # --------------------------------------------------------
    # OBTENER ASOCIACIONES ACTIVAS
    # --------------------------------------------------------

    session_batch = db.session.session_factory()

    try:

        asociaciones = (
            session_batch.query(MaterialProveedor)
            .filter_by(
                proveedor=prov_key,
                activo=True
            )
            .all()
        )

        ids_asociaciones = [
            mp.id_material_proveedor
            for mp in asociaciones
        ]

    except Exception as exc:

        session_batch.rollback()

        logger.error(
            "Error al consultar asociaciones activas para proveedor '%s': %s",
            prov_key,
            exc
        )

        raise RuntimeError(
            "Error al consultar las asociaciones activas del proveedor."
        ) from exc

    finally:
        session_batch.close()

    # --------------------------------------------------------
    # PROCESAR ASOCIACIONES INDIVIDUALES
    # --------------------------------------------------------

    procesados = 0
    actualizados = 0
    registros_guardados = 0
    sin_coincidencia = 0
    sin_precio_valido = 0
    omitidos = 0
    errores = 0

    for id_mp in ids_asociaciones:

        procesados += 1

        try:

            resultado = actualizar_precio_material_proveedor(id_mp)

            status = resultado.get("status")

            if status == "actualizado":

                actualizados += 1

                registros_guardados += resultado.get(
                    "registros_guardados",
                    0
                )

            elif status == "sin_coincidencia":

                sin_coincidencia += 1

            elif status == "sin_precio_valido":

                sin_precio_valido += 1

            elif status in ("omitido", "no_encontrado"):

                omitidos += 1

            else:

                errores += 1

        except Exception as exc:

            errores += 1

            logger.error(
                "Fallo al actualizar asociación ID %s en lote: %s",
                id_mp,
                exc
            )

    return {
        "proveedor": prov_key,
        "procesados": procesados,
        "actualizados": actualizados,
        "registros_guardados": registros_guardados,
        "sin_coincidencia": sin_coincidencia,
        "sin_precio_valido": sin_precio_valido,
        "omitidos": omitidos,
        "errores": errores
    }


# ============================================================
# LISTAR HISTORIAL DE PRECIOS
# ============================================================

def listar_historial_precios(id_material_proveedor):

    id_mp = _validar_identificador(
        id_material_proveedor,
        "El identificador de la asociación MaterialProveedor"
    )

    try:

        mp = db.session.get(MaterialProveedor, id_mp)

        if mp is None:
            raise ValueError(
                "La asociación MaterialProveedor indicada no existe."
            )

        return (
            HistorialPrecioMaterial.query
            .filter_by(
                id_material_proveedor=id_mp
            )
            .order_by(
                HistorialPrecioMaterial.fecha_consulta.desc(),
                HistorialPrecioMaterial.id_historial.desc()
            )
            .all()
        )

    except ValueError:
        db.session.rollback()
        raise

    except Exception as exc:

        db.session.rollback()

        logger.error(
            "Error al listar historial para asociación ID %s: %s",
            id_mp,
            exc
        )

        raise RuntimeError(
            "Error al listar el historial de precios."
        ) from exc