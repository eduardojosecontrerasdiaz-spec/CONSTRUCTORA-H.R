from datetime import datetime, timezone

from app.config.database import db


class CodigoRecuperacion(db.Model):
    __tablename__ = "codigo_recuperacion"

    id_codigo = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario"),
        nullable=False
    )

    codigo = db.Column(
        db.String(255),
        nullable=False
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    fecha_expiracion = db.Column(
        db.DateTime,
        nullable=False
    )

    utilizado = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    usuario = db.relationship(
        "Usuario",
        back_populates="codigos_recuperacion"
    )