from datetime import datetime, timezone

from app.config.database import db


class VersionPresupuesto(db.Model):
    __tablename__ = "version_presupuesto"

    id_version = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_presupuesto = db.Column(
        db.Integer,
        db.ForeignKey("presupuesto.id_presupuesto"),
        nullable=False
    )

    numero_version = db.Column(
        db.Integer,
        nullable=False
    )

    monto_total = db.Column(
        db.Numeric(14, 2),
        nullable=False,
        default=0
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    motivo = db.Column(
        db.String(500),
        nullable=True
    )

    estado = db.Column(
        db.String(50),
        nullable=False,
        default="activa"
    )

    presupuesto = db.relationship(
        "Presupuesto",
        back_populates="versiones"
    )

    detalles = db.relationship(
        "DetalleVersionPresupuesto",
        back_populates="version"
    )