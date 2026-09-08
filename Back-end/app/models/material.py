from datetime import datetime, timezone

from app.config.database import db


class Material(db.Model):
    __tablename__ = "material"

    id_material = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    nombre = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    descripcion = db.Column(
        db.String(500),
        nullable=True
    )

    unidad_medida = db.Column(
        db.String(50),
        nullable=False
    )

    estado = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    precios = db.relationship(
        "PrecioMaterial",
        back_populates="material"
    )

    detalles_presupuesto = db.relationship(
        "DetallePresupuesto",
        back_populates="material"
    )

    detalles_version_presupuesto = db.relationship(
        "DetalleVersionPresupuesto",
        back_populates="material"
    )

    detalles_plantilla = db.relationship(
        "DetallePlantilla",
        back_populates="material"
    )