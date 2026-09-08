from datetime import datetime, timezone

from app.config.database import db


class Plantilla(db.Model):
    __tablename__ = "plantilla"

    id_plantilla = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario"),
        nullable=False
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

    usuario = db.relationship(
        "Usuario",
        back_populates="plantillas"
    )

    detalles = db.relationship(
        "DetallePlantilla",
        back_populates="plantilla"
    )