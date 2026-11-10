from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.config.database import db
from app.models.material import Material
from app.models.material_proveedor import MaterialProveedor
from app.models.historial_precio_material import HistorialPrecioMaterial
from app.scrapers.scraper_manager import ScraperManager

MAX_PRECISION_12_4 = Decimal("99999999.9999")
MAX_PRECISION_14_2 = Decimal("999999999999.99")


def _validar_identificador(valor, nombre):
    """Valida que el identificador sea un entero positivo."""
    if isinstance(valor, bool):
        raise ValueError(f"{nombre} debe ser un entero positivo.")
    try:
        identificador = int(valor)
    except (ValueError, TypeError, OverflowError):
        raise ValueError(f"{nombre} debe ser un entero positivo.")
    if identificador <= 0 or str(valor).strip() != str(identificador):
        raise ValueError(f"{nombre} debe ser un entero positivo.")
    return identificador


def _validar_indices_paginacion(from_index, to_index):
    """Valida los índices de paginación respetando el límite máximo de 50 resultados."""
    if isinstance(from_index, bool) or not isinstance(from_index, int) or from_index < 0:
        raise ValueError("El índice 'from_index' debe ser un entero mayor o igual a 0.")
    if isinstance(to_index, bool) or not isinstance(to_index, int) or to_index < from_index:
        raise ValueError("El índice 'to_index' debe ser un entero mayor o igual a 'from_index'.")
    num_resultados = (to_index - from_index) + 1
    if num_resultados > 50:
        raise ValueError("Cada consulta está limitada a un máximo de 50 resultados.")
    return from_index, to_index


def buscar_productos_proveedor(proveedor, termino_busqueda, from_index=0, to_index=10):
    """Busca productos utilizando ScraperManager para el proveedor especificado sin guardar en BD."""
    if not isinstance(proveedor, str) or not proveedor.strip():
        raise ValueError("El identificador del proveedor debe ser una cadena de texto no vacía.")
    if not isinstance(termino_busqueda, str) or not termino_busqueda.strip():
        raise ValueError("El término de búsqueda debe ser una cadena de texto no vacía.")

    _validar_indices_paginacion(from_index, to_index)

    manager = ScraperManager()
    try:
        resultados = manager.search(proveedor.strip().lower(), termino_busqueda.strip(), from_index=from_index, to_index=to_index)
        return resultados
    except Exception as exc:
        raise RuntimeError(f"Error al buscar productos en el proveedor '{proveedor}': {str(exc)}") from exc


