DROP TABLE IF EXISTS articulos;
DROP TABLE IF EXISTS clientes;
DROP TABLE IF EXISTS sucursales;
DROP TABLE IF EXISTS permisos;
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS abonos_separados;
DROP TABLE IF EXISTS ventas;
DROP TABLE IF EXISTS separados;
DROP TABLE IF EXISTS empresa;

CREATE TABLE sucursales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT
);

CREATE TABLE clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    cedula TEXT,
    celular TEXT,
    direccion TEXT,
    correo TEXT
);

CREATE TABLE articulos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articulo TEXT,
    precio REAL,
    costo REAL,
    codigo TEXT,
    stock INTEGER,
    sucursal INTEGER,
    stock_minimo INTEGER DEFAULT 0
);

CREATE TABLE permisos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rol TEXT NOT NULL,
    modulo TEXT NOT NULL
);

CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    rol TEXT,
    sucursal TEXT
);

CREATE TABLE empresa (
    id INTEGER PRIMARY KEY,
    nombre TEXT,
    direccion TEXT,
    telefono TEXT,
    email TEXT,
    website TEXT,
    nit TEXT
);

CREATE TABLE separados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factura INTEGER,
    cliente TEXT,
    producto TEXT,
    precio REAL,
    cantidad INTEGER,
    total REAL,
    abono REAL,
    deuda_restante NUMERIC DEFAULT 0,
    estado_deuda TEXT DEFAULT 'pendiente',
    fecha_separado TEXT,
    fecha_alerta TEXT,
    alerta_mostrada INTEGER DEFAULT 0,
    sucursal TEXT,
    metodo_pago TEXT,
    banco TEXT
);

CREATE TABLE abonos_separados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factura INTEGER,
    fecha TEXT,
    monto REAL,
    metodo_pago TEXT,
    banco TEXT,
    sucursal TEXT
);

CREATE TABLE ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factura INTEGER,
    cliente TEXT,
    articulo TEXT,
    precio REAL,
    cantidad INTEGER,
    total REAL,
    fecha TEXT,
    hora TEXT,
    costo REAL,
    metodo_pago TEXT,
    sucursal TEXT,
    descuento INTEGER,
    factura_separado INTEGER,
    banco TEXT,
    FOREIGN KEY(factura_separado) REFERENCES separados(factura)
);
