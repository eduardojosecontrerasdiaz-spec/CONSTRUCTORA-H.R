

CREATE DATABASE IF NOT EXISTS constructora_hr_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE constructora_hr_db;

CREATE TABLE IF NOT EXISTS rol (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255) NULL,
    estado BOOLEAN NOT NULL,
    fecha_creacion DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS permiso (
    id_permiso INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(255) NULL,
    estado BOOLEAN NOT NULL,
    fecha_creacion DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS rol_permiso (
    id_rol INT NOT NULL,
    id_permiso INT NOT NULL,
    PRIMARY KEY (id_rol, id_permiso),
    FOREIGN KEY (id_rol) REFERENCES rol(id_rol),
    FOREIGN KEY (id_permiso) REFERENCES permiso(id_permiso)
);

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    id_rol INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    estado BOOLEAN NOT NULL,
    fecha_creacion DATETIME NOT NULL,
    FOREIGN KEY (id_rol) REFERENCES rol(id_rol)
);

CREATE TABLE IF NOT EXISTS codigo_recuperacion (
    id_codigo INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    codigo VARCHAR(255) NOT NULL,
    fecha_creacion DATETIME NOT NULL,
    fecha_expiracion DATETIME NOT NULL,
    utilizado BOOLEAN NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

CREATE TABLE IF NOT EXISTS proyecto (
    id_proyecto INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    descripcion VARCHAR(500) NULL,
    cliente VARCHAR(150) NOT NULL,
    ubicacion VARCHAR(255) NULL,
    estado VARCHAR(50) NOT NULL,
    fecha_creacion DATETIME NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

CREATE TABLE IF NOT EXISTS material (
    id_material INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL UNIQUE,
    descripcion VARCHAR(500) NULL,
    unidad_medida VARCHAR(50) NOT NULL,
    precio_material DECIMAL(12, 2) NOT NULL,
    estado BOOLEAN NOT NULL,
    fecha_creacion DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS presupuesto (
    id_presupuesto INT AUTO_INCREMENT PRIMARY KEY,
    id_proyecto INT NOT NULL,
    fecha DATETIME NOT NULL,
    monto_total DECIMAL(14, 2) NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    estado VARCHAR(50) NOT NULL,
    motivo_rechazo VARCHAR(500) NULL,
    FOREIGN KEY (id_proyecto) REFERENCES proyecto(id_proyecto)
);

CREATE TABLE IF NOT EXISTS detalle_presupuesto (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_presupuesto INT NOT NULL,
    id_material INT NOT NULL,
    cantidad DECIMAL(12, 2) NOT NULL,
    precio_unitario DECIMAL(14, 2) NOT NULL,
    subtotal DECIMAL(14, 2) NOT NULL,
    FOREIGN KEY (id_presupuesto) REFERENCES presupuesto(id_presupuesto),
    FOREIGN KEY (id_material) REFERENCES material(id_material)
);

CREATE TABLE IF NOT EXISTS version_presupuesto (
    id_version INT AUTO_INCREMENT PRIMARY KEY,
    id_presupuesto INT NOT NULL,
    numero_version INT NOT NULL,
    monto_total DECIMAL(14, 2) NOT NULL,
    fecha_creacion DATETIME NOT NULL,
    motivo VARCHAR(500) NULL,
    estado VARCHAR(50) NOT NULL,
    FOREIGN KEY (id_presupuesto) REFERENCES presupuesto(id_presupuesto)
);

CREATE TABLE IF NOT EXISTS detalle_version_presupuesto (
    id_detalle_version INT AUTO_INCREMENT PRIMARY KEY,
    id_version INT NOT NULL,
    id_material INT NOT NULL,
    cantidad DECIMAL(12, 2) NOT NULL,
    precio_unitario DECIMAL(14, 2) NOT NULL,
    subtotal DECIMAL(14, 2) NOT NULL,
    FOREIGN KEY (id_version) REFERENCES version_presupuesto(id_version),
    FOREIGN KEY (id_material) REFERENCES material(id_material)
);

CREATE TABLE IF NOT EXISTS plantilla (
    id_plantilla INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    nombre VARCHAR(150) NOT NULL UNIQUE,
    descripcion VARCHAR(500) NULL,
    estado BOOLEAN NOT NULL,
    fecha_creacion DATETIME NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

CREATE TABLE IF NOT EXISTS detalle_plantilla (
    id_detalle_plantilla INT AUTO_INCREMENT PRIMARY KEY,
    id_plantilla INT NOT NULL,
    id_material INT NOT NULL,
    cantidad DECIMAL(12, 2) NOT NULL,
    precio_unitario DECIMAL(14, 2) NOT NULL,
    subtotal DECIMAL(14, 2) NOT NULL,
    FOREIGN KEY (id_plantilla) REFERENCES plantilla(id_plantilla),
    FOREIGN KEY (id_material) REFERENCES material(id_material)
);

CREATE TABLE IF NOT EXISTS ingreso (
    id_ingreso INT AUTO_INCREMENT PRIMARY KEY,
    id_proyecto INT NOT NULL,
    concepto VARCHAR(255) NOT NULL,
    monto DECIMAL(14, 2) NOT NULL,
    fecha DATETIME NOT NULL,
    estado BOOLEAN NOT NULL,
    FOREIGN KEY (id_proyecto) REFERENCES proyecto(id_proyecto)
);

CREATE TABLE IF NOT EXISTS egreso (
    id_egreso INT AUTO_INCREMENT PRIMARY KEY,
    id_proyecto INT NOT NULL,
    concepto VARCHAR(255) NOT NULL,
    monto DECIMAL(14, 2) NOT NULL,
    fecha DATETIME NOT NULL,
    estado BOOLEAN NOT NULL,
    FOREIGN KEY (id_proyecto) REFERENCES proyecto(id_proyecto)
);

CREATE TABLE IF NOT EXISTS notificacion (
    id_notificacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    mensaje VARCHAR(500) NOT NULL,
    canal VARCHAR(50) NOT NULL,
    estado BOOLEAN NOT NULL,
    fecha_creacion DATETIME NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

CREATE TABLE IF NOT EXISTS auditoria (
    id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    accion VARCHAR(100) NOT NULL,
    entidad VARCHAR(100) NOT NULL,
    id_entidad INT NULL,
    descripcion VARCHAR(500) NULL,
    fecha DATETIME NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);
