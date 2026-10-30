from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from Smart_data_syncro.db.engine import SessionLocal
from Smart_data_syncro.db.models import Articulo


class ArticuloRepository:
    """Unico lugar del sistema que habla SQL/ORM para la tabla articulos."""

    def listar_todos(self):
        session = SessionLocal()
        try:
            return session.query(Articulo).options(joinedload(Articulo.sucursal_obj)).all()
        finally:
            session.close()

    def buscar(self, filtro):
        patron = f"%{filtro}%"
        session = SessionLocal()
        try:
            return (
                session.query(Articulo)
                .options(joinedload(Articulo.sucursal_obj))
                .filter(or_(Articulo.articulo.like(patron), Articulo.codigo.like(patron)))
                .all()
            )
        finally:
            session.close()

    def obtener_por_codigo(self, codigo):
        session = SessionLocal()
        try:
            return (
                session.query(Articulo)
                .options(joinedload(Articulo.sucursal_obj))
                .filter(func.trim(Articulo.codigo) == codigo)
                .first()
            )
        finally:
            session.close()

    def obtener_por_nombre(self, articulo):
        session = SessionLocal()
        try:
            return (
                session.query(Articulo)
                .options(joinedload(Articulo.sucursal_obj))
                .filter(Articulo.articulo == articulo)
                .first()
            )
        finally:
            session.close()

    def crear(self, articulo, precio, costo, codigo, stock, stock_minimo, sucursal_id):
        session = SessionLocal()
        try:
            nuevo = Articulo(
                articulo=articulo, precio=precio, costo=costo, codigo=codigo,
                stock=stock, stock_minimo=stock_minimo, sucursal=sucursal_id,
            )
            session.add(nuevo)
            session.commit()
            return nuevo.id
        finally:
            session.close()

    def actualizar_por_id(self, id_articulo, articulo, precio, costo, codigo, stock, stock_minimo, sucursal_id):
        session = SessionLocal()
        try:
            art = session.query(Articulo).get(id_articulo)
            if art is None:
                raise ValueError(f"Articulo {id_articulo} no existe")
            art.articulo = articulo
            art.precio = precio
            art.costo = costo
            art.codigo = codigo
            art.stock = stock
            art.stock_minimo = stock_minimo
            art.sucursal = sucursal_id
            session.commit()
        finally:
            session.close()

    def descontar_stock(self, id_articulo, cantidad):
        session = SessionLocal()
        try:
            art = session.query(Articulo).get(id_articulo)
            if art is None:
                raise ValueError(f"Articulo {id_articulo} no existe")
            if art.stock < cantidad:
                raise ValueError(f"Stock insuficiente para '{art.articulo}': quedan {art.stock}, se requieren {cantidad}")
            art.stock -= cantidad
            session.commit()
        finally:
            session.close()

    def restaurar_stock(self, id_articulo, cantidad):
        session = SessionLocal()
        try:
            art = session.query(Articulo).get(id_articulo)
            if art is None:
                raise ValueError(f"Articulo {id_articulo} no existe")
            art.stock += cantidad
            session.commit()
        finally:
            session.close()

    def eliminar(self, id_articulo):
        session = SessionLocal()
        try:
            art = session.query(Articulo).get(id_articulo)
            if art is None:
                raise ValueError(f"Articulo {id_articulo} no existe")
            session.delete(art)
            session.commit()
        finally:
            session.close()
