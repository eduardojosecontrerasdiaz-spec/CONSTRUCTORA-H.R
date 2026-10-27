from marshmallow import Schema, fields


class DetallePresupuestoSchema(Schema):
    """
    Schema para la entidad DetallePresupuesto utilizando los campos reales
    del modelo (id_detalle, id_presupuesto, id_material, cantidad, precio_unitario, subtotal).
    Se utiliza fields.Decimal para preservar la precisión monetaria y numérica (db.Numeric).
    """
    id_detalle = fields.Int(dump_only=True)
    id_presupuesto = fields.Int(dump_only=True)
    id_material = fields.Int(required=True)
    cantidad = fields.Decimal(required=True, as_string=True, places=2)
    precio_unitario = fields.Decimal(required=True, as_string=True, places=2)
    subtotal = fields.Decimal(as_string=True, places=2)


class PresupuestoSchema(Schema):
    """
    Schema para la entidad Presupuesto utilizando los campos reales del modelo
    (id_presupuesto, id_proyecto, categoria, monto_total, estado, fecha, motivo_rechazo).
    """
    id_presupuesto = fields.Int(dump_only=True)
    id_proyecto = fields.Int(required=True)
    categoria = fields.Str(required=True)
    monto_total = fields.Decimal(as_string=True, places=2)
    estado = fields.Str()
    fecha = fields.DateTime(dump_only=True)
    motivo_rechazo = fields.Str(allow_none=True)
    
    # Declarado como dump_only por defecto para evitar asumir inserción anidada
    # sin el flujo de negocio documentado.
    detalles = fields.Nested(DetallePresupuestoSchema, many=True, dump_only=True)