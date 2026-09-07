from app.config.database import db


class DetallePresupuesto(db.Model):
    __tablename__ = "detalle_presupuesto"

    id_detalle = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_presupuesto = db.Column(
        db.Integer,
        db.ForeignKey("presupuesto.id_presupuesto"),
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

    presupuesto = db.relationship(
        "Presupuesto",
        back_populates="detalles"
    )

    material = db.relationship(
        "Material",
        back_populates="detalles_presupuesto"
    )