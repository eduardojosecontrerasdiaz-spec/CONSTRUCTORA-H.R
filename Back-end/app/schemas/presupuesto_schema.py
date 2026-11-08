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
    
    # Declarado como dump_only por defecto para evitar inserción anidada directa.
    detalles = fields.Nested(DetallePresupuestoSchema, many=True, dump_only=True)


class DetalleVersionPresupuestoSchema(Schema):
    """
    Schema para la entidad DetalleVersionPresupuesto utilizando los campos reales
    del modelo (id_detalle_version, id_version, id_material, cantidad, precio_unitario, subtotal).
    Configurado completamente como dump_only ya que los detalles históricos son de solo lectura.
    """
    id_detalle_version = fields.Int(dump_only=True)
    id_version = fields.Int(dump_only=True)
    id_material = fields.Int(dump_only=True)
    cantidad = fields.Decimal(as_string=True, places=2, dump_only=True)
    precio_unitario = fields.Decimal(as_string=True, places=2, dump_only=True)
    subtotal = fields.Decimal(as_string=True, places=2, dump_only=True)


class VersionPresupuestoSchema(Schema):
    """
    Schema para la entidad VersionPresupuesto utilizando los campos reales del modelo
    (id_version, id_presupuesto, numero_version, monto_total, fecha_creacion, motivo, estado).
    Permite la entrada del motivo y restringe el resto de campos controlados por el sistema a dump_only.
    """
    id_version = fields.Int(dump_only=True)
    id_presupuesto = fields.Int(dump_only=True)
    numero_version = fields.Int(dump_only=True)
    monto_total = fields.Decimal(as_string=True, places=2, dump_only=True)
    fecha_creacion = fields.DateTime(dump_only=True)
    motivo = fields.Str(allow_none=True)
    estado = fields.Str(dump_only=True)
    
    # Relación anidada con los detalles históricos utilizando el nombre real de la relación ORM.
    detalles = fields.Nested(DetalleVersionPresupuestoSchema, many=True, dump_only=True)