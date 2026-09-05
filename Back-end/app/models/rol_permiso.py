from app.config.database import db

class RolPermiso(db.Model):
    __tablename__ = "rol_permiso"

    id_rol = db.Column(
        db.Integer, 
        db.ForeignKey("rol.id_rol"), 
        primary_key=True, 
        nullable=False
    )
    id_permiso = db.Column(
        db.Integer, 
        db.ForeignKey("permiso.id_permiso"), 
        primary_key=True, 
        nullable=False
    )