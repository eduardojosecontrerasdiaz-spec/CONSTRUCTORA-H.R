from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app import db
from app.models.presupuesto import Presupuesto
from app.models.detalle_presupuesto import DetallePresupuesto
from app.models.material import Material
from app.models.proyecto import Proyecto


DOS_DECIMALES = Decimal("0.01")
CERO = Decimal("0.00")

# Límites de los campos NUMERIC de la base de datos.
MAX_CANTIDAD = Decimal("9999999999.99")
MAX_IMPORTE = Decimal("999999999999.99")


def _convertir_decimal(valor, nombre):
    """Convierte un valor a Decimal y rechaza valores no válidos."""
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{nombre} debe ser un número válido.")

    if not numero.is_finite():
        raise ValueError(f"{nombre} debe ser un número finito.")

    return numero


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


def _validar_limite_numeric(valor, maximo, nombre):
    """Comprueba que un valor no supere el límite permitido."""
    if valor > maximo:
        raise ValueError(
            f"{nombre} excede el límite máximo permitido "
            f"para Numeric({14 if maximo == MAX_IMPORTE else 12},2)."
        )


def crear_presupuesto(data):
    """Crea un presupuesto nuevo en estado borrador."""
    if not isinstance(data, dict):
        raise ValueError("Los datos del presupuesto deben ser un diccionario.")

    id_proyecto = _validar_identificador(
        data.get("id_proyecto"), "El identificador del proyecto"
    )

    categoria = data.get("categoria")
    if not isinstance(categoria, str) or not categoria.strip():
        raise ValueError("La categoría es obligatoria.")

    categoria = categoria.strip()
    if len(categoria) > 100:
        raise ValueError("La categoría no puede superar los 100 caracteres.")

    try:
        proyecto = db.session.get(Proyecto, id_proyecto)
    except Exception as exc:
        db.session.rollback()
        raise RuntimeError(
            "Error al consultar el proyecto en la base de datos."
        ) from exc

    if proyecto is None:
        raise ValueError("El proyecto indicado no existe.")

    try:
        presupuesto = Presupuesto(
            id_proyecto=id_proyecto,
            categoria=categoria,
            monto_total=CERO,
            estado="borrador",
        )

        db.session.add(presupuesto)
        db.session.commit()
        return presupuesto

    except Exception as exc:
        db.session.rollback()
        raise RuntimeError(
            "Error al guardar el presupuesto en la base de datos."
        ) from exc


def obtener_presupuesto_por_id(identificador):
    """Busca un presupuesto por su identificador."""
    id_presupuesto = _validar_identificador(
        identificador, "El identificador del presupuesto"
    )

    try:
        return db.session.get(Presupuesto, id_presupuesto)
    except Exception as exc:
        db.session.rollback()
        raise RuntimeError(
            "Error al consultar el presupuesto en la base de datos."
        ) from exc


def listar_presupuestos_por_proyecto(id_proyecto):
    """Lista los presupuestos asociados a un proyecto."""
    id_proyecto = _validar_identificador(
        id_proyecto, "El identificador del proyecto"
    )

    try:
        return (
            Presupuesto.query
            .filter_by(id_proyecto=id_proyecto)
            .all()
        )
    except Exception as exc:
        db.session.rollback()
        raise RuntimeError(
            "Error al listar los presupuestos del proyecto."
        ) from exc


