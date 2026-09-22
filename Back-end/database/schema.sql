-- Schema DDL para CONSTRUCTORA-H.R
-- Alineación 1:1 con los modelos SQLAlchemy

CREATE DATABASE IF NOT EXISTS constructora_hr_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE constructora_hr_db;


-- =========================================================
-- 1. ROL
-- =========================================================

CREATE TABLE IF NOT EXISTS rol (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255) NULL
);


-- =========================================================
-- 2. PERMISO
-- =========================================================

CREATE TABLE IF NOT EXISTS permiso (
    id_permiso INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(255) NULL
);


-- =========================================================
-- 3. ROL_PERMISO
-- =========================================================

CREATE TABLE IF NOT EXISTS rol_permiso (
    id_rol INT NOT NULL,
    id_permiso INT NOT NULL,

    PRIMARY KEY (id_rol, id_permiso),

    CONSTRAINT fk_rol_permiso_rol
        FOREIGN KEY (id_rol)
        REFERENCES rol(id_rol)
        ON DELETE CASCADE,

    CONSTRAINT fk_rol_permiso_permiso
        FOREIGN KEY (id_permiso)
        REFERENCES permiso(id_permiso)
        ON DELETE CASCADE
);


-- =========================================================
-- 4. USUARIO
-- =========================================================

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Activo',
    id_rol INT NOT NULL,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_usuario_rol
        FOREIGN KEY (id_rol)
        REFERENCES rol(id_rol)
);


-- =========================================================
-- 5. CODIGO_RECUPERACION
-- =========================================================

CREATE TABLE IF NOT EXISTS codigo_recuperacion (
    id_codigo INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    codigo VARCHAR(6) NOT NULL,
    expiracion DATETIME NOT NULL,
    usado BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT fk_codigo_recuperacion_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
        ON DELETE CASCADE
);


-- =========================================================
-- 6. PROYECTO
-- =========================================================

CREATE TABLE IF NOT EXISTS proyecto (
    id_proyecto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'En Planificación',
    id_usuario INT NOT NULL,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_proyecto_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
);


-- =========================================================
-- 7. MATERIAL
-- =========================================================

