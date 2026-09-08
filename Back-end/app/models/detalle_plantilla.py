from app.config.database import db


class DetallePlantilla(db.Model):
    __tablename__ = "detalle_plantilla"

    id_detalle_plantilla = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_plantilla = db.Column(
        db.Integer,
        db.ForeignKey("plantilla.id_plantilla"),
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

    plantilla = db.relationship(
        "Plantilla",
        back_populates="detalles"
    )

    material = db.relationship(
        "Material",
        back_populates="detalles_plantilla"
    )