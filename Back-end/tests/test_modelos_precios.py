import unittest
from datetime import datetime, timezone
from decimal import Decimal
import sqlite3
from flask import Flask
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from app.config.database import db
from app.models.material import Material
from app.models.material_proveedor import MaterialProveedor
from app.models.historial_precio_material import HistorialPrecioMaterial


# Habilitar PRAGMA foreign_keys=ON exclusivamente cuando la conexión sea SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class TestModelosPrecios(unittest.TestCase):

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
        db.session.commit()
        self.app_context.pop()

    def test_importacion_y_modelos(self):
        """Verifica que los modelos se puedan importar y registrar correctamente."""
        self.assertIsNotNone(MaterialProveedor)
        self.assertIsNotNone(HistorialPrecioMaterial)

    def test_relaciones_material_y_proveedor(self):
        """Verifica las relaciones entre Material, MaterialProveedor e HistorialPrecioMaterial."""
        material = Material(
            nombre="Cemento Gris Test",
            unidad_medida="bulto",
            precio_material=Decimal("30000.00"),
            estado=True
        )
        db.session.add(material)
        db.session.commit()

        mat_prov = MaterialProveedor(
            id_material=material.id_material,
            proveedor="easy_colombia",
            sku="1035302",
            termino_busqueda="cemento",
            nombre_producto="Cemento Cemex 50K"
        )
        db.session.add(mat_prov)
        db.session.commit()

        historial = HistorialPrecioMaterial(
            id_material_proveedor=mat_prov.id_material_proveedor,
            precio=Decimal("32600.00"),
            fecha_consulta=datetime.now(timezone.utc)
        )
        db.session.add(historial)
        db.session.commit()

        self.assertEqual(len(material.materiales_proveedores), 1)
        self.assertEqual(material.materiales_proveedores[0].sku, "1035302")
        self.assertEqual(mat_prov.material.nombre, "Cemento Gris Test")
        self.assertEqual(len(mat_prov.historial_precios), 1)
        self.assertEqual(mat_prov.historial_precios[0].precio, Decimal("32600.00"))

    def test_restriccion_unica_proveedor_sku_multiproveedor(self):
        """Verifica la unicidad multiproveedor: mismo SKU no puede repetirse en el mismo proveedor, pero sí en distintos."""
        material = Material(
            nombre="Arena Test Multiproveedor",
            unidad_medida="m3",
            precio_material=Decimal("50000.00"),
            estado=True
        )
        db.session.add(material)
        db.session.commit()

        mp1 = MaterialProveedor(
            id_material=material.id_material,
            proveedor="easy_colombia",
            sku="SKU-SHARED-01",
            termino_busqueda="arena",
            nombre_producto="Arena lavada Easy"
        )
        db.session.add(mp1)
        db.session.commit()

        # Intentar duplicar el mismo SKU para el mismo proveedor (Debe fallar con IntegrityError)
        mp_duplicado = MaterialProveedor(
            id_material=material.id_material,
            proveedor="easy_colombia",
            sku="SKU-SHARED-01",
            termino_busqueda="arena fina",
            nombre_producto="Arena fina Easy"
        )
        db.session.add(mp_duplicado)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # El mismo SKU sí debe permitirse para un proveedor diferente (Arquitectura multiproveedor)
        mp_otro_proveedor = MaterialProveedor(
            id_material=material.id_material,
            proveedor="homecenter_colombia",
            sku="SKU-SHARED-01",
            termino_busqueda="arena",
            nombre_producto="Arena lavada Homecenter"
        )
        db.session.add(mp_otro_proveedor)
        db.session.commit()
        self.assertEqual(mp_otro_proveedor.sku, "SKU-SHARED-01")
        self.assertEqual(mp_otro_proveedor.proveedor, "homecenter_colombia")

    def test_factor_conversion_y_campos_opcionales_nulos(self):
        """Verifica que los campos opcionales acepten NULL y que cuando factor_conversion es NULL, el precio por unidad sea NULL."""
        material = Material(
            nombre="Varilla Test",
            unidad_medida="varilla",
            precio_material=Decimal("25000.00"),
            estado=True
        )
        db.session.add(material)
        db.session.commit()

        # Caso A: factor_conversion es NULL -> precio_por_unidad_material permanece NULL
        mat_prov_null = MaterialProveedor(
            id_material=material.id_material,
            proveedor="easy_colombia",
            sku="VAR-NULL",
            termino_busqueda="varilla",
            nombre_producto="Varilla 3/8",
            factor_conversion=None,
            multiplicador_proveedor=None,
            referencia=None,
            marca=None,
            enlace=None,
            unidad_proveedor=None
        )
        db.session.add(mat_prov_null)
        db.session.commit()

        hist_null = HistorialPrecioMaterial(
            id_material_proveedor=mat_prov_null.id_material_proveedor,
            precio=Decimal("260000.00"),
            precio_por_unidad_material=None,
            precio_lista=None,
            disponibilidad=None,
            vendedor=None,
            seller_id=None,
            seller_default=None,
            enlace=None,
            fecha_consulta=datetime.now(timezone.utc)
        )
        db.session.add(hist_null)
        db.session.commit()

        self.assertIsNone(mat_prov_null.factor_conversion)
        self.assertIsNone(hist_null.precio_por_unidad_material)

        # Caso B: factor_conversion conocido (ej. paquete de 10) con precio por unidad calculado proporcionalmente
        factor = Decimal("10.0000")
        precio_paquete = Decimal("260000.00")
        precio_unitario_calculado = precio_paquete / factor

        mat_prov_factor = MaterialProveedor(
            id_material=material.id_material,
            proveedor="easy_colombia",
            sku="VAR-PACK",
            termino_busqueda="varilla paquete",
            nombre_producto="Paquete Varillas",
            factor_conversion=factor
        )
        db.session.add(mat_prov_factor)
        db.session.commit()

        hist_factor = HistorialPrecioMaterial(
            id_material_proveedor=mat_prov_factor.id_material_proveedor,
            precio=precio_paquete,
            precio_por_unidad_material=precio_unitario_calculado,
            fecha_consulta=datetime.now(timezone.utc)
        )
        db.session.add(hist_factor)
        db.session.commit()

        self.assertEqual(mat_prov_factor.factor_conversion, Decimal("10.0000"))
        self.assertEqual(hist_factor.precio_por_unidad_material, Decimal("26000.00"))

    def test_cotizaciones_multiples_independientes(self):
        """Verifica que cada consulta nueva genere un registro histórico independiente sin sobrescribir."""
        material = Material(
            nombre="Ladrillo Test",
            unidad_medida="unidad",
            precio_material=Decimal("1200.00"),
            estado=True
        )
        db.session.add(material)
        db.session.commit()

        mat_prov = MaterialProveedor(
            id_material=material.id_material,
            proveedor="easy_colombia",
            sku="LAD-01",
            termino_busqueda="ladrillo",
            nombre_producto="Ladrillo tolete"
        )
        db.session.add(mat_prov)
        db.session.commit()

        h1 = HistorialPrecioMaterial(
            id_material_proveedor=mat_prov.id_material_proveedor,
            precio=Decimal("1300.00"),
            fecha_consulta=datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
        )
        h2 = HistorialPrecioMaterial(
            id_material_proveedor=mat_prov.id_material_proveedor,
            precio=Decimal("1350.00"),
            fecha_consulta=datetime(2026, 10, 2, 10, 0, tzinfo=timezone.utc)
        )
        db.session.add_all([h1, h2])
        db.session.commit()

        registros = HistorialPrecioMaterial.query.filter_by(
            id_material_proveedor=mat_prov.id_material_proveedor
        ).order_by(HistorialPrecioMaterial.fecha_consulta.asc()).all()

        self.assertEqual(len(registros), 2)
        self.assertEqual(registros[0].precio, Decimal("1300.00"))
        self.assertEqual(registros[1].precio, Decimal("1350.00"))

    def test_restricciones_numericas_check_constraints_individuales(self):
        """Verifica individualmente que la base de datos rechace con IntegrityError valores cero o negativos en campos restringidos."""
        material = Material(
            nombre="Bloque Test Num",
            unidad_medida="unidad",
            precio_material=Decimal("1500.00"),
            estado=True
        )
        db.session.add(material)
        db.session.commit()

        # 1. MaterialProveedor: multiplicador_proveedor = 0
        mp1 = MaterialProveedor(id_material=material.id_material, proveedor="easy_colombia", sku="M-0", termino_busqueda="b", nombre_producto="B", multiplicador_proveedor=Decimal("0.0000"))
        db.session.add(mp1)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # 2. MaterialProveedor: multiplicador_proveedor negativo
        mp2 = MaterialProveedor(id_material=material.id_material, proveedor="easy_colombia", sku="M-NEG", termino_busqueda="b", nombre_producto="B", multiplicador_proveedor=Decimal("-1.0000"))
        db.session.add(mp2)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # 3. MaterialProveedor: factor_conversion = 0
        mp3 = MaterialProveedor(id_material=material.id_material, proveedor="easy_colombia", sku="F-0", termino_busqueda="b", nombre_producto="B", factor_conversion=Decimal("0.0000"))
        db.session.add(mp3)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # 4. MaterialProveedor: factor_conversion negativo
        mp4 = MaterialProveedor(id_material=material.id_material, proveedor="easy_colombia", sku="F-NEG", termino_busqueda="b", nombre_producto="B", factor_conversion=Decimal("-0.5000"))
        db.session.add(mp4)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Crear un MaterialProveedor válido base para probar HistorialPrecioMaterial
        mp_base = MaterialProveedor(id_material=material.id_material, proveedor="easy_colombia", sku="BASE-HIST", termino_busqueda="b", nombre_producto="B")
        db.session.add(mp_base)
        db.session.commit()

        # 5. HistorialPrecioMaterial: precio = 0
        h1 = HistorialPrecioMaterial(id_material_proveedor=mp_base.id_material_proveedor, precio=Decimal("0.00"), fecha_consulta=datetime.now(timezone.utc))
        db.session.add(h1)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # 6. HistorialPrecioMaterial: precio negativo
        h2 = HistorialPrecioMaterial(id_material_proveedor=mp_base.id_material_proveedor, precio=Decimal("-10.00"), fecha_consulta=datetime.now(timezone.utc))
        db.session.add(h2)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # 7. HistorialPrecioMaterial: precio_lista = 0
        h3 = HistorialPrecioMaterial(id_material_proveedor=mp_base.id_material_proveedor, precio=Decimal("100.00"), precio_lista=Decimal("0.00"), fecha_consulta=datetime.now(timezone.utc))
        db.session.add(h3)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # 8. HistorialPrecioMaterial: precio_lista negativo
        h4 = HistorialPrecioMaterial(id_material_proveedor=mp_base.id_material_proveedor, precio=Decimal("100.00"), precio_lista=Decimal("-5.00"), fecha_consulta=datetime.now(timezone.utc))
        db.session.add(h4)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # 9. HistorialPrecioMaterial: disponibilidad negativa
        h5 = HistorialPrecioMaterial(id_material_proveedor=mp_base.id_material_proveedor, precio=Decimal("100.00"), disponibilidad=-1, fecha_consulta=datetime.now(timezone.utc))
        db.session.add(h5)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # 10. HistorialPrecioMaterial: precio_por_unidad_material = 0
        h6 = HistorialPrecioMaterial(id_material_proveedor=mp_base.id_material_proveedor, precio=Decimal("100.00"), precio_por_unidad_material=Decimal("0.00"), fecha_consulta=datetime.now(timezone.utc))
        db.session.add(h6)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # 11. HistorialPrecioMaterial: precio_por_unidad_material negativo
        h7 = HistorialPrecioMaterial(id_material_proveedor=mp_base.id_material_proveedor, precio=Decimal("100.00"), precio_por_unidad_material=Decimal("-2.50"), fecha_consulta=datetime.now(timezone.utc))
        db.session.add(h7)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

    def test_integridad_referencial_claves_foraneas(self):
        """Verifica que las claves foráneas rechacen referencias a registros inexistentes con IntegrityError."""
        # MaterialProveedor con id_material inexistente (99999)
        mp_bad_fk = MaterialProveedor(
            id_material=99999,
            proveedor="easy_colombia",
            sku="BAD-FK",
            termino_busqueda="test",
            nombre_producto="Test"
        )
        db.session.add(mp_bad_fk)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # HistorialPrecioMaterial con id_material_proveedor inexistente (99999)
        hist_bad_fk = HistorialPrecioMaterial(
            id_material_proveedor=99999,
            precio=Decimal("500.00"),
            fecha_consulta=datetime.now(timezone.utc)
        )
        db.session.add(hist_bad_fk)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()


if __name__ == "__main__":
    unittest.main()