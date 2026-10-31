from sqlalchemy import Column, Integer, String, Float, Numeric, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Sucursal(Base):
    __tablename__ = "sucursales"
    id = Column(Integer, primary_key=True)
    nombre = Column(String)


class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    cedula = Column(String)
    celular = Column(String)
    direccion = Column(String)
    correo = Column(String)


class Articulo(Base):
    __tablename__ = "articulos"
    id = Column(Integer, primary_key=True)
    articulo = Column(String)
    precio = Column(Float)
    costo = Column(Float)
    codigo = Column(String)
    stock = Column(Integer)
    sucursal = Column(Integer, ForeignKey("sucursales.id"))
    stock_minimo = Column(Integer, default=0)

    sucursal_obj = relationship("Sucursal")


class Permiso(Base):
    __tablename__ = "permisos"
    id = Column(Integer, primary_key=True)
    rol = Column(String, nullable=False)
    modulo = Column(String, nullable=False)


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    rol = Column(String)
    sucursal = Column(String)


class Empresa(Base):
    __tablename__ = "empresa"
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    direccion = Column(String)
    telefono = Column(String)
    email = Column(String)
    website = Column(String)
    nit = Column(String)
    codigo_registro = Column(String)


class Venta(Base):
    __tablename__ = "ventas"
    id = Column(Integer, primary_key=True)
    factura = Column(Integer)
    cliente = Column(String)
    articulo = Column(String)
    precio = Column(Float)
    cantidad = Column(Integer)
    total = Column(Float)
    fecha = Column(String)
    hora = Column(String)
    costo = Column(Float)
    metodo_pago = Column(String)
    sucursal = Column(String)
    descuento = Column(Integer)
    factura_separado = Column(Integer, ForeignKey("separados.factura"))
    banco = Column(String)


class Separado(Base):
    __tablename__ = "separados"
    id = Column(Integer, primary_key=True)
    factura = Column(Integer)
    cliente = Column(String)
    producto = Column(String)
    precio = Column(Float)
    cantidad = Column(Integer)
    total = Column(Float)
    abono = Column(Float)
    deuda_restante = Column(Numeric, default=0)
    estado_deuda = Column(String, default="pendiente")
    fecha_separado = Column(String)
    fecha_alerta = Column(String)
    alerta_mostrada = Column(Integer, default=0)
    sucursal = Column(String)
    metodo_pago = Column(String)
    banco = Column(String)


class AbonoSeparado(Base):
    __tablename__ = "abonos_separados"
    id = Column(Integer, primary_key=True)
    factura = Column(Integer)
    fecha = Column(String)
    monto = Column(Float)
    metodo_pago = Column(String)
    banco = Column(String)
    sucursal = Column(String)
