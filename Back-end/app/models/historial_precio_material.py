from datetime import datetime, timezone
from app.config.database import db


class HistorialPrecioMaterial(db.Model):
    __tablename__ = "historial_precio_material"

    __table_args__ = (
        db.CheckConstraint(
            "precio > 0",
            name="chk_hist_precio_positivo"
        ),
        db.CheckConstraint(
            "precio_lista IS NULL OR precio_lista > 0",
            name="chk_hist_precio_lista_positivo"
        ),
        db.CheckConstraint(
            "disponibilidad IS NULL OR disponibilidad >= 0",
            name="chk_hist_disponibilidad_no_negativa"
        ),
        db.CheckConstraint(
            "precio_por_unidad_material IS NULL OR precio_por_unidad_material > 0",
            name="chk_hist_precio_unidad_positivo"
        ),
    )

    id_historial = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_material_proveedor = db.Column(
        db.Integer,
        db.ForeignKey("material_proveedor.id_material_proveedor"),
        nullable=False
    )

    precio = db.Column(
        db.Numeric(14, 2),
        nullable=False
    )

    precio_lista = db.Column(
        db.Numeric(14, 2),
        nullable=True
    )

    disponibilidad = db.Column(
        db.Integer,
        nullable=True
    )

    vendedor = db.Column(
        db.String(150),
        nullable=True
    )

    seller_id = db.Column(
        db.String(100),
        nullable=True
    )

    seller_default = db.Column(
        db.Boolean,
        nullable=True
    )

    precio_por_unidad_material = db.Column(
        db.Numeric(14, 2),
        nullable=True
    )

    fecha_consulta = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    enlace = db.Column(
        db.String(500),
        nullable=True
    )

    # Relaciones
    material_proveedor = db.relationship(
        "MaterialProveedor",
        back_populates="historial_precios"
    )