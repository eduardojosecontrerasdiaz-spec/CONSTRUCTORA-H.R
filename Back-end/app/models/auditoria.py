from datetime import datetime, timezone

from app.config.database import db


class Auditoria(db.Model):
    __tablename__ = "auditoria"

    id_auditoria = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario"),
        nullable=False
    )

    accion = db.Column(
        db.String(100),
        nullable=False
    )

    entidad = db.Column(
        db.String(100),
        nullable=False
    )

    id_entidad = db.Column(
        db.Integer,
        nullable=True
    )

    descripcion = db.Column(
        db.String(500),
        nullable=True
    )

    fecha = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship(
        "Usuario",
        back_populates="auditorias"
    )