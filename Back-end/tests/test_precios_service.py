
import unittest
import sqlite3

from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime, timezone

from flask import Flask
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.config.database import db

from app.models.material import Material
from app.models.material_proveedor import MaterialProveedor
from app.models.historial_precio_material import HistorialPrecioMaterial
from app.models.presupuesto import Presupuesto
from app.models.version_presupuesto import VersionPresupuesto
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.proyecto import Proyecto

from app.services.precio_service import (
    buscar_productos_proveedor,
    asociar_producto_material,
    actualizar_precio_material_proveedor,
    actualizar_precios_proveedor,
    listar_historial_precios
)


# ============================================================
# CONFIGURACIÓN DE SQLITE PARA LAS PRUEBAS
# ============================================================

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Activa las claves foráneas en SQLite."""

    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ============================================================
# PRUEBAS DEL SERVICIO DE PRECIOS
# ============================================================

class TestPreciosService(unittest.TestCase):

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
    # 1. BÚSQUEDA DE PRODUCTOS
    # ========================================================

    @patch("app.services.precio_service.ScraperManager")
    def test_buscar_productos_proveedor_exito(self, mock_scraper_manager_cls):
        """Verifica la búsqueda de productos mediante ScraperManager."""

        mock_instance = MagicMock()

        mock_instance.search.return_value = [
            {
                "nombre": "Cemento",
                "sku": "103"
            }
        ]

        mock_scraper_manager_cls.return_value = mock_instance

        resultados = buscar_productos_proveedor(
            "easy_colombia",
            "cemento",
            0,
            5
        )

        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["sku"], "103")

        with self.assertRaises(ValueError):
            buscar_productos_proveedor("", "cemento")

        with self.assertRaises(ValueError):
            buscar_productos_proveedor("easy_colombia", "")

        with self.assertRaises(ValueError):
            buscar_productos_proveedor(
                "easy_colombia",
                "cemento",
                from_index=0,
                to_index=60
            )

    # ========================================================
    # 2. ASOCIACIÓN EXITOSA DE PRODUCTO
    # ========================================================

    def test_asociar_producto_material_exito(self):
        """Verifica la asociación correcta de un producto con un material."""

        material = Material(
            nombre="Cemento Interno",
            unidad_medida="bulto",
            precio_material=Decimal("30000.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        producto = {
            "proveedor": "easy_colombia",
            "sku": "SKU-CEMENTO-01",
            "nombre": "Cemento Cemex Super",
            "marca": "CEMEX",
            "referencia": "REF-123",
            "enlace": "https://easy.com.co/prod",
            "unidad": "un",
            "multiplicador": 1.0
        }

        mp = asociar_producto_material(
            material.id_material,
            producto,
            "cemento",
            factor_conversion=1.0
        )

        self.assertIsNotNone(mp.id_material_proveedor)
        self.assertEqual(mp.proveedor, "easy_colombia")
        self.assertEqual(mp.sku, "SKU-CEMENTO-01")

    # ========================================================
    # 3. MATERIAL INEXISTENTE Y ASOCIACIÓN DUPLICADA
    # ========================================================

    def test_asociar_producto_material_inexistente_y_duplicado(self):
        """Verifica el rechazo de materiales inexistentes y SKU duplicados."""

        material = Material(
            nombre="Arena Interna",
            unidad_medida="m3",
            precio_material=Decimal("50000.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        producto = {
            "proveedor": "easy_colombia",
            "sku": "SKU-ARENA",
            "nombre": "Arena Lavada"
        }

        with self.assertRaises(ValueError):
            asociar_producto_material(
                99999,
                producto,
                "arena"
            )

        asociar_producto_material(
            material.id_material,
            producto,
            "arena"
        )

        with self.assertRaises(ValueError):
            asociar_producto_material(
                material.id_material,
                producto,
                "arena lavada"
            )

    # ========================================================
    # 4. VALIDACIÓN DE FACTOR Y MULTIPLICADOR
    # ========================================================

    def test_asociar_producto_material_factor_conversion_y_multiplicador_invalidos(self):
        """Verifica la validación de factores y multiplicadores."""

        material = Material(
            nombre="Ladrillo Interno",
            unidad_medida="unidad",
            precio_material=Decimal("1000.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        producto = {
            "proveedor": "easy_colombia",
            "sku": "SKU-LAD",
            "nombre": "Ladrillo"
        }

        with self.assertRaises(ValueError):
            asociar_producto_material(
                material.id_material,
                producto,
                "ladrillo",
                factor_conversion=0
            )

        with self.assertRaises(ValueError):
            asociar_producto_material(
                material.id_material,
                producto,
                "ladrillo",
                factor_conversion=-5
            )

        with self.assertRaises(ValueError):
            asociar_producto_material(
                material.id_material,
                dict(producto, multiplicador=True),
                "ladrillo"
            )

        with self.assertRaises(ValueError):
            asociar_producto_material(
                material.id_material,
                dict(producto, multiplicador=0),
                "ladrillo"
            )

        with self.assertRaises(ValueError):
            asociar_producto_material(
                material.id_material,
                dict(producto, multiplicador=-2.5),
                "ladrillo"
            )

        with self.assertRaises(ValueError):
            asociar_producto_material(
                material.id_material,
                dict(producto, multiplicador=999999999.0),
                "ladrillo"
            )

    # ========================================================
    # 5. SKU EXACTO Y MÚLTIPLES VENDEDORES
    # ========================================================

    @patch("app.services.precio_service.ScraperManager")
    def test_actualizar_precio_sku_exacto_y_multiples_vendedores(
        self,
        mock_scraper_manager_cls
    ):
        """Verifica SKU exacto y almacenamiento independiente de vendedores."""

        material = Material(
            nombre="Varilla Interna",
            unidad_medida="unidad",
            precio_material=Decimal("20000.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        producto = {
            "proveedor": "easy_colombia",
            "sku": "SKU-VAR",
            "nombre": "Varilla Corrugada"
        }

        mp = asociar_producto_material(
            material.id_material,
            producto,
            "varilla"
        )

        mock_instance = MagicMock()

        mock_instance.search.return_value = [
            {
                "proveedor": "easy_colombia",
                "sku": "SKU-VAR",
                "precio": 25000.00,
                "vendedor": "Vendedor A",
                "seller_id": "1",
                "seller_default": True,
                "disponibilidad": 100
            },
            {
                "proveedor": "easy_colombia",
                "sku": "SKU-VAR",
                "precio": 24500.00,
                "vendedor": "Vendedor B",
                "seller_id": "2",
                "seller_default": False,
                "disponibilidad": 50
            }
        ]

        mock_scraper_manager_cls.return_value = mock_instance

        resultado = actualizar_precio_material_proveedor(
            mp.id_material_proveedor
        )

        self.assertEqual(resultado["status"], "actualizado")
        self.assertEqual(resultado["registros_guardados"], 2)

        historiales = listar_historial_precios(
            mp.id_material_proveedor
        )

        self.assertEqual(len(historiales), 2)

    # ========================================================
    # 6. SIN COINCIDENCIA Y SIN PRECIO VÁLIDO
    # ========================================================

    @patch("app.services.precio_service.ScraperManager")
    def test_actualizar_precio_sin_coincidencia_y_sin_precio_valido(
        self,
        mock_scraper_manager_cls
    ):
        """Verifica los estados sin_coincidencia y sin_precio_valido."""

        material = Material(
            nombre="Pintura Interna",
            unidad_medida="galon",
            precio_material=Decimal("60000.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        producto = {
            "proveedor": "easy_colombia",
            "sku": "SKU-PINTURA",
            "nombre": "Pintura Blanca"
        }

        mp = asociar_producto_material(
            material.id_material,
            producto,
            "pintura"
        )

        mock_instance = MagicMock()

        mock_instance.search.return_value = [
            {
                "proveedor": "easy_colombia",
                "sku": "SKU-OTRO",
                "precio": 55000.00
            }
        ]

        mock_scraper_manager_cls.return_value = mock_instance

        resultado = actualizar_precio_material_proveedor(
            mp.id_material_proveedor
        )

        self.assertEqual(
            resultado["status"],
            "sin_coincidencia"
        )

        mock_instance.search.return_value = [
            {
                "proveedor": "easy_colombia",
                "sku": "SKU-PINTURA",
                "precio": 0
            }
        ]

        resultado2 = actualizar_precio_material_proveedor(
            mp.id_material_proveedor
        )

        self.assertEqual(
            resultado2["status"],
            "sin_precio_valido"
        )

    # ========================================================
    # 7. CONVERSIÓN DE UNIDADES Y REDONDEO A CERO
    # ========================================================

    @patch("app.services.precio_service.ScraperManager")
    def test_actualizar_precio_conversion_unidades_y_cero(
        self,
        mock_scraper_manager_cls
    ):
        """Verifica conversión de precios y redondeo a cero."""

        material = Material(
            nombre="Cemento Conversión",
            unidad_medida="bulto",
            precio_material=Decimal("30000.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        mp_con = asociar_producto_material(
            material.id_material,
            {
                "proveedor": "easy_colombia",
                "sku": "SKU-CF",
                "nombre": "C1"
            },
            "c1",
            factor_conversion=2.5
        )

        mp_cero = asociar_producto_material(
            material.id_material,
            {
                "proveedor": "easy_colombia",
                "sku": "SKU-ZERO",
                "nombre": "C2"
            },
            "c2",
            factor_conversion=1000.0
        )

        mock_instance = MagicMock()

        def mock_search(proveedor, termino, **kwargs):
            if termino == "c1":
                return [
                    {
                        "proveedor": proveedor,
                        "sku": "SKU-CF",
                        "precio": 75000.00
                    }
                ]

            return [
                {
                    "proveedor": proveedor,
                    "sku": "SKU-ZERO",
                    "precio": 0.01
                }
            ]

        mock_instance.search.side_effect = mock_search
        mock_scraper_manager_cls.return_value = mock_instance

        actualizar_precio_material_proveedor(
            mp_con.id_material_proveedor
        )

        actualizar_precio_material_proveedor(
            mp_cero.id_material_proveedor
        )

        historial_conversion = listar_historial_precios(
            mp_con.id_material_proveedor
        )[0]

        historial_cero = listar_historial_precios(
            mp_cero.id_material_proveedor
        )[0]

        self.assertEqual(
            historial_conversion.precio_por_unidad_material,
            Decimal("30000.00")
        )

        self.assertEqual(
            historial_cero.precio,
            Decimal("0.01")
        )

        self.assertIsNone(
            historial_cero.precio_por_unidad_material
        )

    # ========================================================
    # 8. DISPONIBILIDAD FRACCIONARIA Y LÍMITES NUMÉRICOS
    # ========================================================

    @patch("app.services.precio_service.ScraperManager")
    def test_disponibilidad_fraccionaria_y_limites_numericos(
        self,
        mock_scraper_manager_cls
    ):
        """Verifica disponibilidad y límites Numeric(14,2)."""

        material = Material(
            nombre="Mat Limites",
            unidad_medida="un",
            precio_material=Decimal("100.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        mp = asociar_producto_material(
            material.id_material,
            {
                "proveedor": "easy_colombia",
                "sku": "SKU-LIM",
                "nombre": "L"
            },
            "l"
        )

        mock_instance = MagicMock()

        mock_instance.search.return_value = [
            {
                "proveedor": "easy_colombia",
                "sku": "SKU-LIM",
                "precio": 1000.00,
                "disponibilidad": 10.5
            },
            {
                "proveedor": "easy_colombia",
                "sku": "SKU-LIM",
                "precio": 99999999999999.00
            }
        ]

        mock_scraper_manager_cls.return_value = mock_instance

        resultado = actualizar_precio_material_proveedor(
            mp.id_material_proveedor
        )

        self.assertEqual(resultado["status"], "actualizado")
        self.assertEqual(resultado["registros_guardados"], 1)

        historial = listar_historial_precios(
            mp.id_material_proveedor
        )[0]

        self.assertIsNone(historial.disponibilidad)

        self.assertEqual(
            historial.precio,
            Decimal("1000.00")
        )

    # ========================================================
    # 9. ERROR DE COMMIT Y ROLLBACK REAL
    # ========================================================

    def test_actualizar_precio_error_commit_rollback(self):
        """
        Verifica que un fallo después del flush:
        - Ejecute rollback real.
        - Cierre las sesiones independientes.
        - No deje registros históricos parciales.
        """

        # Crear material real en SQLite.

        material = Material(
            nombre="Mat Rollback",
            unidad_medida="un",
            precio_material=Decimal("100.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        # Crear asociación real.

        producto = {
            "proveedor": "easy_colombia",
            "sku": "SKU-RB",
            "nombre": "Material Rollback"
        }

        mp = asociar_producto_material(
            material.id_material,
            producto,
            "rollback"
        )

        id_mp = mp.id_material_proveedor

        # Guardar la fábrica original de sesiones.

        factory_original = db.session.session_factory
        sesiones_creadas = []

        def factory_spy(*args, **kwargs):

            sesion = factory_original(*args, **kwargs)
            sesiones_creadas.append(sesion)

            # Primera sesión: lectura.

            if len(sesiones_creadas) == 1:

                close_original = sesion.close

                sesion.close = MagicMock(
                    wraps=close_original
                )

            # Segunda sesión: escritura.

            elif len(sesiones_creadas) == 2:

                flush_original = sesion.flush

                flush_spy = MagicMock(
                    wraps=flush_original
                )

                sesion.flush = flush_spy

                def commit_falla_despues_de_flush(
                    *args,
                    **kwargs
                ):

                    flush_spy(*args, **kwargs)

                    raise RuntimeError(
                        "Fallo simulado después del flush"
                    )

                sesion.commit = MagicMock(
                    side_effect=commit_falla_despues_de_flush
                )

                rollback_original = sesion.rollback
                close_original = sesion.close

                sesion.rollback = MagicMock(
                    wraps=rollback_original
                )

                sesion.close = MagicMock(
                    wraps=close_original
                )

            return sesion

        # Provocar el error durante el commit.

        with patch.object(
            db.session,
            "session_factory",
            side_effect=factory_spy
        ):

            with patch(
                "app.services.precio_service.ScraperManager"
            ) as mock_mgr_cls:

                mock_mgr = MagicMock()

                mock_mgr.search.return_value = [
                    {
                        "proveedor": "easy_colombia",
                        "sku": "SKU-RB",
                        "precio": Decimal("1500.00"),
                        "vendedor": "Easy",
                        "seller_id": "1",
                        "seller_default": True
                    }
                ]

                mock_mgr_cls.return_value = mock_mgr

                with self.assertRaises(RuntimeError) as ctx:

                    actualizar_precio_material_proveedor(id_mp)

                self.assertIn(
                    "Error al persistir el historial de precios",
                    str(ctx.exception)
                )

        # Verificar las sesiones independientes.

        self.assertEqual(len(sesiones_creadas), 2)

        session_read = sesiones_creadas[0]
        session_write = sesiones_creadas[1]

        session_read.close.assert_called_once()

        # SQLAlchemy puede ejecutar flush más de una vez.
        self.assertGreaterEqual(
            session_write.flush.call_count,
            1,
            "La sesión de escritura debe ejecutar flush."
        )

        session_write.commit.assert_called_once()
        session_write.rollback.assert_called()
        session_write.close.assert_called()

        # Consultar desde una tercera sesión independiente.

        session_verificacion = factory_original()

        try:

            registros = (
                session_verificacion.query(HistorialPrecioMaterial)
                .filter_by(id_material_proveedor=id_mp)
                .all()
            )

            self.assertEqual(
                len(registros),
                0,
                "El rollback dejó registros históricos parciales."
            )

        finally:
            session_verificacion.close()

    # ========================================================
    # 10. ASOCIACIÓN INACTIVA
    # ========================================================

    @patch("app.services.precio_service.ScraperManager")
    def test_actualizar_precio_asociacion_inactiva(
        self,
        mock_scraper_manager_cls
    ):
        """Verifica que las asociaciones inactivas no sean procesadas."""

        material = Material(
            nombre="Inactivo Mat",
            unidad_medida="un",
            precio_material=Decimal("100.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        producto = {
            "proveedor": "easy_colombia",
            "sku": "SKU-INAC",
            "nombre": "Inactivo"
        }

        mp = asociar_producto_material(
            material.id_material,
            producto,
            "inactivo"
        )

        mp.activo = False
        db.session.commit()

        resultado = actualizar_precio_material_proveedor(
            mp.id_material_proveedor
        )

        self.assertEqual(
            resultado["status"],
            "no_encontrado"
        )

        resultado_batch = actualizar_precios_proveedor(
            "easy_colombia"
        )

        self.assertEqual(
            resultado_batch["procesados"],
            0
        )

    # ========================================================
    # 11. ACTUALIZACIÓN MASIVA Y CONTINUIDAD ANTE ERRORES
    # ========================================================

    @patch("app.services.precio_service.ScraperManager")
    def test_actualizar_precios_proveedor_resumen_y_continua_ante_error(
        self,
        mock_scraper_manager_cls
    ):
        """Verifica resumen batch y continuidad ante errores."""

        material = Material(
            nombre="Batch Mat",
            unidad_medida="un",
            precio_material=Decimal("100.00"),
            estado=True
        )

        db.session.add(material)
        db.session.commit()

        asociar_producto_material(
            material.id_material,
            {
                "proveedor": "easy_colombia",
                "sku": "SKU-B1",
                "nombre": "B1"
            },
            "b1"
        )

        asociar_producto_material(
            material.id_material,
            {
                "proveedor": "easy_colombia",
                "sku": "SKU-B2",
                "nombre": "B2"
            },
            "b2"
        )

        mock_instance = MagicMock()

        def mock_search(proveedor, termino, **kwargs):

            if termino == "b1":
                raise ConnectionError(
                    "Fallo de red simulado"
                )

            return [
                {
                    "proveedor": proveedor,
                    "sku": "SKU-B2",
                    "precio": 2000.00
                }
            ]

        mock_instance.search.side_effect = mock_search
        mock_scraper_manager_cls.return_value = mock_instance

        resultado = actualizar_precios_proveedor(
            "easy_colombia"
        )

        self.assertEqual(resultado["procesados"], 2)
        self.assertEqual(resultado["actualizados"], 1)
        self.assertEqual(resultado["errores"], 1)

    # ========================================================
    # 12. PROTECCIÓN DEL PRECIO INTERNO Y PRESUPUESTOS
    # ========================================================

    def test_material_precio_material_y_presupuestos_no_modificados(self):
        """
        Confirma que Material.precio_material y los presupuestos
        no se alteren durante la actualización de precios.
        """

        rol = Rol(
            nombre="Arquitecto Test",
            descripcion="Rol",
            estado=True,
            fecha_creacion=datetime.now(timezone.utc)
        )

        db.session.add(rol)
        db.session.flush()

        usuario = Usuario(
            id_rol=rol.id_rol,
            nombre="Miguel",
            apellido="Osorio",
            correo="miguel@arquitecto.com",
            contrasena="hash",
            estado=True,
            fecha_creacion=datetime.now(timezone.utc)
        )

        db.session.add(usuario)
        db.session.flush()

        proyecto = Proyecto(
            id_usuario=usuario.id_usuario,
            nombre="Proyecto Constructor",
            cliente="Cliente X",
            estado="activo",
            fecha_creacion=datetime.now(timezone.utc)
        )

        db.session.add(proyecto)
        db.session.flush()

        material = Material(
            nombre="Inalterable Mat",
            unidad_medida="un",
            precio_material=Decimal("10000.00"),
            estado=True
        )

        db.session.add(material)

        presupuesto = Presupuesto(
            id_proyecto=proyecto.id_proyecto,
            fecha=datetime.now(timezone.utc),
            monto_total=Decimal("10000.00"),
            categoria="Obras",
            estado="borrador"
        )

        db.session.add(presupuesto)
        db.session.commit()

        precio_original_material = material.precio_material
        monto_original_presupuesto = presupuesto.monto_total

        producto = {
            "proveedor": "easy_colombia",
            "sku": "SKU-INALT",
            "nombre": "Inalterable"
        }

        mp = asociar_producto_material(
            material.id_material,
            producto,
            "inalterable"
        )

        with patch(
            "app.services.precio_service.ScraperManager"
        ) as mock_sm:

            mock_inst = MagicMock()

            mock_inst.search.return_value = [
                {
                    "proveedor": "easy_colombia",
                    "sku": "SKU-INALT",
                    "precio": 15000.00
                }
            ]

            mock_sm.return_value = mock_inst

            actualizar_precio_material_proveedor(
                mp.id_material_proveedor
            )

        self.assertEqual(
            material.precio_material,
            precio_original_material
        )

        self.assertEqual(
            presupuesto.monto_total,
            monto_original_presupuesto
        )


if __name__ == "__main__":
    unittest.main()