def agregar_detalle_presupuesto(id_presupuesto, data):
    """Agrega un material al presupuesto y recalcula su monto total."""
    if not isinstance(data, dict):
        raise ValueError("Los datos del detalle deben ser un diccionario.")

    id_presupuesto = _validar_identificador(
        id_presupuesto, "El identificador del presupuesto"
    )
    id_material = _validar_identificador(
        data.get("id_material"), "El identificador del material"
    )

    cantidad = _convertir_decimal(
        data.get("cantidad"), "La cantidad"
    )

    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")

    cantidad = cantidad.quantize(
        DOS_DECIMALES, rounding=ROUND_HALF_UP
    )

    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")

    _validar_limite_numeric(
        cantidad, MAX_CANTIDAD, "La cantidad"
    )

    try:
        presupuesto = db.session.get(Presupuesto, id_presupuesto)
        material = db.session.get(Material, id_material)

        if presupuesto is None:
            raise ValueError("El presupuesto indicado no existe.")

        if material is None:
            raise ValueError("El material indicado no existe.")

        precio_unitario = _convertir_decimal(
            material.precio_material, "El precio del material"
        )

        if precio_unitario < 0:
            raise ValueError("El precio del material no puede ser negativo.")

        precio_unitario = precio_unitario.quantize(
            DOS_DECIMALES, rounding=ROUND_HALF_UP
        )

        subtotal = (cantidad * precio_unitario).quantize(
            DOS_DECIMALES, rounding=ROUND_HALF_UP
        )

        _validar_limite_numeric(
            subtotal, MAX_IMPORTE, "El subtotal"
        )

        detalle = DetallePresupuesto(
            id_presupuesto=id_presupuesto,
            id_material=id_material,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            subtotal=subtotal,
        )

        db.session.add(detalle)
        db.session.flush()

        detalles = (
            DetallePresupuesto.query
            .filter_by(id_presupuesto=id_presupuesto)
            .all()
        )

        monto_total = sum(
            (
                _convertir_decimal(
                    item.subtotal, "El subtotal del detalle"
                )
                for item in detalles
            ),
            CERO,
        ).quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)

        _validar_limite_numeric(
            monto_total, MAX_IMPORTE, "El monto total del presupuesto"
        )

        presupuesto.monto_total = monto_total

        db.session.commit()
        return detalle

    except ValueError:
        db.session.rollback()
        raise

    except Exception as exc:
        db.session.rollback()
        raise RuntimeError(
            "Error inesperado al persistir el detalle del presupuesto."
        ) from exc
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app import db
from app.models.presupuesto import Presupuesto
from app.models.detalle_presupuesto import DetallePresupuesto
from app.models.material import Material
from app.models.proyecto import Proyecto


DOS_DECIMALES = Decimal("0.01")
CERO = Decimal("0.00")

# Límites de los campos NUMERIC de la base de datos.
MAX_CANTIDAD = Decimal("9999999999.99")
MAX_IMPORTE = Decimal("999999999999.99")


def _convertir_decimal(valor, nombre):
    """Convierte un valor a Decimal y rechaza valores no válidos."""
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{nombre} debe ser un número válido.")

    if not numero.is_finite():
        raise ValueError(f"{nombre} debe ser un número finito.")

    return numero


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


def _validar_limite_numeric(valor, maximo, nombre):
    """Comprueba que un valor no supere el límite permitido."""
    if valor > maximo:
        raise ValueError(
            f"{nombre} excede el límite máximo permitido "
            f"para Numeric({14 if maximo == MAX_IMPORTE else 12},2)."
        )


def crear_presupuesto(data):
    """Crea un presupuesto nuevo en estado borrador."""
    if not isinstance(data, dict):
        raise ValueError("Los datos del presupuesto deben ser un diccionario.")

    id_proyecto = _validar_identificador(
        data.get("id_proyecto"), "El identificador del proyecto"
    )

    categoria = data.get("categoria")
    if not isinstance(categoria, str) or not categoria.strip():
        raise ValueError("La categoría es obligatoria.")

    categoria = categoria.strip()
    if len(categoria) > 100:
        raise ValueError("La categoría no puede superar los 100 caracteres.")

    try:
        proyecto = db.session.get(Proyecto, id_proyecto)
    except Exception as exc:
        db.session.rollback()
        raise RuntimeError(
            "Error al consultar el proyecto en la base de datos."
        ) from exc

    if proyecto is None:
        raise ValueError("El proyecto indicado no existe.")

    try:
        presupuesto = Presupuesto(
            id_proyecto=id_proyecto,
            categoria=categoria,
            monto_total=CERO,
            estado="borrador",
        )

        db.session.add(presupuesto)
        db.session.commit()
        return presupuesto

    except Exception as exc:
        db.session.rollback()
        raise RuntimeError(
            "Error al guardar el presupuesto en la base de datos."
        ) from exc


