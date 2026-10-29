import unittest
from unittest.mock import patch, MagicMock

from flask import Flask

from app.routes.presupuesto_routes import presupuesto_bp


class TestPresupuestoController(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(
            presupuesto_bp,
            url_prefix="/api"
        )
        self.client = self.app.test_client()

    @patch("app.controllers.presupuesto_controller.presupuesto_schema")
    @patch("app.controllers.presupuesto_controller.crear_presupuesto")
    def test_crear_presupuesto_exito(
        self, mock_crear, mock_schema
    ):
        mock_crear.return_value = MagicMock()

        mock_schema.dump.return_value = {
            "id_presupuesto": 1,
            "id_proyecto": 5,
            "categoria": "Obras Civiles",
            "estado": "borrador",
        }

        response = self.client.post(
            "/api/proyectos/5/presupuestos",
            json={"categoria": "Obras Civiles"}
        )

        self.assertEqual(response.status_code, 201)

        mock_crear.assert_called_once_with({
            "categoria": "Obras Civiles",
            "id_proyecto": 5,
        })

        self.assertEqual(
            response.get_json()["id_presupuesto"],
            1
        )

    @patch("app.controllers.presupuesto_controller.crear_presupuesto")
    def test_crear_presupuesto_proyecto_no_encontrado(
        self, mock_crear
    ):
        mock_crear.side_effect = ValueError(
            "El proyecto indicado no existe."
        )

        response = self.client.post(
            "/api/proyectos/999/presupuestos",
            json={"categoria": "Obras Civiles"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn(
            "no existe",
            response.get_json()["error"]
        )

    @patch("app.controllers.presupuesto_controller.crear_presupuesto")
    def test_crear_presupuesto_error_interno(self, mock_crear):
        mock_crear.side_effect = RuntimeError(
            "Error interno de base de datos."
        )

        response = self.client.post(
            "/api/proyectos/1/presupuestos",
            json={"categoria": "Obras Civiles"}
        )

        self.assertEqual(response.status_code, 500)
        self.assertNotIn(
            "base de datos",
            response.get_json()["error"].lower()
        )

    def test_crear_presupuesto_json_invalido(self):
        response = self.client.post(
            "/api/proyectos/1/presupuestos",
            data="esto no es JSON",
            content_type="text/plain"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "JSON válido",
            response.get_json()["error"]
        )

    @patch("app.controllers.presupuesto_controller.presupuesto_schema")
    @patch("app.controllers.presupuesto_controller.obtener_presupuesto_por_id")
    def test_obtener_presupuesto_exito(
        self, mock_obtener, mock_schema
    ):
        mock_obtener.return_value = MagicMock()

        mock_schema.dump.return_value = {
            "id_presupuesto": 1
        }

        response = self.client.get(
            "/api/presupuestos/1"
        )

        self.assertEqual(response.status_code, 200)
        mock_obtener.assert_called_once_with(1)

        self.assertEqual(
            response.get_json()["id_presupuesto"],
            1
        )

    @patch("app.controllers.presupuesto_controller.obtener_presupuesto_por_id")
    def test_obtener_presupuesto_no_encontrado(
        self, mock_obtener
    ):
        mock_obtener.return_value = None

        response = self.client.get(
            "/api/presupuestos/999"
        )

        self.assertEqual(response.status_code, 404)

    @patch("app.controllers.presupuesto_controller.presupuestos_schema")
    @patch("app.controllers.presupuesto_controller.listar_presupuestos_por_proyecto")
    def test_listar_presupuestos_exito(
        self, mock_listar, mock_schema
    ):
        mock_listar.return_value = [MagicMock()]

        mock_schema.dump.return_value = [
            {"id_presupuesto": 1}
        ]

        response = self.client.get(
            "/api/proyectos/10/presupuestos"
        )

        self.assertEqual(response.status_code, 200)
        mock_listar.assert_called_once_with(10)

        self.assertIsInstance(
            response.get_json(),
            list
        )

    @patch("app.controllers.presupuesto_controller.detalle_schema")
    @patch("app.controllers.presupuesto_controller.agregar_detalle_presupuesto")
    def test_agregar_detalle_exito(
        self, mock_agregar, mock_schema
    ):
        mock_agregar.return_value = MagicMock()

        mock_schema.dump.return_value = {
            "id_detalle": 1,
            "id_presupuesto": 1,
            "subtotal": "10.00",
        }

        payload = {
            "id_material": 2,
            "cantidad": "2.00",
        }

        response = self.client.post(
            "/api/presupuestos/1/detalles",
            json=payload
        )

        self.assertEqual(response.status_code, 201)

        mock_agregar.assert_called_once_with(
            1,
            payload
        )

        self.assertEqual(
            response.get_json()["id_detalle"],
            1
        )

    @patch("app.controllers.presupuesto_controller.agregar_detalle_presupuesto")
    def test_agregar_detalle_material_no_encontrado(
        self, mock_agregar
    ):
        mock_agregar.side_effect = ValueError(
            "El material indicado no existe."
        )

        response = self.client.post(
            "/api/presupuestos/1/detalles",
            json={
                "id_material": 999,
                "cantidad": "1.00",
            }
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn(
            "no existe",
            response.get_json()["error"]
        )

    def test_agregar_detalle_json_invalido(self):
        response = self.client.post(
            "/api/presupuestos/1/detalles",
            data="esto no es JSON",
            content_type="text/plain"
        )

        self.assertEqual(response.status_code, 400)

    @patch("app.controllers.presupuesto_controller.listar_presupuestos_por_proyecto")
    def test_listar_presupuestos_proyecto_no_encontrado(
        self, mock_listar
    ):
        mock_listar.side_effect = ValueError(
            "El proyecto indicado no existe."
        )

        response = self.client.get(
            "/api/proyectos/999/presupuestos"
        )

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()