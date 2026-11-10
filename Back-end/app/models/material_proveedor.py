from datetime import datetime, timezone
from app.config.database import db


class MaterialProveedor(db.Model):
    __tablename__ = "material_proveedor"

    __table_args__ = (
        db.UniqueConstraint("proveedor", "sku", name="uq_proveedor_sku"),
        db.CheckConstraint(
            "multiplicador_proveedor IS NULL OR multiplicador_proveedor > 0",
            name="chk_mat_prov_multiplicador_positivo"
        ),
        db.CheckConstraint(
            "factor_conversion IS NULL OR factor_conversion > 0",
            name="chk_mat_prov_factor_positivo"
        ),
    )

    id_material_proveedor = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_material = db.Column(
        db.Integer,
        db.ForeignKey("material.id_material"),
        nullable=False
    )

    proveedor = db.Column(
        db.String(100),
        nullable=False
    )

    sku = db.Column(
        db.String(150),
        nullable=False
    )

    referencia = db.Column(
        db.String(150),
        nullable=True
    )

    termino_busqueda = db.Column(
        db.String(255),
        nullable=False
    )

    nombre_producto = db.Column(
        db.String(255),
        nullable=False
    )

    marca = db.Column(
        db.String(150),
        nullable=True
    )

    enlace = db.Column(
        db.String(500),
        nullable=True
    )

    unidad_proveedor = db.Column(
        db.String(50),
        nullable=True
    )

    multiplicador_proveedor = db.Column(
        db.Numeric(12, 4),
        nullable=True
    )

    factor_conversion = db.Column(
        db.Numeric(12, 4),
        nullable=True
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relaciones
    material = db.relationship(
        "Material",
        back_populates="materiales_proveedores"
    )

    historial_precios = db.relationship(
        "HistorialPrecioMaterial",
        back_populates="material_proveedor",
        cascade="save-update, merge"
    )