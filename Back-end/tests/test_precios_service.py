import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime, timezone
import sqlite3
from flask import Flask
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

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


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class TestPreciosService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
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

    @patch("app.services.precio_service.ScraperManager")
    def test_buscar_productos_proveedor_exito(self, mock_scraper_manager_cls):
        """Verifica la búsqueda de productos mediante ScraperManager y validación de parámetros."""
        mock_instance = MagicMock()
        mock_instance.search.return_value = [{"nombre": "Cemento", "sku": "103"}]
        mock_scraper_manager_cls.return_value = mock_instance

        resultados = buscar_productos_proveedor("easy_colombia", "cemento", 0, 5)
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["sku"], "103")

        with self.assertRaises(ValueError):
            buscar_productos_proveedor("", "cemento")
        with self.assertRaises(ValueError):
            buscar_productos_proveedor("easy_colombia", "")
        with self.assertRaises(ValueError):
            buscar_productos_proveedor("easy_colombia", "cemento", from_index=0, to_index=60)

    def test_asociar_producto_material_exito(self):
        """Verifica la asociación correcta de un producto con un material existente."""
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

        mp = asociar_producto_material(material.id_material, producto, "cemento", factor_conversion=1.0)
        self.assertIsNotNone(mp.id_material_proveedor)
        self.assertEqual(mp.proveedor, "easy_colombia")
        self.assertEqual(mp.sku, "SKU-CEMENTO-01")

    def test_asociar_producto_material_inexistente_y_duplicado(self):
        """Verifica el rechazo de materiales inexistentes y asociaciones duplicadas (proveedor + SKU)."""
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
            asociar_producto_material(99999, producto, "arena")

        asociar_producto_material(material.id_material, producto, "arena")

        with self.assertRaises(ValueError):
            asociar_producto_material(material.id_material, producto, "arena lavada")

    def test_asociar_producto_material_factor_conversion_y_multiplicador_invalidos(self):
        """Verifica la validación estricta de factores de conversión y multiplicadores."""
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
            asociar_producto_material(material.id_material, producto, "ladrillo", factor_conversion=0)
        with self.assertRaises(ValueError):
            asociar_producto_material(material.id_material, producto, "ladrillo", factor_conversion=-5)

        with self.assertRaises(ValueError):
            asociar_producto_material(material.id_material, dict(producto, multiplicador=True), "ladrillo")
        with self.assertRaises(ValueError):
            asociar_producto_material(material.id_material, dict(producto, multiplicador=0), "ladrillo")
        with self.assertRaises(ValueError):
            asociar_producto_material(material.id_material, dict(producto, multiplicador=-2.5), "ladrillo")
        with self.assertRaises(ValueError):
            asociar_producto_material(material.id_material, dict(producto, multiplicador=999999999.0), "ladrillo")

    @patch("app.services.precio_service.ScraperManager")
    def test_actualizar_precio_sku_exacto_y_multiples_vendedores(self, mock_scraper_manager_cls):
        """Verifica la actualización usando SKU exacto y el almacenamiento independiente de múltiples vendedores."""
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
        mp = asociar_producto_material(material.id_material, producto, "varilla")

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

        res = actualizar_precio_material_proveedor(mp.id_material_proveedor)
        self.assertEqual(res["status"], "actualizado")
        self.assertEqual(res["registros_guardados"], 2)

        historiales = listar_historial_precios(mp.id_material_proveedor)
        self.assertEqual(len(historiales), 2)

    @patch("app.services.precio_service.ScraperManager")
    def test_actualizar_precio_sin_coincidencia_y_sin_precio_valido(self, mock_scraper_manager_cls):
        """Verifica estados sin_coincidencia y sin_precio_valido."""
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
        mp = asociar_producto_material(material.id_material, producto, "pintura")

        mock_instance = MagicMock()
        mock_instance.search.return_value = [{"proveedor": "easy_colombia", "sku": "SKU-OTRO", "precio": 55000.00}]
        mock_scraper_manager_cls.return_value = mock_instance

        res = actualizar_precio_material_proveedor(mp.id_material_proveedor)
        self.assertEqual(res["status"], "sin_coincidencia")

        mock_instance.search.return_value = [{"proveedor": "easy_colombia", "sku": "SKU-PINTURA", "precio": 0}]
        res2 = actualizar_precio_material_proveedor(mp.id_material_proveedor)
        self.assertEqual(res2["status"], "sin_precio_valido")

    @patch("app.services.precio_service.ScraperManager")
    def test_actualizar_precio_conversion_unidades_y_cero(self, mock_scraper_manager_cls):
        """Verifica conversión de precio por unidad y redondeo a cero (precio 0.01 con factor 1000.0 -> guardando NULL)."""
        material = Material(
            nombre="Cemento Conversión",
            unidad_medida="bulto",
            precio_material=Decimal("30000.00"),
            estado=True
        )
        db.session.add(material)
        db.session.commit()

        mp_con = asociar_producto_material(material.id_material, {"proveedor": "easy_colombia", "sku": "SKU-CF", "nombre": "C1"}, "c1", factor_conversion=2.5)
        mp_cero = asociar_producto_material(material.id_material, {"proveedor": "easy_colombia", "sku": "SKU-ZERO", "nombre": "C2"}, "c2", factor_conversion=1000.0)

        mock_instance = MagicMock()
        mock_instance.search.side_effect = lambda prov, term, **kwargs: [
            {"proveedor": prov, "sku": "SKU-CF", "precio": 75000.00} if term == "c1" else {"proveedor": prov, "sku": "SKU-ZERO", "precio": 0.01}
        ]
        mock_scraper_manager_cls.return_value = mock_instance

        actualizar_precio_material_proveedor(mp_con.id_material_proveedor)
        actualizar_precio_material_proveedor(mp_cero.id_material_proveedor)

        h_con = listar_historial_precios(mp_con.id_material_proveedor)[0]
        h_cero = listar_historial_precios(mp_cero.id_material_proveedor)[0]

        self.assertEqual(h_con.precio_por_unidad_material, Decimal("30000.00"))
        self.assertEqual(h_cero.precio, Decimal("0.01"))
        self.assertIsNone(h_cero.precio_por_unidad_material)

    @patch("app.services.precio_service.ScraperManager")
    def test_disponibilidad_fraccionaria_y_limites_numericos(self, mock_scraper_manager_cls):
        """Verifica rechazo de disponibilidad fraccionaria/booleana y validación de límites Numeric(14,2)."""
        material = Material(
            nombre="Mat Limites",
            unidad_medida="un",
            precio_material=Decimal("100.00"),
            estado=True
        )
        db.session.add(material)
        db.session.commit()

        mp = asociar_producto_material(material.id_material, {"proveedor": "easy_colombia", "sku": "SKU-LIM", "nombre": "L"}, "l")

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

        res = actualizar_precio_material_proveedor(mp.id_material_proveedor)
        self.assertEqual(res["status"], "actualizado")
        self.assertEqual(res["registros_guardados"], 1)

        historial = listar_historial_precios(mp.id_material_proveedor)[0]
        self.assertIsNone(historial.disponibilidad)
        self.assertEqual(historial.precio, Decimal("1000.00"))

    def test_actualizar_precio_error_commit_rollback(self):
        """Verifica que si ocurre un error en db.session.commit(), se ejecute rollback y no queden registros parciales."""
        material = Material(
            nombre="Mat Rollback",
            unidad_medida="un",
            precio_material=Decimal("100.00"),
            estado=True
        )
        db.session.add(material)
        db.session.commit()

        mp = asociar_producto_material(material.id_material, {"proveedor": "easy_colombia", "sku": "SKU-RB", "nombre": "RB"}, "rb")

        mock_instance = MagicMock()
        mock_instance.search.return_value = [{"proveedor": "easy_colombia", "sku": "SKU-RB", "precio": 1500.00}]

        with patch("app.services.precio_service.db.session.commit", side_effect=Exception("Fallo simulado en commit")):
            with patch("app.services.precio_service.ScraperManager", return_value=mock_instance):
                with self.assertRaises(RuntimeError):
                    actualizar_precio_material_proveedor(mp.id_material_proveedor)

        historiales = listar_historial_precios(mp.id_material_proveedor)
        self.assertEqual(len(historiales), 0)

    @patch("app.services.precio_service.ScraperManager")
    def test_actualizar_precio_asociacion_inactiva(self, mock_scraper_manager_cls):
        """Verifica que las asociaciones inactivas no sean procesadas."""
        material = Material(
            nombre="Inactivo Mat",
            unidad_medida="un",
            precio_material=Decimal("100.00"),
            estado=True
        )
        db.session.add(material)
        db.session.commit()

        producto = {"proveedor": "easy_colombia", "sku": "SKU-INAC", "nombre": "Inactivo"}
        mp = asociar_producto_material(material.id_material, producto, "inactivo")
        mp.activo = False
        db.session.commit()

        res = actualizar_precio_material_proveedor(mp.id_material_proveedor)
        self.assertEqual(res["status"], "no_encontrado")

        res_batch = actualizar_precios_proveedor("easy_colombia")
        self.assertEqual(res_batch["procesados"], 0)

    @patch("app.services.precio_service.ScraperManager")
    def test_actualizar_precios_proveedor_resumen_y_continua_ante_error(self, mock_scraper_manager_cls):
        """Verifica el resumen en batch y que un error en un producto no interrumpa a los demás."""
        material = Material(
            nombre="Batch Mat",
            unidad_medida="un",
            precio_material=Decimal("100.00"),
            estado=True
        )
        db.session.add(material)
        db.session.commit()

        asociar_producto_material(material.id_material, {"proveedor": "easy_colombia", "sku": "SKU-B1", "nombre": "B1"}, "b1")
        asociar_producto_material(material.id_material, {"proveedor": "easy_colombia", "sku": "SKU-B2", "nombre": "B2"}, "b2")

        mock_instance = MagicMock()
        def mock_search(prov, term, **kwargs):
            if term == "b1":
                raise ConnectionError("Fallo de red simulado")
            return [{"proveedor": prov, "sku": "SKU-B2", "precio": 2000.00}]

        mock_instance.search.side_effect = mock_search
        mock_scraper_manager_cls.return_value = mock_instance

        res = actualizar_precios_proveedor("easy_colombia")
        self.assertEqual(res["procesados"], 2)
        self.assertEqual(res["actualizados"], 1)
        self.assertEqual(res["errores"], 1)

    def test_material_precio_material_y_presupuestos_no_modificados(self):
        """Confirma que Material.precio_material y presupuestos no se alteran, respetando relaciones y limpieza."""
        rol = Rol(nombre="Arquitecto Test", descripcion="Rol", estado=True, fecha_creacion=datetime.now(timezone.utc))
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

        producto = {"proveedor": "easy_colombia", "sku": "SKU-INALT", "nombre": "Inalterable"}
        mp = asociar_producto_material(material.id_material, producto, "inalterable")

        with patch("app.services.precio_service.ScraperManager") as mock_sm:
            mock_inst = MagicMock()
            mock_inst.search.return_value = [{"proveedor": "easy_colombia", "sku": "SKU-INALT", "precio": 15000.00}]
            mock_sm.return_value = mock_inst

            actualizar_precio_material_proveedor(mp.id_material_proveedor)

        self.assertEqual(material.precio_material, precio_original_material)
        self.assertEqual(presupuesto.monto_total, monto_original_presupuesto)


if __name__ == "__main__":
    unittest.main()