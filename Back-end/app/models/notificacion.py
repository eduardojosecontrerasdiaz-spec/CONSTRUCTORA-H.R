from datetime import datetime, timezone

from app.config.database import db


class Notificacion(db.Model):
    __tablename__ = "notificacion"

    id_notificacion = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario"),
        nullable=False
    )

    tipo = db.Column(
        db.String(50),
        nullable=False
    )

    mensaje = db.Column(
        db.String(500),
        nullable=False
    )

    canal = db.Column(
        db.String(50),
        nullable=False
    )

    estado = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship(
        "Usuario",
        back_populates="notificaciones"
    )