CREATE TABLE IF NOT EXISTS material (
    id_material INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL UNIQUE,
    descripcion TEXT NULL,
    unidad_medida VARCHAR(20) NOT NULL,
    precio_material DECIMAL(12, 2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Activo',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- 8. PRESUPUESTO
-- =========================================================

CREATE TABLE IF NOT EXISTS presupuesto (
    id_presupuesto INT AUTO_INCREMENT PRIMARY KEY,
    id_proyecto INT NOT NULL,
    monto_total DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    estado VARCHAR(50) NOT NULL DEFAULT 'Borrador',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_presupuesto_proyecto
        FOREIGN KEY (id_proyecto)
        REFERENCES proyecto(id_proyecto)
        ON DELETE CASCADE
);


-- =========================================================
-- 9. DETALLE_PRESUPUESTO
-- =========================================================

CREATE TABLE IF NOT EXISTS detalle_presupuesto (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_presupuesto INT NOT NULL,
    id_material INT NOT NULL,
    cantidad DECIMAL(10, 2) NOT NULL,
    precio_unitario DECIMAL(12, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,

    CONSTRAINT fk_detalle_presupuesto_presupuesto
        FOREIGN KEY (id_presupuesto)
        REFERENCES presupuesto(id_presupuesto)
        ON DELETE CASCADE,

    CONSTRAINT fk_detalle_presupuesto_material
        FOREIGN KEY (id_material)
        REFERENCES material(id_material)
);


-- =========================================================
-- 10. VERSION_PRESUPUESTO
-- =========================================================

CREATE TABLE IF NOT EXISTS version_presupuesto (
    id_version INT AUTO_INCREMENT PRIMARY KEY,
    id_presupuesto INT NOT NULL,
    numero_version INT NOT NULL,
    monto_total DECIMAL(14, 2) NOT NULL,
    motivo VARCHAR(255) NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'Aprobado',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_version_presupuesto_presupuesto
        FOREIGN KEY (id_presupuesto)
        REFERENCES presupuesto(id_presupuesto)
        ON DELETE CASCADE
);


-- =========================================================
-- 11. DETALLE_VERSION_PRESUPUESTO
-- =========================================================

CREATE TABLE IF NOT EXISTS detalle_version_presupuesto (
    id_detalle_version INT AUTO_INCREMENT PRIMARY KEY,
    id_version INT NOT NULL,
    id_material INT NOT NULL,
    cantidad DECIMAL(10, 2) NOT NULL,
    precio_unitario DECIMAL(12, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,

    CONSTRAINT fk_detalle_version_version
        FOREIGN KEY (id_version)
        REFERENCES version_presupuesto(id_version)
        ON DELETE CASCADE,

    CONSTRAINT fk_detalle_version_material
        FOREIGN KEY (id_material)
        REFERENCES material(id_material)
);


-- =========================================================
-- 12. PLANTILLA
-- =========================================================

CREATE TABLE IF NOT EXISTS plantilla (
    id_plantilla INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Activa',
    id_usuario INT NOT NULL,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_plantilla_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
);


-- =========================================================
-- 13. DETALLE_PLANTILLA
-- =========================================================

CREATE TABLE IF NOT EXISTS detalle_plantilla (
    id_detalle_plantilla INT AUTO_INCREMENT PRIMARY KEY,
    id_plantilla INT NOT NULL,
    id_material INT NOT NULL,
    cantidad DECIMAL(10, 2) NOT NULL,
    precio_unitario DECIMAL(12, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,

    CONSTRAINT fk_detalle_plantilla_plantilla
        FOREIGN KEY (id_plantilla)
        REFERENCES plantilla(id_plantilla)
        ON DELETE CASCADE,

    CONSTRAINT fk_detalle_plantilla_material
        FOREIGN KEY (id_material)
        REFERENCES material(id_material)
);


-- =========================================================
-- 14. INGRESO
-- =========================================================

CREATE TABLE IF NOT EXISTS ingreso (
    id_ingreso INT AUTO_INCREMENT PRIMARY KEY,
    id_proyecto INT NOT NULL,
    monto DECIMAL(12, 2) NOT NULL,
    concepto VARCHAR(255) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Registrado',
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ingreso_proyecto
        FOREIGN KEY (id_proyecto)
        REFERENCES proyecto(id_proyecto)
        ON DELETE CASCADE
);


-- =========================================================
-- 15. EGRESO
-- =========================================================

CREATE TABLE IF NOT EXISTS egreso (
    id_egreso INT AUTO_INCREMENT PRIMARY KEY,
    id_proyecto INT NOT NULL,
    monto DECIMAL(12, 2) NOT NULL,
    concepto VARCHAR(255) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Registrado',
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_egreso_proyecto
        FOREIGN KEY (id_proyecto)
        REFERENCES proyecto(id_proyecto)
        ON DELETE CASCADE
);


-- =========================================================
-- 16. NOTIFICACION
-- =========================================================

CREATE TABLE IF NOT EXISTS notificacion (
    id_notificacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    mensaje TEXT NOT NULL,
    tipo VARCHAR(50) NOT NULL DEFAULT 'Informativa',
    estado VARCHAR(20) NOT NULL DEFAULT 'No Leída',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notificacion_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
        ON DELETE CASCADE
);


-- =========================================================
-- 17. AUDITORIA
-- =========================================================

CREATE TABLE IF NOT EXISTS auditoria (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    accion VARCHAR(100) NOT NULL,
    id_entidad INT NOT NULL,
    nombre_entidad VARCHAR(50) NOT NULL,
    detalles TEXT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_auditoria_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
);