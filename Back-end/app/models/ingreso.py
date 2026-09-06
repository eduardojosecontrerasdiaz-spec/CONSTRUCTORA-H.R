from datetime import datetime, timezone

from app.config.database import db


class Ingreso(db.Model):
    __tablename__ = "ingreso"

    id_ingreso = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_proyecto = db.Column(
        db.Integer,
        db.ForeignKey("proyecto.id_proyecto"),
        nullable=False
    )

    concepto = db.Column(
        db.String(255),
        nullable=False
    )

    monto = db.Column(
        db.Numeric(14, 2),
        nullable=False
    )

    fecha = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    estado = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )