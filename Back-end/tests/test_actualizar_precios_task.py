
import unittest
import urllib.error

from unittest.mock import patch, MagicMock
from decimal import Decimal
from flask import Flask

from app.config.database import db

from app.models.material import Material
from app.models.material_proveedor import MaterialProveedor
from app.models.historial_precio_material import HistorialPrecioMaterial

# Importar los demás modelos para registrar sus tablas
from app.models.presupuesto import Presupuesto
from app.models.version_presupuesto import VersionPresupuesto
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.proyecto import Proyecto

from app.services.precio_service import (
    actualizar_precio_material_proveedor,
    actualizar_precios_proveedor,
    listar_historial_precios
)

from app.tasks.actualizar_precios import (
    adquirir_bloqueo_proveedor,
    liberar_bloqueo_proveedor,
    run_task
)

from app.scrapers.base_scraper import (
    ScraperHTTPError,
    ScraperConnectionError,
    ScraperError
)


# ============================================================
# AUXILIAR PARA SIMULAR ERRORES HTTP
# ============================================================

def crear_scraper_http_error(status_code):
    """
    Construye un ScraperHTTPError respetando el contrato original
    del scraper.

    El código HTTP se obtiene mediante la excepción original
    urllib.error.HTTPError encadenada en __cause__.
    """

    mensajes = {
        404: "Not Found",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout"
    }

    mensaje = mensajes.get(status_code, "HTTP Error")

    http_error = urllib.error.HTTPError(
        "https://www.easy.com.co/api/catalog_system/pub/products/search",
        status_code,
        mensaje,
        None,
        None
    )

    error = ScraperHTTPError(
        f"Error HTTP {status_code}: {mensaje}"
    )

    error.__cause__ = http_error

    return error


# ============================================================
# PRUEBAS DE LA TAREA AUTOMATIZADA
# ============================================================

class TestActualizarPreciosTask(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)

        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        cls.app.config["TESTING"] = True

        db.init_app(cls.app)

        with cls.app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.drop_all()

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.rollback()

        db.session.query(HistorialPrecioMaterial).delete()
        db.session.query(MaterialProveedor).delete()
        db.session.query(Material).delete()

        db.session.query(Presupuesto).delete()
        db.session.query(Proyecto).delete()
        db.session.query(Usuario).delete()
        db.session.query(Rol).delete()

        db.session.commit()
        self.app_context.pop()

    # ========================================================
    # BLOQUEOS SQLITE PARA PRUEBAS
    # ========================================================

    def test_adquirir_y_liberar_bloqueo_sqlite_testing(self):
        """Verifica la adaptación SQLite cuando testing=True."""

        self.app.testing = True

        conn, status = adquirir_bloqueo_proveedor(
            "easy_colombia"
        )

        self.assertEqual(status, 1)
        self.assertIsNotNone(conn)

        liberado = liberar_bloqueo_proveedor(
            conn,
            "easy_colombia"
        )

        self.assertTrue(liberado)

    def test_sqlite_rechazado_fuera_de_testing(self):
        """Verifica que SQLite sea rechazado fuera de pruebas."""

        self.app.testing = False

        conn, status = adquirir_bloqueo_proveedor(
            "easy_colombia"
        )

        self.assertIsNone(conn)
        self.assertIsNone(status)

        self.app.testing = True

    # ========================================================
    # VALIDACIÓN DEL PROVEEDOR
    # ========================================================

    def test_proveedor_invalido_restringido_cli(self):
        """Verifica que solo se permita easy_colombia."""

        code = run_task("proveedor_desconocido")

        self.assertEqual(code, 1)

    # ========================================================
    # BLOQUEOS GET_LOCK Y RELEASE_LOCK
    # ========================================================

    @patch("app.tasks.actualizar_precios.db.engine.connect")
    def test_get_lock_ocupado_omite_servicio(self, mock_connect):
        """Verifica que un bloqueo ocupado omita la actualización."""

        mock_conn = MagicMock()

        mock_conn.execute.return_value.scalar.return_value = 0
        mock_connect.return_value = mock_conn

        with patch(
            "app.tasks.actualizar_precios.db.engine.dialect.name",
            "mysql"
        ):
            with patch(
                "app.tasks.actualizar_precios.actualizar_precios_proveedor"
            ) as mock_actualizar:

                code = run_task("easy_colombia")

                self.assertEqual(code, 0)
                mock_actualizar.assert_not_called()

    @patch("app.tasks.actualizar_precios.db.engine.connect")
    def test_ejecucion_exitosa_get_lock_release_lock_1(self, mock_connect):
        """Verifica adquisición, ejecución y liberación exitosa."""

        mock_conn = MagicMock()

        mock_conn.execute.return_value.scalar.side_effect = [1, 1]
        mock_connect.return_value = mock_conn

        with patch(
            "app.tasks.actualizar_precios.db.engine.dialect.name",
            "mysql"
        ):
            with patch(
                "app.tasks.actualizar_precios.actualizar_precios_proveedor",
                return_value={
                    "procesados": 1,
                    "actualizados": 1,
                    "errores": 0
                }
            ) as mock_actualizar:

                code = run_task("easy_colombia")

                self.assertEqual(code, 0)

                mock_actualizar.assert_called_once_with(
                    "easy_colombia"
                )

                self.assertGreaterEqual(
                    mock_conn.execute.call_count,
                    2
                )

    @patch("app.tasks.actualizar_precios.db.engine.connect")
    def test_excepcion_servicio_intenta_liberar_bloqueo(self, mock_connect):
        """Verifica la liberación del bloqueo ante una excepción."""

        mock_conn = MagicMock()

        mock_conn.execute.return_value.scalar.side_effect = [1, 1]
        mock_connect.return_value = mock_conn

        with patch(
            "app.tasks.actualizar_precios.db.engine.dialect.name",
            "mysql"
        ):
            with patch(
                "app.tasks.actualizar_precios.actualizar_precios_proveedor",
                side_effect=RuntimeError("Fallo en servicio")
            ):

                code = run_task("easy_colombia")

                self.assertEqual(code, 1)

                self.assertGreaterEqual(
                    mock_conn.execute.call_count,
                    2
                )

    @patch("app.tasks.actualizar_precios.db.engine.connect")
    def test_get_lock_devuelve_null(self, mock_connect):
        """Verifica que GET_LOCK NULL se trate como error técnico."""

        mock_conn = MagicMock()

        mock_conn.execute.return_value.scalar.return_value = None
        mock_connect.return_value = mock_conn

        with patch(
            "app.tasks.actualizar_precios.db.engine.dialect.name",
            "mysql"
        ):
            code = run_task("easy_colombia")

            self.assertEqual(code, 1)

    # ========================================================
    # REINTENTOS POR ERRORES DEL SCRAPER
    # ========================================================

    @patch("app.services.precio_service.ScraperManager")
    def test_scraper_connection_error_con_tres_intentos(
        self,
        mock_scraper_manager_cls
    ):
        """Verifica tres intentos ante ScraperConnectionError."""

        material = Material(
            nombre="Mat Conn",
            unidad_medida="un",
            precio_material=Decimal("1000.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        mp = MaterialProveedor(
            id_material=material.id_material,
            proveedor="easy_colombia",
            sku="SKU-CONN",
            termino_busqueda="conn",
            nombre_producto="Prod Conn",
            activo=True
        )

        db.session.add(mp)
        db.session.commit()

        mock_instance = MagicMock()

        mock_instance.search.side_effect = ScraperConnectionError(
            "Error de conexión con proveedor"
        )

        mock_scraper_manager_cls.return_value = mock_instance

        with self.assertRaises(RuntimeError):
            actualizar_precio_material_proveedor(
                mp.id_material_proveedor
            )

        self.assertEqual(
            mock_instance.search.call_count,
            3
        )

    @patch("app.services.precio_service.ScraperManager")
    def test_http_error_404_sin_reintento(
        self,
        mock_scraper_manager_cls
    ):
        """Verifica que HTTP 404 genere exactamente un intento."""

        material = Material(
            nombre="Mat 404",
            unidad_medida="un",
            precio_material=Decimal("1000.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        mp = MaterialProveedor(
            id_material=material.id_material,
            proveedor="easy_colombia",
            sku="SKU-404",
            termino_busqueda="404",
            nombre_producto="Prod 404",
            activo=True
        )

        db.session.add(mp)
        db.session.commit()

        mock_instance = MagicMock()

        mock_instance.search.side_effect = crear_scraper_http_error(
            404
        )

        mock_scraper_manager_cls.return_value = mock_instance

        with self.assertRaises(RuntimeError):
            actualizar_precio_material_proveedor(
                mp.id_material_proveedor
            )

        self.assertEqual(
            mock_instance.search.call_count,
            1,
            "HTTP 404 no debe generar reintentos."
        )

    @patch("app.services.precio_service.ScraperManager")
    def test_http_error_503_con_reintentos(
        self,
        mock_scraper_manager_cls
    ):
        """Verifica tres intentos ante HTTP 503."""

        material = Material(
            nombre="Mat 503",
            unidad_medida="un",
            precio_material=Decimal("1000.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        mp = MaterialProveedor(
            id_material=material.id_material,
            proveedor="easy_colombia",
            sku="SKU-503",
            termino_busqueda="503",
            nombre_producto="Prod 503",
            activo=True
        )

        db.session.add(mp)
        db.session.commit()

        mock_instance = MagicMock()

        mock_instance.search.side_effect = (
            lambda *args, **kwargs: (_ for _ in ()).throw(
                crear_scraper_http_error(503)
            )
        )

        mock_scraper_manager_cls.return_value = mock_instance

        with self.assertRaises(RuntimeError):
            actualizar_precio_material_proveedor(
                mp.id_material_proveedor
            )

        self.assertEqual(
            mock_instance.search.call_count,
            3,
            "HTTP 503 debe generar exactamente tres intentos."
        )

    @patch("app.services.precio_service.ScraperManager")
    def test_error_inesperado_sin_reintentos(
        self,
        mock_scraper_manager_cls
    ):
        """Verifica que ScraperError inesperado no se reintente."""

        material = Material(
            nombre="Mat Unexpected",
            unidad_medida="un",
            precio_material=Decimal("1000.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        mp = MaterialProveedor(
            id_material=material.id_material,
            proveedor="easy_colombia",
            sku="SKU-UNEXPECTED",
            termino_busqueda="unexpected",
            nombre_producto="Prod Unexpected",
            activo=True
        )

        db.session.add(mp)
        db.session.commit()

        mock_instance = MagicMock()

        mock_instance.search.side_effect = ScraperError(
            "Error inesperado general del scraper"
        )

        mock_scraper_manager_cls.return_value = mock_instance

        with self.assertRaises(RuntimeError):
            actualizar_precio_material_proveedor(
                mp.id_material_proveedor
            )

        self.assertEqual(
            mock_instance.search.call_count,
            1
        )

    # ========================================================
    # SESIONES INDEPENDIENTES
    # ========================================================

    @patch("app.services.precio_service.db.session")
    def test_sesiones_independientes_lectura_y_escritura(
        self,
        mock_db_session
    ):
        """Comprueba el uso de sesiones independientes."""

        mock_session_factory = MagicMock()

        mock_read_session = MagicMock()
        mock_write_session = MagicMock()

        mock_mp = MaterialProveedor(
            id_material_proveedor=1,
            id_material=1,
            proveedor="easy_colombia",
            sku="SKU-SEP",
            termino_busqueda="sep",
            activo=True
        )

        mock_read_session.get.return_value = mock_mp

        mock_write_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_mp
        )

        mock_session_factory.side_effect = [
            mock_read_session,
            mock_write_session
        ]

        mock_db_session.session_factory = mock_session_factory

        with patch(
            "app.services.precio_service.ScraperManager"
        ) as mock_mgr_cls:

            mock_mgr = MagicMock()

            mock_mgr.search.return_value = [
                {
                    "proveedor": "easy_colombia",
                    "sku": "SKU-SEP",
                    "precio": 15000.00
                }
            ]

            mock_mgr_cls.return_value = mock_mgr

            resultado = actualizar_precio_material_proveedor(1)

            self.assertEqual(
                resultado["status"],
                "actualizado"
            )

            mock_read_session.close.assert_called_once()

            mock_write_session.commit.assert_called_once()
            mock_write_session.close.assert_called_once()

    # ========================================================
    # ASOCIACIÓN MODIFICADA DURANTE CONSULTA HTTP
    # ========================================================

    @patch("app.services.precio_service.ScraperManager")
    def test_asociacion_modificada_durante_solicitud_http(
        self,
        mock_scraper_manager_cls
    ):
        """Comprueba que una asociación modificada no genere historial."""

        material = Material(
            nombre="Mat Mod",
            unidad_medida="un",
            precio_material=Decimal("1000.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        mp = MaterialProveedor(
            id_material=material.id_material,
            proveedor="easy_colombia",
            sku="SKU-MOD",
            termino_busqueda="mod",
            nombre_producto="Prod Mod",
            activo=True
        )

        db.session.add(mp)
        db.session.commit()

        id_mp = mp.id_material_proveedor

        def mock_search_side_effect(*args, **kwargs):

            session_mod = db.session.session_factory()

            try:
                mp_db = session_mod.get(
                    MaterialProveedor,
                    id_mp
                )

                mp_db.activo = False

                session_mod.commit()

            finally:
                session_mod.close()

            return [
                {
                    "proveedor": "easy_colombia",
                    "sku": "SKU-MOD",
                    "precio": 5000.00
                }
            ]

        mock_instance = MagicMock()

        mock_instance.search.side_effect = mock_search_side_effect

        mock_scraper_manager_cls.return_value = mock_instance

        resultado = actualizar_precio_material_proveedor(id_mp)

        self.assertEqual(
            resultado["status"],
            "omitido"
        )

        self.assertEqual(
            resultado["motivo"],
            "asociacion_inactiva_o_modificada"
        )

        historiales = listar_historial_precios(id_mp)

        self.assertEqual(
            len(historiales),
            0
        )


if __name__ == "__main__":
    unittest.main()
