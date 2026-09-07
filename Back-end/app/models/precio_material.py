from datetime import datetime, timezone

from app.config.database import db


class PrecioMaterial(db.Model):
    __tablename__ = "precio_material"

    id_precio = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_material = db.Column(
        db.Integer,
        db.ForeignKey("material.id_material"),
        nullable=False
    )

    precio = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    fecha_inicio = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    fecha_fin = db.Column(
        db.DateTime,
        nullable=True
    )

    fuente = db.Column(
        db.String(255),
        nullable=True
    )

    estado = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    material = db.relationship(
        "Material",
        back_populates="precios"
    )