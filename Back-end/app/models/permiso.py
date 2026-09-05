from datetime import datetime, timezone
from app.config.database import db

class Permiso(db.Model):
    __tablename__ = "permiso"

    id_permiso = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True
        )

    nombre = db.Column(
        db.String(100),
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
        default=lambda: datetime.now(timezone.utc)
    )