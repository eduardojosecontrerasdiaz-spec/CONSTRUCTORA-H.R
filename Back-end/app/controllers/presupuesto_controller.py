from flask import jsonify, request

from app.services.presupuesto_service import (
    crear_presupuesto,
    obtener_presupuesto_por_id,
    listar_presupuestos_por_proyecto,
    agregar_detalle_presupuesto,
)

from app.schemas.presupuesto_schema import (
    PresupuestoSchema,
    DetallePresupuestoSchema,
)


presupuesto_schema = PresupuestoSchema()
presupuestos_schema = PresupuestoSchema(many=True)
detalle_schema = DetallePresupuestoSchema()


def _respuesta_error_value(exc):
    mensaje = str(exc)

    if "no existe" in mensaje.lower():
        return jsonify({"error": mensaje}), 404

    return jsonify({"error": mensaje}), 400


def api_crear_presupuesto(id_proyecto):
    """Crea un presupuesto asociado a un proyecto."""

    json_data = request.get_json(silent=True)

    if not isinstance(json_data, dict):
        return jsonify({
            "error": "El cuerpo de la solicitud debe ser un JSON válido."
        }), 400

    # El ID de la URL tiene prioridad sobre cualquier ID enviado en el JSON.
    data = dict(json_data)
    data["id_proyecto"] = id_proyecto

    try:
        presupuesto = crear_presupuesto(data)

        return jsonify(
            presupuesto_schema.dump(presupuesto)
        ), 201

    except ValueError as exc:
        return _respuesta_error_value(exc)

    except RuntimeError:
        return jsonify({
            "error": "Error interno al procesar la solicitud en el servidor."
        }), 500


def api_obtener_presupuesto(id_presupuesto):
    """Consulta un presupuesto por su identificador."""

    try:
        presupuesto = obtener_presupuesto_por_id(id_presupuesto)

        if presupuesto is None:
            return jsonify({
                "error": "El presupuesto indicado no existe."
            }), 404

        return jsonify(
            presupuesto_schema.dump(presupuesto)
        ), 200

    except ValueError as exc:
        return _respuesta_error_value(exc)

    except RuntimeError:
        return jsonify({
            "error": "Error interno al procesar la solicitud en el servidor."
        }), 500


def api_listar_presupuestos(id_proyecto):
    """Lista los presupuestos asociados a un proyecto."""

    try:
        presupuestos = listar_presupuestos_por_proyecto(id_proyecto)

        return jsonify(
            presupuestos_schema.dump(presupuestos)
        ), 200

    except ValueError as exc:
        return _respuesta_error_value(exc)

    except RuntimeError:
        return jsonify({
            "error": "Error interno al procesar la solicitud en el servidor."
        }), 500


def api_agregar_detalle(id_presupuesto):
    """Agrega un material al presupuesto."""

    json_data = request.get_json(silent=True)

    if not isinstance(json_data, dict):
        return jsonify({
            "error": "El cuerpo de la solicitud debe ser un JSON válido."
        }), 400

    try:
        detalle = agregar_detalle_presupuesto(
            id_presupuesto,
            json_data
        )

        return jsonify(
            detalle_schema.dump(detalle)
        ), 201

    except ValueError as exc:
        return _respuesta_error_value(exc)

    except RuntimeError:
        return jsonify({
            "error": "Error interno al procesar la solicitud en el servidor."
        }), 500