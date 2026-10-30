from sqlalchemy import String, cast, func , or_

from Smart_data_syncro.db.engine import SessionLocal
from Smart_data_syncro.db.models import Sucursal


class SucursalRepository:

    def listar_todas_las_sucursales(self):
        session =SessionLocal()
        try:
            return session.query(Sucursal).all()
        finally:
            session.close()

    def buscar(self, filtro):
        patron = f"%{filtro.lower()}%"
        session = SessionLocal()
        try:
            return session.query(Sucursal).filter(func.lower(cast(Sucursal.nombre, String)).like(patron)).all()
        finally:
            session.close()


    def crear(self, nombre):
        session = SessionLocal()
        try:
            sucursal = Sucursal(nombre = nombre )
            session.add(sucursal)
            session.commit()
            return sucursal.id
        finally:
            session.close()


    def actualizar(self, id_sucursal, nombre):
        session = SessionLocal()
        try:
            sucursal = session.query(Sucursal).get(id_sucursal)
            if sucursal is None:
                raise ValueError(f"La sucursal {id_sucursal} no existe")
            sucursal.nombre = nombre
            session.commit()
        finally:
            session.close()


    def eliminar(self, id_sucursal):
        session = SessionLocal()
        try:
            sucursal = session.query(Sucursal).get(id_sucursal)
            if sucursal is None:
                raise ValueError(f"La sucursal {id_sucursal} no existe")
            session.delete(sucursal)
            session.commit()
        finally:
            session.close()