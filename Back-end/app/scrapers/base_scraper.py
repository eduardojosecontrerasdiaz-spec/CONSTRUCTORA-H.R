from abc import ABC, abstractmethod
import math
from decimal import Decimal


class ScraperError(Exception):
    """Excepción base para errores de scrapers."""
    pass


class ScraperValidationError(ScraperError):
    """Error en la validación de parámetros de búsqueda o paginación."""
    pass


class ScraperConnectionError(ScraperError):
    """Error de conexión o tiempo de espera con el proveedor."""
    pass


class ScraperHTTPError(ScraperError):
    """Error HTTP devuelto por el servidor del proveedor."""
    pass


class ScraperInvalidResponseError(ScraperError):
    """Respuesta JSON inválida o estructura inesperada del proveedor."""
    pass


class BaseScraper(ABC):
    """Clase base abstracta que establece el contrato común para todos los proveedores."""

    def __init__(self, proveedor_nombre: str, timeout: int = 10):
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float, Decimal)):
            raise ScraperValidationError("El tiempo de espera (timeout) debe ser un número.")
        try:
            f_timeout = float(timeout)
        except (ValueError, TypeError, OverflowError):
            raise ScraperValidationError("El tiempo de espera (timeout) debe ser un número válido.")
        if math.isnan(f_timeout) or math.isinf(f_timeout) or f_timeout <= 0:
            raise ScraperValidationError("El tiempo de espera (timeout) debe ser un número positivo y finito.")

        self.proveedor_nombre = proveedor_nombre
        self.timeout = f_timeout  # Guardar f_timeout validado

    def _validate_params(self, query: str, from_index: int, to_index: int):
        """Valida los parámetros de búsqueda y paginación con restricciones estrictas."""
        if not isinstance(query, str) or not query.strip():
            raise ScraperValidationError("El término de búsqueda debe ser una cadena de texto no vacía.")
        
        if isinstance(from_index, bool) or not isinstance(from_index, int) or from_index < 0:
            raise ScraperValidationError("El índice 'from_index' debe ser un entero mayor o igual a 0.")
        
        if isinstance(to_index, bool) or not isinstance(to_index, int) or to_index < from_index:
            raise ScraperValidationError("El índice 'to_index' debe ser un entero mayor o igual a 'from_index'.")

        num_resultados = (to_index - from_index) + 1
        if num_resultados > 50:
            raise ScraperValidationError("Cada consulta está limitada a un máximo de 50 resultados.")

    @abstractmethod
    def search(self, query: str, from_index: int = 0, to_index: int = 10) -> list:
        """Método abstracto para buscar productos en el proveedor."""
        pass