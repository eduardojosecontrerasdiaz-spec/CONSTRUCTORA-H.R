
import urllib.request
import urllib.parse
import urllib.error
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.scrapers.base_scraper import (
    BaseScraper,
    ScraperConnectionError,
    ScraperHTTPError,
    ScraperInvalidResponseError
)


class EasyScraper(BaseScraper):
    """Conector específico para Easy Colombia utilizando la API pública de catálogo."""

    BASE_URL = "https://www.easy.com.co/api/catalog_system/pub/products/search"

    def __init__(self, timeout: int = 10):
        super().__init__(proveedor_nombre="easy_colombia", timeout=timeout)

    def _convertir_decimal_finito(self, valor):
        """Convierte un valor a Decimal con ROUND_HALF_UP y verifica que sea finito y positivo."""
        if valor is None or isinstance(valor, bool):
            return None
        try:
            dec = Decimal(str(valor)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if not dec.is_finite() or dec <= Decimal("0.00"):
                return None
            return dec
        except (InvalidOperation, ValueError, TypeError):
            return None

    def search(self, query: str, from_index: int = 0, to_index: int = 10) -> list:
        """Busca productos en Easy Colombia y normaliza los resultados."""
        self._validate_params(query, from_index, to_index)

        encoded_query = urllib.parse.quote(query.strip(), safe="")
        url = f"{self.BASE_URL}/{encoded_query}?_from={from_index}&_to={to_index}"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "application/json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                body = response.read().decode(charset)
                data = json.loads(body)
        except (json.JSONDecodeError, TypeError) as e:
            raise ScraperInvalidResponseError(
                f"Respuesta JSON inválida recibida de Easy Colombia: {str(e)}"
            )
        except urllib.error.HTTPError as e:
            raise ScraperHTTPError(
                f"Error HTTP {e.code} al consultar Easy Colombia: {e.reason}"
            )
        except urllib.error.URLError as e:
            raise ScraperConnectionError(
                f"Error de conexión al consultar Easy Colombia: {e.reason}"
            )
        except TimeoutError:
            raise ScraperConnectionError(
                "Tiempo de espera agotado (timeout) al conectar con Easy Colombia."
            )
        except (urllib.error.ContentTooShortError, ValueError, UnicodeDecodeError) as e:
            raise ScraperConnectionError(
                f"Error de lectura de respuesta de Easy Colombia: {str(e)}"
            )

        if not isinstance(data, list):
            raise ScraperInvalidResponseError(
                "La estructura de la respuesta de Easy Colombia no es una lista de productos."
            )

        normalized_results = []
        consulta_utc = datetime.now(timezone.utc).isoformat()

        for product in data:
            if not isinstance(product, dict):
                continue

            product_name = product.get("productName")
            brand = product.get("brand", "Desconocida")
            product_id = str(product.get("productId", ""))

            # Priorizar productReference del producto.
            prod_reference = product.get("productReference")

            product_link = product.get("link")
            if product_link and isinstance(product_link, str):
                product_link = product_link.strip()
                if product_link and not product_link.startswith("http"):
                    if product_link.startswith("/"):
                        product_link = f"https://www.easy.com.co{product_link}"
                    else:
                        product_link = f"https://www.easy.com.co/{product_link}"
            else:
                product_link = None

            items = product.get("items", [])
            if not isinstance(items, list):
                items = []

            for item in items:
                if not isinstance(item, dict):
                    continue

                sku = str(item.get("itemId", product_id))

                # Referencia alternativa protegida.
                reference = prod_reference
                if not reference:
                    ref_id_list = item.get("referenceId")
                    if isinstance(ref_id_list, list) and ref_id_list:
                        first_elem = ref_id_list[0]
                        if isinstance(first_elem, dict):
                            val = first_elem.get("Value")
                            if val:
                                reference = str(val)

                if not reference:
                    reference = sku

                # Unidad: None si falta o no es una cadena válida.
                raw_unit = item.get("measurementUnit")
                if isinstance(raw_unit, str) and raw_unit.strip():
                    unit = raw_unit.strip()
                else:
                    unit = None

                # Multiplicador: None si falta o es inválido.
                raw_multiplier = item.get("unitMultiplier")
                multiplier = None
                if raw_multiplier is not None and not isinstance(raw_multiplier, bool):
                    try:
                        dec_mult = Decimal(str(raw_multiplier)).quantize(
                            Decimal("0.0001"), rounding=ROUND_HALF_UP
                        )
                        if dec_mult.is_finite() and dec_mult > Decimal("0.0000"):
                            multiplier = dec_mult
                    except (InvalidOperation, ValueError, TypeError):
                        multiplier = None

                sellers = item.get("sellers", [])
                if not isinstance(sellers, list):
                    sellers = []

                for seller in sellers:
                    if not isinstance(seller, dict):
                        continue

                    seller_name = seller.get("sellerName", "Desconocido")

                    raw_seller_id = seller.get("sellerId")
                    seller_id = (
                        str(raw_seller_id)
                        if raw_seller_id is not None
                        and str(raw_seller_id).strip() != ""
                        else None
                    )

                    # Normalización estricta de sellerDefault.
                    raw_default = seller.get("sellerDefault")
                    seller_default = None

                    if isinstance(raw_default, bool):
                        seller_default = raw_default
                    elif isinstance(raw_default, str):
                        lower_val = raw_default.strip().lower()
                        if lower_val in ("true", "1", "yes", "si"):
                            seller_default = True
                        elif lower_val in ("false", "0", "no"):
                            seller_default = False

                    offer = (
                        seller.get("commertialOffer")
                        or seller.get("commercialOffer")
                    )
                    if not isinstance(offer, dict):
                        continue

                    raw_price = offer.get("Price")
                    raw_list_price = offer.get("ListPrice")

                    # Disponibilidad: enteros no negativos, sin truncar flotantes.
                    raw_avail = offer.get("AvailableQuantity")
                    available_quantity = None

                    if raw_avail is not None and not isinstance(raw_avail, bool):
                        if isinstance(raw_avail, int):
                            if raw_avail >= 0:
                                available_quantity = raw_avail
                        elif isinstance(raw_avail, str):
                            if raw_avail.isdigit():
                                available_quantity = int(raw_avail)

                    price = self._convertir_decimal_finito(raw_price)
                    if price is None:
                        continue

                    list_price = self._convertir_decimal_finito(raw_list_price)

                    normalized_results.append({
                        "proveedor": self.proveedor_nombre,
                        "nombre": product_name,
                        "marca": brand,
                        "referencia": reference,
                        "sku": sku,
                        "unidad": unit,
                        "multiplicador": multiplier,
                        "vendedor": seller_name,
                        "seller_id": seller_id,
                        "seller_default": seller_default,
                        "precio": price,
                        "precio_lista": list_price,
                        "disponibilidad": available_quantity,
                        "enlace": product_link,
                        "fecha_consulta": consulta_utc
                    })

        return normalized_results
