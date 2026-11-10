-- Script idempotente para crear las tablas de vinculación y precios de proveedores
USE constructora_hr_db;

CREATE TABLE IF NOT EXISTS material_proveedor (
    id_material_proveedor INT AUTO_INCREMENT PRIMARY KEY,
    id_material INT NOT NULL,
    proveedor VARCHAR(100) NOT NULL,
    sku VARCHAR(150) NOT NULL,
    referencia VARCHAR(150) NULL,
    termino_busqueda VARCHAR(255) NOT NULL,
    nombre_producto VARCHAR(255) NOT NULL,
    marca VARCHAR(150) NULL,
    enlace VARCHAR(500) NULL,
    unidad_proveedor VARCHAR(50) NULL,
    multiplicador_proveedor DECIMAL(12, 4) NULL,
    factor_conversion DECIMAL(12, 4) NULL,
    activo BOOLEAN NOT NULL DEFAULT 1,
    fecha_creacion DATETIME NOT NULL,
    CONSTRAINT uq_proveedor_sku UNIQUE (proveedor, sku),
    CONSTRAINT chk_mat_prov_multiplicador_positivo CHECK (multiplicador_proveedor IS NULL OR multiplicador_proveedor > 0),
    CONSTRAINT chk_mat_prov_factor_positivo CHECK (factor_conversion IS NULL OR factor_conversion > 0),
    FOREIGN KEY (id_material) REFERENCES material(id_material)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS historial_precio_material (
    id_historial INT AUTO_INCREMENT PRIMARY KEY,
    id_material_proveedor INT NOT NULL,
    precio DECIMAL(14, 2) NOT NULL,
    precio_lista DECIMAL(14, 2) NULL,
    disponibilidad INT NULL,
    vendedor VARCHAR(150) NULL,
    seller_id VARCHAR(100) NULL,
    seller_default BOOLEAN NULL,
    precio_por_unidad_material DECIMAL(14, 2) NULL,
    fecha_consulta DATETIME NOT NULL,
    enlace VARCHAR(500) NULL,
    CONSTRAINT chk_hist_precio_positivo CHECK (precio > 0),
    CONSTRAINT chk_hist_precio_lista_positivo CHECK (precio_lista IS NULL OR precio_lista > 0),
    CONSTRAINT chk_hist_disponibilidad_no_negativa CHECK (disponibilidad IS NULL OR disponibilidad >= 0),
    CONSTRAINT chk_hist_precio_unidad_positivo CHECK (precio_por_unidad_material IS NULL OR precio_por_unidad_material > 0),
    FOREIGN KEY (id_material_proveedor) REFERENCES material_proveedor(id_material_proveedor)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;