from datetime import datetime, timezone

from app.config.database import db


class Presupuesto(db.Model):
    __tablename__ = "presupuesto"

    id_presupuesto = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_proyecto = db.Column(
        db.Integer,
        db.ForeignKey("proyecto.id_proyecto"),
        nullable=False
    )

    fecha = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    monto_total = db.Column(
        db.Numeric(14, 2),
        nullable=False,
        default=0
    )

    categoria = db.Column(
        db.String(100),
        nullable=False
    )

    estado = db.Column(
        db.String(50),
        nullable=False,
        default="borrador"
    )

    motivo_rechazo = db.Column(
        db.String(500),
        nullable=True
    )

    proyecto = db.relationship(
        "Proyecto",
        back_populates="presupuestos"
    )

    detalles = db.relationship(
        "DetallePresupuesto",
        back_populates="presupuesto"
    )

    versiones = db.relationship(
        "VersionPresupuesto",
        back_populates="presupuesto"
    )