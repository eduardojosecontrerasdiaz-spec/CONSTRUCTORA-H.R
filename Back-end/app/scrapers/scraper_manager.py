from app.scrapers.base_scraper import BaseScraper
from app.scrapers.easy_scraper import EasyScraper


class ScraperManager:
    """Administrador de proveedores para gestionar y ejecutar consultas de precios de forma uniforme."""

    def __init__(self):
        self._scrapers = {}
        self.register("easy_colombia", EasyScraper(), overwrite=False)

    def register(self, name: str, scraper: BaseScraper, overwrite: bool = False):
        """Registra un nuevo conector de proveedor evitando sobrescribir por accidente."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("El nombre del proveedor debe ser una cadena válida.")
        if not isinstance(scraper, BaseScraper):
            raise TypeError("El conector debe ser una instancia de BaseScraper.")

        key = name.strip().lower()
        if not overwrite and key in self._scrapers:
            raise ValueError(f"El proveedor '{key}' ya se encuentra registrado y no se permite sobrescribirlo accidentalmente.")

        self._scrapers[key] = scraper

    def get_scraper(self, name: str) -> BaseScraper:
        """Obtiene un conector registrado por su nombre utilizando el identificador consistente."""
        if not isinstance(name, str):
            raise ValueError("El nombre del proveedor debe ser una cadena.")
        key = name.strip().lower()
        if key not in self._scrapers:
            raise ValueError(f"El proveedor '{name}' no está registrado en el ScraperManager.")
        return self._scrapers[key]

    def search(self, provider_name: str, query: str, from_index: int = 0, to_index: int = 10) -> list:
        """Busca productos utilizando el proveedor seleccionado de forma uniforme."""
        scraper = self.get_scraper(provider_name)
        return scraper.search(query, from_index=from_index, to_index=to_index)

    def list_providers(self) -> list:
        """Devuelve la lista de nombres de proveedores registrados."""
        return list(self._scrapers.keys())