def asociar_producto_material(id_material, producto, termino_busqueda, factor_conversion=None):
    """Asocia un producto externo de proveedor con un material interno existente protegido con manejo de errores."""
    id_mat = _validar_identificador(id_material, "El identificador del material")

    if not isinstance(producto, dict):
        raise ValueError("Los datos del producto deben ser un diccionario.")
    if not isinstance(termino_busqueda, str) or not termino_busqueda.strip():
        raise ValueError("El término de búsqueda es obligatorio.")

    proveedor = producto.get("proveedor")
    sku = producto.get("sku")
    nombre_producto = producto.get("nombre")

    if not proveedor or not str(proveedor).strip():
        raise ValueError("El proveedor del producto es obligatorio.")
    if not sku or not str(sku).strip():
        raise ValueError("El SKU del producto es obligatorio.")
    if not nombre_producto or not str(nombre_producto).strip():
        raise ValueError("El nombre del producto es obligatorio.")

    proveedor_str = str(proveedor).strip().lower()
    sku_str = str(sku).strip()

    try:
        material = db.session.get(Material, id_mat)
        if material is None:
            raise ValueError("El material interno indicado no existe.")

        existente = MaterialProveedor.query.filter_by(proveedor=proveedor_str, sku=sku_str).first()
        if existente is not None:
            raise ValueError("El producto con este proveedor y SKU ya se encuentra asociado.")
    except ValueError:
        db.session.rollback()
        raise
    except Exception as exc:
        db.session.rollback()
        raise RuntimeError("Error al consultar la base de datos durante la asociación.") from exc

    dec_factor = None
    if factor_conversion is not None:
        try:
            dec_factor = Decimal(str(factor_conversion))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("El factor de conversión debe ser un número válido.")
        if not dec_factor.is_finite() or dec_factor <= Decimal("0.0000"):
            raise ValueError("El factor de conversión debe ser un número positivo y finito.")
        dec_factor = dec_factor.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        if not dec_factor.is_finite() or dec_factor <= Decimal("0.0000") or dec_factor > MAX_PRECISION_12_4:
            raise ValueError("El factor de conversión excede el límite permitido para Numeric(12,4).")

    raw_mult = producto.get("multiplicador") if producto.get("multiplicador") is not None else producto.get("multiplicador_proveedor")
    multiplicador = None
    if raw_mult is not None:
        if isinstance(raw_mult, bool):
            raise ValueError("El multiplicador del proveedor no puede ser un booleano.")
        try:
            multiplicador = Decimal(str(raw_mult))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("El multiplicador del proveedor debe ser un número válido.")
        if not multiplicador.is_finite():
            raise ValueError("El multiplicador del proveedor debe ser un número finito.")
        multiplicador = multiplicador.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        if multiplicador <= Decimal("0.0000") or multiplicador > MAX_PRECISION_12_4:
            raise ValueError("El multiplicador del proveedor debe ser un número positivo y dentro del rango permitido para Numeric(12,4).")

    try:
        material_proveedor = MaterialProveedor(
            id_material=id_mat,
            proveedor=proveedor_str,
            sku=sku_str,
            referencia=str(producto.get("referencia")).strip() if producto.get("referencia") else None,
            termino_busqueda=termino_busqueda.strip(),
            nombre_producto=str(nombre_producto).strip(),
            marca=str(producto.get("marca")).strip() if producto.get("marca") else None,
            enlace=str(producto.get("enlace")).strip() if producto.get("enlace") else None,
            unidad_proveedor=str(producto.get("unidad")).strip() if producto.get("unidad") else None,
            multiplicador_proveedor=multiplicador,
            factor_conversion=dec_factor,
            activo=True
        )

        db.session.add(material_proveedor)
        db.session.commit()
        return material_proveedor

    except ValueError:
        db.session.rollback()
        raise
    except Exception as exc:
        db.session.rollback()
        raise RuntimeError("Error inesperado al asociar el producto al material.") from exc


