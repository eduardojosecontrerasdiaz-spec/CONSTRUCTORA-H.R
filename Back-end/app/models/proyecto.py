from datetime import datetime, timezone

from app.config.database import db


class Proyecto(db.Model):
    __tablename__ = "proyecto"

    id_proyecto = db.Column(
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
        nullable=False
    )

    descripcion = db.Column(
        db.String(500),
        nullable=True
    )

    cliente = db.Column(
        db.String(150),
        nullable=False
    )

    ubicacion = db.Column(
        db.String(255),
        nullable=True
    )

    estado = db.Column(
        db.String(50),
        nullable=False,
        default="activo"
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship(
        "Usuario",
        back_populates="proyectos"
    )

    presupuestos = db.relationship(
        "Presupuesto",
        back_populates="proyecto"
    )

    ingresos = db.relationship(
        "Ingreso",
        back_populates="proyecto"
    )

    egresos = db.relationship(
        "Egreso",
        back_populates="proyecto"
    )