def obtener_presupuesto_por_id(identificador):
    """Busca un presupuesto por su identificador."""
    id_presupuesto = _validar_identificador(
        identificador, "El identificador del presupuesto"
    )

    try:
        return db.session.get(Presupuesto, id_presupuesto)
    except Exception as exc:
        db.session.rollback()
        raise RuntimeError(
            "Error al consultar el presupuesto en la base de datos."
        ) from exc


def listar_presupuestos_por_proyecto(id_proyecto):
    """Lista los presupuestos asociados a un proyecto."""
    id_proyecto = _validar_identificador(
        id_proyecto, "El identificador del proyecto"
    )

    try:
        return (
            Presupuesto.query
            .filter_by(id_proyecto=id_proyecto)
            .all()
        )
    except Exception as exc:
        db.session.rollback()
        raise RuntimeError(
            "Error al listar los presupuestos del proyecto."
        ) from exc


def agregar_detalle_presupuesto(id_presupuesto, data):
    """Agrega un material al presupuesto y recalcula su monto total."""
    if not isinstance(data, dict):
        raise ValueError("Los datos del detalle deben ser un diccionario.")

    id_presupuesto = _validar_identificador(
        id_presupuesto, "El identificador del presupuesto"
    )
    id_material = _validar_identificador(
        data.get("id_material"), "El identificador del material"
    )

    cantidad = _convertir_decimal(
        data.get("cantidad"), "La cantidad"
    )

    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")

    cantidad = cantidad.quantize(
        DOS_DECIMALES, rounding=ROUND_HALF_UP
    )

    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")

    _validar_limite_numeric(
        cantidad, MAX_CANTIDAD, "La cantidad"
    )

    try:
        presupuesto = db.session.get(Presupuesto, id_presupuesto)
        material = db.session.get(Material, id_material)

        if presupuesto is None:
            raise ValueError("El presupuesto indicado no existe.")

        if material is None:
            raise ValueError("El material indicado no existe.")

        precio_unitario = _convertir_decimal(
            material.precio_material, "El precio del material"
        )

        if precio_unitario < 0:
            raise ValueError("El precio del material no puede ser negativo.")

        precio_unitario = precio_unitario.quantize(
            DOS_DECIMALES, rounding=ROUND_HALF_UP
        )

        subtotal = (cantidad * precio_unitario).quantize(
            DOS_DECIMALES, rounding=ROUND_HALF_UP
        )

        _validar_limite_numeric(
            subtotal, MAX_IMPORTE, "El subtotal"
        )

        detalle = DetallePresupuesto(
            id_presupuesto=id_presupuesto,
            id_material=id_material,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            subtotal=subtotal,
        )

        db.session.add(detalle)
        db.session.flush()

        detalles = (
            DetallePresupuesto.query
            .filter_by(id_presupuesto=id_presupuesto)
            .all()
        )

        monto_total = sum(
            (
                _convertir_decimal(
                    item.subtotal, "El subtotal del detalle"
                )
                for item in detalles
            ),
            CERO,
        ).quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)

        _validar_limite_numeric(
            monto_total, MAX_IMPORTE, "El monto total del presupuesto"
        )

        presupuesto.monto_total = monto_total

        db.session.commit()
        return detalle

    except ValueError:
        db.session.rollback()
        raise

    except Exception as exc:
        db.session.rollback()
        raise RuntimeError(
            "Error inesperado al persistir el detalle del presupuesto."
        ) from exc
