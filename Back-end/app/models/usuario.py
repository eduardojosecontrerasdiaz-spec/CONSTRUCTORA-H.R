from datetime import datetime, timezone

from app.config.database import db


class Usuario(db.Model):
    __tablename__ = "usuario"

    id_usuario = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_rol = db.Column(
        db.Integer,
        db.ForeignKey("rol.id_rol"),
        nullable=False
    )

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    apellido = db.Column(
        db.String(100),
        nullable=False
    )

    correo = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    contrasena = db.Column(
        db.String(255),
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

    rol = db.relationship(
        "Rol",
        back_populates="usuarios"
    )

    codigos_recuperacion = db.relationship(
        "CodigoRecuperacion",
        back_populates="usuario"
    )