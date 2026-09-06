from app.config.database import db


class DetalleVersionPresupuesto(db.Model):
    __tablename__ = "detalle_version_presupuesto"

    id_detalle_version = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_version = db.Column(
        db.Integer,
        db.ForeignKey("version_presupuesto.id_version"),
        nullable=False
    )

    id_material = db.Column(
        db.Integer,
        db.ForeignKey("material.id_material"),
        nullable=False
    )

    cantidad = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    precio_unitario = db.Column(
        db.Numeric(14, 2),
        nullable=False
    )

    subtotal = db.Column(
        db.Numeric(14, 2),
        nullable=False,
        default=0
    )