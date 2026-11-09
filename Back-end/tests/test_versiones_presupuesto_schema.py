import unittest
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from marshmallow import ValidationError

from app.schemas.presupuesto_schema import (
    VersionPresupuestoSchema,
    DetalleVersionPresupuestoSchema,
)


class TestVersionesPresupuestoSchema(unittest.TestCase):

    def setUp(self):
        self.schema = VersionPresupuestoSchema()

        self.detalle = SimpleNamespace(
            id_detalle_version=1,
            id_version=1,
            id_material=1,
            cantidad=Decimal("2.00"),
            precio_unitario=Decimal("35000.00"),
            subtotal=Decimal("70000.00"),
        )

        self.version = SimpleNamespace(
            id_version=1,
            id_presupuesto=1,
            numero_version=1,
            monto_total=Decimal("70000.00"),
            fecha_creacion=datetime(2026, 11, 8, 12, 0, 0),
            motivo="Primera version",
            estado="activa",
            detalles=[self.detalle],
        )

    def test_serializar_version_completa(self):
        """Comprueba que se serialice la version y sus detalles."""

        resultado = self.schema.dump(self.version)

        self.assertEqual(resultado["id_version"], 1)
        self.assertEqual(resultado["numero_version"], 1)
        self.assertEqual(resultado["estado"], "activa")
        self.assertEqual(resultado["motivo"], "Primera version")

        self.assertEqual(
            resultado["monto_total"],
            "70000.00",
        )

        self.assertEqual(len(resultado["detalles"]), 1)

    def test_serializar_detalles_historicos(self):
        """Comprueba que los detalles se incluyan correctamente."""

        resultado = self.schema.dump(self.version)

        detalle = resultado["detalles"][0]

        self.assertEqual(detalle["id_material"], 1)
        self.assertEqual(detalle["cantidad"], "2.00")
        self.assertEqual(detalle["precio_unitario"], "35000.00")
        self.assertEqual(detalle["subtotal"], "70000.00")

    def test_deserializar_motivo(self):
        """Comprueba que se pueda recibir el motivo."""

        resultado = self.schema.load({
            "motivo": "Actualizacion de precios"
        })

        self.assertEqual(
            resultado["motivo"],
            "Actualizacion de precios",
        )

    def test_deserializar_motivo_nulo(self):
        """Comprueba que el motivo pueda ser nulo."""

        resultado = self.schema.load({
            "motivo": None
        })

        self.assertIsNone(resultado["motivo"])

    def test_rechazar_campos_controlados_por_sistema(self):
        """Comprueba que no se puedan enviar campos dump_only."""

        with self.assertRaises(ValidationError):
            self.schema.load({
                "id_version": 1,
                "id_presupuesto": 1,
                "numero_version": 10,
                "estado": "activa",
                "motivo": "Prueba",
            })

    def test_detalle_version_es_solo_lectura(self):
        """Comprueba que los detalles históricos no admitan escritura."""

        schema = DetalleVersionPresupuestoSchema()

        with self.assertRaises(ValidationError):
            schema.load({
                "id_version": 1,
                "id_material": 1,
                "cantidad": "2.00",
                "precio_unitario": "35000.00",
                "subtotal": "70000.00",
            })


if __name__ == "__main__":
    unittest.main()