def actualizar_precio_material_proveedor(id_material_proveedor):
    """Consulta el proveedor y actualiza el historial protegiendo las consultas iniciales ante errores de BD."""
    id_mp = _validar_identificador(id_material_proveedor, "El identificador de la asociación MaterialProveedor")

    try:
        mp = db.session.get(MaterialProveedor, id_mp)
    except Exception as exc:
        db.session.rollback()
        raise RuntimeError("Error al consultar la base de datos para obtener la asociación.") from exc

    if mp is None or not mp.activo:
        return {"status": "no_encontrado", "mensaje": "La asociación de material con proveedor no existe o no está activa."}

    manager = ScraperManager()
    try:
        resultados = manager.search(mp.proveedor, mp.termino_busqueda, from_index=0, to_index=49)
    except Exception as exc:
        raise RuntimeError(f"Error al consultar el proveedor '{mp.proveedor}': {str(exc)}") from exc

    ofertas_coincidentes = []
    for prod in resultados:
        if not isinstance(prod, dict):
            continue
        p_proveedor = str(prod.get("proveedor", "")).strip().lower()
        p_sku = str(prod.get("sku", "")).strip()
        if p_proveedor == mp.proveedor and p_sku == mp.sku:
            ofertas_coincidentes.append(prod)

    if not ofertas_coincidentes:
        return {"status": "sin_coincidencia", "mensaje": "No se encontró una coincidencia exacta de proveedor y SKU en los resultados de búsqueda."}

    try:
        registros_guardados = 0
        for oferta in ofertas_coincidentes:
            raw_precio = oferta.get("precio")
            if raw_precio is None:
                continue
            try:
                precio = Decimal(str(raw_precio)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            except (InvalidOperation, ValueError, TypeError):
                continue

            if not precio.is_finite() or precio <= Decimal("0.00") or precio > MAX_PRECISION_14_2:
                continue

            raw_precio_lista = oferta.get("precio_lista")
            precio_lista = None
            if raw_precio_lista is not None:
                try:
                    pl = Decimal(str(raw_precio_lista)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    if pl.is_finite() and Decimal("0.00") < pl <= MAX_PRECISION_14_2:
                        precio_lista = pl
                except (InvalidOperation, ValueError, TypeError):
                    pass

            disponibilidad = None
            raw_disp = oferta.get("disponibilidad")
            if raw_disp is not None and not isinstance(raw_disp, bool):
                try:
                    if isinstance(raw_disp, int):
                        if raw_disp >= 0:
                            disponibilidad = raw_disp
                    else:
                        s_disp = str(raw_disp).strip()
                        if '.' in s_disp or 'e' in s_disp.lower():
                            disponibilidad = None
                        else:
                            d_int = int(s_disp)
                            if d_int >= 0:
                                disponibilidad = d_int
                except (ValueError, TypeError):
                    disponibilidad = None

            vendedor = str(oferta.get("vendedor")).strip() if oferta.get("vendedor") else None
            seller_id = str(oferta.get("seller_id")).strip() if oferta.get("seller_id") else None
            
            seller_default = oferta.get("seller_default")
            if not isinstance(seller_default, bool):
                seller_default = None

            enlace = str(oferta.get("enlace")).strip() if oferta.get("enlace") else None

            precio_por_unidad_material = None
            if mp.factor_conversion is not None:
                try:
                    calculo = precio / mp.factor_conversion
                    p_unidad = calculo.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    if p_unidad.is_finite() and Decimal("0.00") < p_unidad <= MAX_PRECISION_14_2:
                        precio_por_unidad_material = p_unidad
                except (InvalidOperation, ValueError, TypeError, ZeroDivisionError):
                    precio_por_unidad_material = None

            historial = HistorialPrecioMaterial(
                id_material_proveedor=mp.id_material_proveedor,
                precio=precio,
                precio_lista=precio_lista,
                disponibilidad=disponibilidad,
                vendedor=vendedor,
                seller_id=seller_id,
                seller_default=seller_default,
                precio_por_unidad_material=precio_por_unidad_material,
                enlace=enlace
            )

            db.session.add(historial)
            registros_guardados += 1

        if registros_guardados == 0:
            return {"status": "sin_precio_valido", "mensaje": "Se encontró el SKU pero ninguna oferta tenía un precio válido."}

        db.session.commit()
        return {
            "status": "actualizado",
            "registros_guardados": registros_guardados
        }

    except Exception as exc:
        db.session.rollback()
        raise RuntimeError("Error al persistir el historial de precios.") from exc


def actualizar_precios_proveedor(proveedor):
    """Actualiza de forma individual todas las asociaciones activas protegiendo la consulta inicial."""
    if not isinstance(proveedor, str) or not proveedor.strip():
        raise ValueError("El identificador del proveedor debe ser una cadena válida.")
    
    prov_key = proveedor.strip().lower()

    try:
        asociaciones = MaterialProveedor.query.filter_by(proveedor=prov_key, activo=True).all()
    except Exception as exc:
        db.session.rollback()
        raise RuntimeError("Error al consultar las asociaciones activas del proveedor.") from exc

    procesados = 0
    actualizados = 0
    registros_guardados = 0
    sin_coincidencia = 0
    sin_precio_valido = 0
    errores = 0

    for mp in asociaciones:
        procesados += 1
        try:
            resultado = actualizar_precio_material_proveedor(mp.id_material_proveedor)
            status = resultado.get("status")
            if status == "actualizado":
                actualizados += 1
                registros_guardados += resultado.get("registros_guardados", 0)
            elif status == "sin_coincidencia":
                sin_coincidencia += 1
            elif status == "sin_precio_valido":
                sin_precio_valido += 1
            else:
                errores += 1
        except Exception:
            errores += 1

    return {
        "proveedor": prov_key,
        "procesados": procesados,
        "actualizados": actualizados,
        "registros_guardados": registros_guardados,
        "sin_coincidencia": sin_coincidencia,
        "sin_precio_valido": sin_precio_valido,
        "errores": errores
    }


def listar_historial_precios(id_material_proveedor):
    """Lista el historial de precios ordenado del más reciente al más antiguo."""
    id_mp = _validar_identificador(id_material_proveedor, "El identificador de la asociación MaterialProveedor")

    try:
        mp = db.session.get(MaterialProveedor, id_mp)
        if mp is None:
            raise ValueError("La asociación MaterialProveedor indicada no existe.")

        return (
            HistorialPrecioMaterial.query
            .filter_by(id_material_proveedor=id_mp)
            .order_by(HistorialPrecioMaterial.fecha_consulta.desc(), HistorialPrecioMaterial.id_historial.desc())
            .all()
        )
    except ValueError:
        db.session.rollback()
        raise
    except Exception as exc:
        db.session.rollback()
        raise RuntimeError("Error al listar el historial de precios.") from exc