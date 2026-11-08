import unittest
from decimal import Decimal
from unittest.mock import MagicMock, call, patch

from app.services.presupuesto_service import (
    crear_version_presupuesto,
    listar_versiones_por_presupuesto,
)


class TestVersionesPresupuesto(unittest.TestCase):

    def configurar_mocks_creacion(
        self,
        mock_session,
        mock_presupuesto_model,
        mock_version_model,
        mock_detalle_model,
        mock_detalle_version_model,
        ultima_version=None,
        versiones_activas=None,
        detalles_actuales=None,
    ):
        """Prepara los mocks necesarios para crear una versión."""

        presupuesto = MagicMock()
        presupuesto.monto_total = Decimal("70000.00")

        # Consulta del presupuesto con bloqueo FOR UPDATE.
        (
            mock_session.query.return_value
            .filter_by.return_value
            .populate_existing.return_value
            .with_for_update.return_value
            .first.return_value
        ) = presupuesto

        # Consultas del historial de versiones.
        query_versiones = MagicMock()
        mock_version_model.query = query_versiones

        query_ultima = MagicMock()
        query_activas = MagicMock()

        query_versiones.filter_by.side_effect = [
            query_ultima,
            query_activas,
        ]

        query_ultima.order_by.return_value.first.return_value = (
            ultima_version
        )

        query_activas.all.return_value = (
            versiones_activas or []
        )

        # Consulta de los detalles actuales.
        mock_detalle_model.query.filter_by.return_value.all.return_value = (
            detalles_actuales or []
        )

        # Preparar objetos nuevos.
        nueva_version = MagicMock()
        nueva_version.id_version = 50

        mock_version_model.return_value = nueva_version

        detalle_version = MagicMock()
        mock_detalle_version_model.return_value = detalle_version

        return nueva_version, detalle_version

    @patch("app.services.presupuesto_service.db.session")
    @patch("app.services.presupuesto_service.Presupuesto")
    @patch("app.services.presupuesto_service.VersionPresupuesto")
    @patch("app.services.presupuesto_service.DetallePresupuesto")
    @patch("app.services.presupuesto_service.DetalleVersionPresupuesto")
    def test_crear_version_exito(
        self,
        mock_detalle_version_model,
        mock_detalle_model,
        mock_version_model,
        mock_presupuesto_model,
        mock_session,
    ):
        """Comprueba la creación de una primera versión y sus detalles."""

        detalle = MagicMock()
        detalle.id_material = 1
        detalle.cantidad = Decimal("2.00")
        detalle.precio_unitario = Decimal("35000.00")
        detalle.subtotal = Decimal("70000.00")

        nueva_version, detalle_version = self.configurar_mocks_creacion(
            mock_session,
            mock_presupuesto_model,
            mock_version_model,
            mock_detalle_model,
            mock_detalle_version_model,
            detalles_actuales=[detalle],
        )

        resultado = crear_version_presupuesto(
            1, "Primera versión"
        )

        mock_version_model.assert_called_once_with(
            id_presupuesto=1,
            numero_version=1,
            monto_total=Decimal("70000.00"),
            motivo="Primera versión",
            estado="activa",
        )

        mock_detalle_version_model.assert_called_once_with(
            id_version=50,
            id_material=1,
            cantidad=Decimal("2.00"),
            precio_unitario=Decimal("35000.00"),
            subtotal=Decimal("70000.00"),
        )

        self.assertEqual(resultado, nueva_version)

        mock_session.add.assert_has_calls([
            call(nueva_version),
            call(detalle_version),
        ])

        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

    @patch("app.services.presupuesto_service.db.session")
    @patch("app.services.presupuesto_service.Presupuesto")
    @patch("app.services.presupuesto_service.VersionPresupuesto")
    @patch("app.services.presupuesto_service.DetallePresupuesto")
    @patch("app.services.presupuesto_service.DetalleVersionPresupuesto")
    def test_crear_version_consecutiva(
        self,
        mock_detalle_version_model,
        mock_detalle_model,
        mock_version_model,
        mock_presupuesto_model,
        mock_session,
    ):
        """Comprueba que la siguiente versión tenga número consecutivo."""

        version_anterior = MagicMock()
        version_anterior.numero_version = 1
        version_anterior.estado = "activa"

        nueva_version, detalle_version = self.configurar_mocks_creacion(
            mock_session,
            mock_presupuesto_model,
            mock_version_model,
            mock_detalle_model,
            mock_detalle_version_model,
            ultima_version=version_anterior,
            versiones_activas=[version_anterior],
        )

        nueva_version.numero_version = 2

        crear_version_presupuesto(1, "Segunda versión")

        self.assertEqual(
            version_anterior.estado,
            "historica",
        )

        mock_version_model.assert_called_once_with(
            id_presupuesto=1,
            numero_version=2,
            monto_total=Decimal("70000.00"),
            motivo="Segunda versión",
            estado="activa",
        )

        mock_session.commit.assert_called_once()

    @patch("app.services.presupuesto_service.db.session")
    def test_crear_version_presupuesto_no_encontrado(
        self, mock_session
    ):
        """Comprueba el error cuando no existe el presupuesto."""

        (
            mock_session.query.return_value
            .filter_by.return_value
            .populate_existing.return_value
            .with_for_update.return_value
            .first.return_value
        ) = None

        with self.assertRaises(ValueError) as ctx:
            crear_version_presupuesto(99999, "Prueba")

        self.assertIn(
            "El presupuesto indicado no existe",
            str(ctx.exception),
        )

        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    @patch("app.services.presupuesto_service.db.session")
    @patch("app.services.presupuesto_service.Presupuesto")
    @patch("app.services.presupuesto_service.VersionPresupuesto")
    @patch("app.services.presupuesto_service.DetallePresupuesto")
    @patch("app.services.presupuesto_service.DetalleVersionPresupuesto")
    def test_crear_version_rollback(
        self,
        mock_detalle_version_model,
        mock_detalle_model,
        mock_version_model,
        mock_presupuesto_model,
        mock_session,
    ):
        """Comprueba el rollback cuando falla el commit."""

        self.configurar_mocks_creacion(
            mock_session,
            mock_presupuesto_model,
            mock_version_model,
            mock_detalle_model,
            mock_detalle_version_model,
        )

        mock_session.commit.side_effect = Exception(
            "Error simulado de base de datos"
        )

        with self.assertRaises(RuntimeError) as ctx:
            crear_version_presupuesto(1, "Prueba rollback")

        self.assertIn(
            "Error inesperado al crear la versión",
            str(ctx.exception),
        )

        mock_session.rollback.assert_called_once()

    @patch("app.services.presupuesto_service.db.session")
    def test_crear_version_motivo_supera_limite(
        self, mock_session
    ):
        """Comprueba que el motivo no supere los 500 caracteres."""

        motivo = "A" * 501

        with self.assertRaises(ValueError) as ctx:
            crear_version_presupuesto(1, motivo)

        self.assertIn(
            "El motivo no puede superar los 500 caracteres",
            str(ctx.exception),
        )

        mock_session.query.assert_not_called()

    @patch("app.services.presupuesto_service.db.session")
    @patch("app.services.presupuesto_service.Presupuesto")
    @patch("app.services.presupuesto_service.VersionPresupuesto")
    def test_listar_versiones_exito(
        self,
        mock_version_model,
        mock_presupuesto_model,
        mock_session,
    ):
        """Comprueba que se listen las versiones del presupuesto."""

        mock_session.get.return_value = MagicMock()

        versiones = [
            MagicMock(numero_version=1, estado="historica"),
            MagicMock(numero_version=2, estado="activa"),
        ]

        (
            mock_version_model.query
            .filter_by.return_value
            .order_by.return_value
            .all.return_value
        ) = versiones

        resultado = listar_versiones_por_presupuesto(1)

        self.assertEqual(resultado, versiones)

        mock_session.get.assert_called_once_with(
            mock_presupuesto_model, 1
        )

        mock_version_model.query.filter_by.assert_called_once_with(
            id_presupuesto=1
        )

    @patch("app.services.presupuesto_service.db.session")
    def test_listar_versiones_presupuesto_no_encontrado(
        self, mock_session
    ):
        """Comprueba el error al listar un presupuesto inexistente."""

        mock_session.get.return_value = None

        with self.assertRaises(ValueError) as ctx:
            listar_versiones_por_presupuesto(99999)

        self.assertIn(
            "El presupuesto indicado no existe",
            str(ctx.exception),
        )

        mock_session.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()