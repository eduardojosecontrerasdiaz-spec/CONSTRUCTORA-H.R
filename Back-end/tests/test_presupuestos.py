import unittest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from app.services.presupuesto_service import (
    crear_presupuesto,
    obtener_presupuesto_por_id,
    listar_presupuestos_por_proyecto,
    agregar_detalle_presupuesto,
)


class TestPresupuestoServiceFinalAuditComplete(unittest.TestCase):

    @patch("app.services.presupuesto_service.db.session")
    @patch("app.services.presupuesto_service.Proyecto")
    def test_crear_presupuesto_exito(self, mock_proyecto, mock_db_session):
        mock_db_session.get.return_value = MagicMock()
        data = {"id_proyecto": 1, "categoria": "Obras Civiles"}

        with patch(
            "app.services.presupuesto_service.Presupuesto"
        ) as mock_presupuesto_class:
            mock_instance = MagicMock()
            mock_presupuesto_class.return_value = mock_instance

            resultado = crear_presupuesto(data)

            mock_db_session.add.assert_called_once_with(mock_instance)
            mock_db_session.commit.assert_called_once()
            self.assertEqual(resultado, mock_instance)

    @patch("app.services.presupuesto_service.db.session")
    def test_crear_presupuesto_error_consulta_db_rollback(self, mock_db_session):
        mock_db_session.get.side_effect = Exception("DB Connection Error")

        with self.assertRaises(RuntimeError) as ctx:
            crear_presupuesto(
                {"id_proyecto": 1, "categoria": "Estructuras"}
            )

        self.assertIn("Error al consultar el proyecto", str(ctx.exception))
        mock_db_session.rollback.assert_called()

    @patch("app.services.presupuesto_service.db.session")
    @patch("app.services.presupuesto_service.Proyecto")
    def test_crear_presupuesto_categoria_vacia(
        self, mock_proyecto, mock_db_session
    ):
        mock_db_session.get.return_value = MagicMock()

        with self.assertRaises(ValueError) as ctx:
            crear_presupuesto(
                {"id_proyecto": 1, "categoria": "   "}
            )

        self.assertIn("categoría es obligatoria", str(ctx.exception))

    @patch("app.services.presupuesto_service.db.session")
    def test_obtener_presupuesto_por_id_exito(self, mock_db_session):
        mock_presupuesto = MagicMock()
        mock_db_session.get.return_value = mock_presupuesto

        resultado = obtener_presupuesto_por_id(1)

        self.assertEqual(resultado, mock_presupuesto)

    @patch("app.services.presupuesto_service.db.session")
    def test_obtener_presupuesto_por_id_error_db(self, mock_db_session):
        mock_db_session.get.side_effect = Exception("Fail")

        with self.assertRaises(RuntimeError):
            obtener_presupuesto_por_id(1)

        mock_db_session.rollback.assert_called()

    @patch("app.services.presupuesto_service.Presupuesto")
    def test_listar_presupuestos_por_proyecto(self, mock_model):
        mock_query = MagicMock()
        mock_model.query = mock_query
        mock_query.filter_by.return_value.all.return_value = [1, 2, 3]

        resultado = listar_presupuestos_por_proyecto(10)

        self.assertEqual(resultado, [1, 2, 3])
        mock_query.filter_by.assert_called_once_with(id_proyecto=10)

    def test_agregar_detalle_cantidad_invalida_nan_inf(self):
        with self.assertRaises(ValueError):
            agregar_detalle_presupuesto(
                1, {"id_material": 1, "cantidad": "NaN"}
            )

        with self.assertRaises(ValueError):
            agregar_detalle_presupuesto(
                1, {"id_material": 1, "cantidad": "Infinity"}
            )

    def test_agregar_detalle_limite_numeric_cantidad(self):
        with self.assertRaises(ValueError) as ctx:
            agregar_detalle_presupuesto(
                1,
                {"id_material": 1, "cantidad": "10000000000.00"},
            )

        self.assertIn("excede el límite máximo", str(ctx.exception))

    @patch("app.services.presupuesto_service.db.session")
    @patch("app.services.presupuesto_service.Presupuesto")
    @patch("app.services.presupuesto_service.Material")
    def test_redondeo_round_half_up_caso_1_005(
        self, mock_material_model, mock_presupuesto_model, mock_db_session
    ):
        mock_presupuesto = MagicMock()
        mock_material = MagicMock()
        mock_material.precio_material = Decimal("0.67")

        def side_effect(model, ident):
            if model is mock_presupuesto_model:
                return mock_presupuesto
            if model is mock_material_model:
                return mock_material
            return None

        mock_db_session.get.side_effect = side_effect

        with patch(
            "app.services.presupuesto_service.DetallePresupuesto"
        ) as mock_detalle_class:
            mock_detalle_class.return_value = MagicMock()

            with patch(
                "app.services.presupuesto_service.DetallePresupuesto.query"
            ) as mock_detalle_query:
                detalle_existente = MagicMock()
                detalle_existente.subtotal = Decimal("5.00")

                detalle_nuevo_db = MagicMock()
                detalle_nuevo_db.subtotal = Decimal("1.01")

                mock_detalle_query.filter_by.return_value.all.return_value = [
                    detalle_existente,
                    detalle_nuevo_db,
                ]

                agregar_detalle_presupuesto(
                    1, {"id_material": 2, "cantidad": "1.50"}
                )

                mock_detalle_class.assert_called_once_with(
                    id_presupuesto=1,
                    id_material=2,
                    cantidad=Decimal("1.50"),
                    precio_unitario=Decimal("0.67"),
                    subtotal=Decimal("1.01"),
                )

                self.assertEqual(
                    mock_presupuesto.monto_total, Decimal("6.01")
                )

    @patch("app.services.presupuesto_service.db.session")
    @patch("app.services.presupuesto_service.Presupuesto")
    @patch("app.services.presupuesto_service.Material")
    def test_redondeo_round_half_up_caso_1_015(
        self, mock_material_model, mock_presupuesto_model, mock_db_session
    ):
        mock_presupuesto = MagicMock()
        mock_material = MagicMock()
        mock_material.precio_material = Decimal("0.70")

        def side_effect(model, ident):
            if model is mock_presupuesto_model:
                return mock_presupuesto
            if model is mock_material_model:
                return mock_material
            return None

        mock_db_session.get.side_effect = side_effect

        with patch(
            "app.services.presupuesto_service.DetallePresupuesto"
        ) as mock_detalle_class:
            mock_detalle_class.return_value = MagicMock()

            with patch(
                "app.services.presupuesto_service.DetallePresupuesto.query"
            ) as mock_detalle_query:
                detalle_existente = MagicMock()
                detalle_existente.subtotal = Decimal("10.00")

                detalle_nuevo_db = MagicMock()
                detalle_nuevo_db.subtotal = Decimal("1.02")

                mock_detalle_query.filter_by.return_value.all.return_value = [
                    detalle_existente,
                    detalle_nuevo_db,
                ]

                agregar_detalle_presupuesto(
                    1, {"id_material": 2, "cantidad": "1.45"}
                )

                mock_detalle_class.assert_called_once_with(
                    id_presupuesto=1,
                    id_material=2,
                    cantidad=Decimal("1.45"),
                    precio_unitario=Decimal("0.70"),
                    subtotal=Decimal("1.02"),
                )

                self.assertEqual(
                    mock_presupuesto.monto_total, Decimal("11.02")
                )

    @patch("app.services.presupuesto_service.db.session")
    @patch("app.services.presupuesto_service.Presupuesto")
    @patch("app.services.presupuesto_service.Material")
    def test_agregar_detalle_exceso_limite_subtotal(
        self, mock_material_model, mock_presupuesto_model, mock_db_session
    ):
        mock_presupuesto = MagicMock()
        mock_material = MagicMock()
        mock_material.precio_material = Decimal("9999999999.99")

        def side_effect(model, ident):
            if model is mock_presupuesto_model:
                return mock_presupuesto
            if model is mock_material_model:
                return mock_material
            return None

        mock_db_session.get.side_effect = side_effect

        with self.assertRaises(ValueError) as ctx:
            agregar_detalle_presupuesto(
                1, {"id_material": 2, "cantidad": "101.00"}
            )

        self.assertIn(
            "excede el límite máximo permitido para Numeric(14,2)",
            str(ctx.exception),
        )
        mock_db_session.rollback.assert_called()

    @patch("app.services.presupuesto_service.db.session")
    @patch("app.services.presupuesto_service.Presupuesto")
    @patch("app.services.presupuesto_service.Material")
    def test_agregar_detalle_exceso_limite_monto_total(
        self, mock_material_model, mock_presupuesto_model, mock_db_session
    ):
        mock_presupuesto = MagicMock()
        mock_material = MagicMock()
        mock_material.precio_material = Decimal("1000.00")

        def side_effect(model, ident):
            if model is mock_presupuesto_model:
                return mock_presupuesto
            if model is mock_material_model:
                return mock_material
            return None

        mock_db_session.get.side_effect = side_effect

        detalle_existente = MagicMock()
        detalle_existente.subtotal = Decimal("999999999990.00")

        with patch(
            "app.services.presupuesto_service.DetallePresupuesto"
        ) as mock_detalle_class:
            mock_nuevo_detalle = MagicMock()
            mock_nuevo_detalle.subtotal = Decimal("1000.00")
            mock_detalle_class.return_value = mock_nuevo_detalle

            with patch(
                "app.services.presupuesto_service.DetallePresupuesto.query"
            ) as mock_detalle_query:
                mock_detalle_query.filter_by.return_value.all.return_value = [
                    detalle_existente,
                    mock_nuevo_detalle,
                ]

                with self.assertRaises(ValueError) as ctx:
                    agregar_detalle_presupuesto(
                        1, {"id_material": 2, "cantidad": "1.00"}
                    )

                self.assertIn(
                    "monto total del presupuesto excede el límite máximo",
                    str(ctx.exception),
                )
                mock_db_session.rollback.assert_called()

    @patch("app.services.presupuesto_service.db.session")
    @patch("app.services.presupuesto_service.Presupuesto")
    @patch("app.services.presupuesto_service.Material")
    def test_agregar_detalle_fallo_flush_rollback(
        self, mock_material_model, mock_presupuesto_model, mock_db_session
    ):
        mock_presupuesto = MagicMock()
        mock_material = MagicMock()
        mock_material.precio_material = Decimal("10.00")

        def side_effect(model, ident):
            if model is mock_presupuesto_model:
                return mock_presupuesto
            if model is mock_material_model:
                return mock_material
            return None

        mock_db_session.get.side_effect = side_effect
        mock_db_session.flush.side_effect = Exception("Flush error in DB")

        with patch("app.services.presupuesto_service.DetallePresupuesto"):
            with self.assertRaises(RuntimeError) as ctx:
                agregar_detalle_presupuesto(
                    1, {"id_material": 2, "cantidad": "2.00"}
                )

            self.assertIn(
                "Error inesperado al persistir", str(ctx.exception)
            )
            mock_db_session.rollback.assert_called()

    @patch("app.services.presupuesto_service.db.session")
    @patch("app.services.presupuesto_service.Presupuesto")
    @patch("app.services.presupuesto_service.Material")
    def test_agregar_detalle_fallo_commit_rollback(
        self, mock_material_model, mock_presupuesto_model, mock_db_session
    ):
        mock_presupuesto = MagicMock()
        mock_material = MagicMock()
        mock_material.precio_material = Decimal("10.00")

        def side_effect(model, ident):
            if model is mock_presupuesto_model:
                return mock_presupuesto
            if model is mock_material_model:
                return mock_material
            return None

        mock_db_session.get.side_effect = side_effect
        mock_db_session.commit.side_effect = Exception("Commit error in DB")

        with patch("app.services.presupuesto_service.DetallePresupuesto"):
            with self.assertRaises(RuntimeError) as ctx:
                agregar_detalle_presupuesto(
                    1, {"id_material": 2, "cantidad": "2.00"}
                )

            self.assertIn(
                "Error inesperado al persistir", str(ctx.exception)
            )
            mock_db_session.rollback.assert_called()


if __name__ == "__main__":
    unittest.main()
