from flask import Blueprint

from app.controllers.presupuesto_controller import (
    api_crear_presupuesto,
    api_obtener_presupuesto,
    api_listar_presupuestos,
    api_agregar_detalle,
)


presupuesto_bp = Blueprint("presupuesto", __name__)


# Crear un presupuesto para un proyecto.
@presupuesto_bp.route(
    "/proyectos/<int:id_proyecto>/presupuestos",
    methods=["POST"]
)
def crear_presupuesto_route(id_proyecto):
    return api_crear_presupuesto(id_proyecto)


# Listar los presupuestos de un proyecto.
@presupuesto_bp.route(
    "/proyectos/<int:id_proyecto>/presupuestos",
    methods=["GET"]
)
def listar_presupuestos_route(id_proyecto):
    return api_listar_presupuestos(id_proyecto)


# Consultar un presupuesto específico.
@presupuesto_bp.route(
    "/presupuestos/<int:id_presupuesto>",
    methods=["GET"]
)
def obtener_presupuesto_route(id_presupuesto):
    return api_obtener_presupuesto(id_presupuesto)


# Agregar un detalle a un presupuesto.
@presupuesto_bp.route(
    "/presupuestos/<int:id_presupuesto>/detalles",
    methods=["POST"]
)
def agregar_detalle_route(id_presupuesto):
    return api_agregar_detalle(id_presupuesto)