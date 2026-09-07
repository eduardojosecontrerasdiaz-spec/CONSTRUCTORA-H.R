from datetime import datetime

from app.config.database import db


class Rol(db.Model):
    __tablename__ = "rol"

    id_rol = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    nombre = db.Column(
        db.String(50),
        nullable=False,
        unique=True
    )

    descripcion = db.Column(
        db.String(255),
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
        default=datetime.utcnow
    )

    usuarios = db.relationship(
        "Usuario",
        back_populates="rol"
    )

    permisos = db.relationship(
        "Permiso",
        secondary="rol_permiso",
        back_populates="roles"
    )