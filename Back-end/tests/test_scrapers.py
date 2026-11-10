import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
import urllib.error
import urllib.parse
import json

from app.scrapers.base_scraper import (
    ScraperValidationError,
    ScraperConnectionError,
    ScraperHTTPError,
    ScraperInvalidResponseError
)
from app.scrapers.easy_scraper import EasyScraper
from app.scrapers.scraper_manager import ScraperManager


class DummyScraper(EasyScraper):
    """Scraper ficticio para probar el registro y selección en ScraperManager."""
    def __init__(self):
        super().__init__()
        self.proveedor_nombre = "dummy_provider"

    def search(self, query: str, from_index: int = 0, to_index: int = 10) -> list:
        self._validate_params(query, from_index, to_index)
        return [{"proveedor": self.proveedor_nombre, "nombre": query}]


class TestScrapers(unittest.TestCase):

    def setUp(self):
        self.scraper = EasyScraper()
        self.manager = ScraperManager()

    def test_timeout_validation(self):
        """Valida rechazo de timeouts booleanos, NaN, infinitos, no positivos y aceptación de Decimal válido."""
        with self.assertRaises(ScraperValidationError):
            EasyScraper(timeout=True)
        with self.assertRaises(ScraperValidationError):
            EasyScraper(timeout=float('nan'))
        with self.assertRaises(ScraperValidationError):
            EasyScraper(timeout=float('inf'))
        with self.assertRaises(ScraperValidationError):
            EasyScraper(timeout=-5)
        with self.assertRaises(ScraperValidationError):
            EasyScraper(timeout=0)
        
        # Comprobar comportamiento con un Decimal válido
        scraper_dec = EasyScraper(timeout=Decimal("15"))
        self.assertEqual(scraper_dec.timeout, 15.0)

    def test_pagination_limits_inclusive(self):
        """Verifica paginación inclusiva (máx 50 elementos)."""
        self.scraper._validate_params("cemento", 0, 49)  # 50 elementos -> OK
        with self.assertRaises(ScraperValidationError):
            self.scraper._validate_params("cemento", 0, 50)  # 51 elementos -> Error

    def test_validation_params_and_boolean_indices(self):
        """Verifica rechazo de booleanos y parámetros inválidos en índices."""
        with self.assertRaises(ScraperValidationError):
            self.scraper.search("")
        with self.assertRaises(ScraperValidationError):
            self.scraper.search("cemento", from_index=True)
        with self.assertRaises(ScraperValidationError):
            self.scraper.search("cemento", from_index=0, to_index=False)
        with self.assertRaises(ScraperValidationError):
            self.scraper.search("cemento", from_index=-1)
        with self.assertRaises(ScraperValidationError):
            self.scraper.search("cemento", from_index=5, to_index=2)

    def test_query_encoding_safe_empty(self):
        """Verifica codificación de consultas con safe=''."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response_obj = MagicMock()
            mock_response_obj.read.return_value = json.dumps([]).encode("utf-8")
            mock_response_obj.headers.get_content_charset.return_value = "utf-8"
            mock_response_obj.__enter__.return_value = mock_response_obj
            mock_urlopen.return_value = mock_response_obj

            self.scraper.search("cemento / gris & especial", 0, 0)
            args, _ = mock_urlopen.call_args
            req_obj = args[0]
            expected_encoded = urllib.parse.quote("cemento / gris & especial", safe="")
            self.assertIn(expected_encoded, req_obj.full_url)

    @patch("urllib.request.urlopen")
    def test_product_reference_priority_and_malformed_reference_id(self, mock_urlopen):
        """Comprueba prioridad de productReference y protección ante referenceId malformado."""
        sample_response = [
            {
                "productName": "Producto Test Ref",
                "brand": "MARCA",
                "productId": "111",
                "productReference": None,
                "link": "/producto/test/p",
                "items": [
                    {
                        "itemId": "SKU111",
                        "referenceId": ["no-es-diccionario"],
                        "sellers": [
                            {
                                "sellerName": "V1",
                                "commertialOffer": {"Price": 1000.00}
                            }
                        ]
                    }
                ]
            }
        ]

        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = json.dumps(sample_response).encode("utf-8")
        mock_response_obj.headers.get_content_charset.return_value = "utf-8"
        mock_response_obj.__enter__.return_value = mock_response_obj
        mock_urlopen.return_value = mock_response_obj

        results = self.scraper.search("test", 0, 0)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["referencia"], "SKU111")
        self.assertEqual(results[0]["enlace"], "https://www.easy.com.co/producto/test/p")

    @patch("urllib.request.urlopen")
    def test_seller_default_normalization_and_absent_id(self, mock_urlopen):
        """Pruebas exhaustivas de sellerDefault y sellerId ausente."""
        sample_response = [
            {
                "productName": "Producto Seller Default Test",
                "brand": "B",
                "productId": "333",
                "items": [
                    {
                        "itemId": "SKU333",
                        "sellers": [
                            {
                                "sellerId": None,
                                "sellerName": "V1",
                                "sellerDefault": True,
                                "commertialOffer": {"Price": 500.00}
                            },
                            {
                                "sellerName": "V2",
                                "sellerDefault": "false",
                                "commertialOffer": {"Price": 600.00}
                            },
                            {
                                "sellerName": "V3",
                                "sellerDefault": "desconocido",
                                "commertialOffer": {"Price": 700.00}
                            },
                            {
                                "sellerName": "V4",
                                "sellerDefault": 12345,
                                "commertialOffer": {"Price": 800.00}
                            },
                            {
                                "sellerName": "V5",
                                "commertialOffer": {"Price": 900.00}
                            }
                        ]
                    }
                ]
            }
        ]

        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = json.dumps(sample_response).encode("utf-8")
        mock_response_obj.headers.get_content_charset.return_value = "utf-8"
        mock_response_obj.__enter__.return_value = mock_response_obj
        mock_urlopen.return_value = mock_response_obj

        results = self.scraper.search("test", 0, 4)
        self.assertEqual(len(results), 5)

        self.assertIsNone(results[0]["seller_id"])
        self.assertTrue(results[0]["seller_default"])
        self.assertFalse(results[1]["seller_default"])
        self.assertIsNone(results[2]["seller_default"])
        self.assertIsNone(results[3]["seller_default"])
        self.assertIsNone(results[4]["seller_default"])

    @patch("urllib.request.urlopen")
    def test_availability_and_unit_multiplier_edge_cases(self, mock_urlopen):
        """Comprueba disponibilidad fraccionaria/booleana y unidades/multiplicadores ausentes."""
        sample_response = [
            {
                "productName": "Producto Edge Cases",
                "brand": "X",
                "productId": "444",
                "items": [
                    {
                        "itemId": "SKU444",
                        "measurementUnit": None,
                        "unitMultiplier": "abc",
                        "sellers": [
                            {
                                "sellerName": "V1",
                                "commertialOffer": {"Price": 1500.00, "AvailableQuantity": True}
                            },
                            {
                                "sellerName": "V2",
                                "commertialOffer": {"Price": 1600.00, "AvailableQuantity": 10.5}
                            },
                            {
                                "sellerName": "V3",
                                "commertialOffer": {"Price": 1700.00, "AvailableQuantity": 50}
                            }
                        ]
                    }
                ]
            }
        ]

        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = json.dumps(sample_response).encode("utf-8")
        mock_response_obj.headers.get_content_charset.return_value = "utf-8"
        mock_response_obj.__enter__.return_value = mock_response_obj
        mock_urlopen.return_value = mock_response_obj

        results = self.scraper.search("test", 0, 2)
        self.assertEqual(len(results), 3)

        for res in results:
            self.assertIsNone(res["unidad"])
            self.assertIsNone(res["multiplicador"])

        self.assertIsNone(results[0]["disponibilidad"])
        self.assertIsNone(results[1]["disponibilidad"])
        self.assertEqual(results[2]["disponibilidad"], 50)

    @patch("urllib.request.urlopen")
    def test_rounding_round_half_up(self, mock_urlopen):
        """Verifica redondeo ROUND_HALF_UP con 1.005."""
        sample_response = [
            {
                "productName": "Redondeo",
                "brand": "R",
                "productId": "555",
                "items": [
                    {
                        "itemId": "SKU555",
                        "sellers": [
                            {
                                "sellerName": "V",
                                "commertialOffer": {"Price": 1.005, "ListPrice": 2.005}
                            }
                        ]
                    }
                ]
            }
        ]

        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = json.dumps(sample_response).encode("utf-8")
        mock_response_obj.headers.get_content_charset.return_value = "utf-8"
        mock_response_obj.__enter__.return_value = mock_response_obj
        mock_urlopen.return_value = mock_response_obj

        results = self.scraper.search("test", 0, 0)
        self.assertEqual(results[0]["precio"], Decimal("1.01"))
        self.assertEqual(results[0]["precio_lista"], Decimal("2.01"))

    @patch("urllib.request.urlopen")
    def test_errors_handling(self, mock_urlopen):
        """Verifica errores de lectura, JSON inválido y HTTP/conexión."""
        mock_response_obj = MagicMock()
        mock_response_obj.read.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "error")
        mock_response_obj.headers.get_content_charset.return_value = "utf-8"
        mock_response_obj.__enter__.return_value = mock_response_obj
        mock_urlopen.return_value = mock_response_obj

        with self.assertRaises(ScraperConnectionError):
            self.scraper.search("cemento")

        mock_response_obj.read.side_effect = None
        mock_response_obj.read.return_value = b"JSON corrupto"
        with self.assertRaises(ScraperInvalidResponseError):
            self.scraper.search("cemento")

        mock_urlopen.side_effect = urllib.error.HTTPError(url="http://test", code=500, msg="Error", hdrs=None, fp=None)
        with self.assertRaises(ScraperHTTPError):
            self.scraper.search("cemento")

        mock_urlopen.side_effect = urllib.error.URLError(reason="Refused")
        with self.assertRaises(ScraperConnectionError):
            self.scraper.search("cemento")

    def test_scraper_manager_operations(self):
        """Verifica registro automático y protección de sobrescritura."""
        self.assertIn("easy_colombia", self.manager.list_providers())
        dummy = DummyScraper()
        self.manager.register("dummy", dummy)
        self.assertIn("dummy", self.manager.list_providers())

        with self.assertRaises(ValueError):
            self.manager.register("easy_colombia", dummy, overwrite=False)


if __name__ == "__main__":
    unittest.main()