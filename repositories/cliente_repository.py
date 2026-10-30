from sqlalchemy import String, cast, func, or_

from Smart_data_syncro.db.engine import SessionLocal
from Smart_data_syncro.db.models import Cliente


class ClienteRepository:
    """Unico lugar del sistema que habla SQL/ORM para la tabla clientes."""

    def listar_todos(self):
        session = SessionLocal()
        try:
            return session.query(Cliente).all()
        finally:
            session.close()

    def buscar(self, filtro):
        patron = f"%{filtro.lower()}%"
        session = SessionLocal()
        try:
            campos = [Cliente.nombre, Cliente.cedula, Cliente.celular, Cliente.direccion, Cliente.correo]
            condiciones = [func.lower(cast(campo, String)).like(patron) for campo in campos]
            return session.query(Cliente).filter(or_(*condiciones)).all()
        finally:
            session.close()

    def obtener(self, id_cliente):
        session = SessionLocal()
        try:
            return session.query(Cliente).get(id_cliente)
        finally:
            session.close()

    def crear(self, nombre, cedula, celular, direccion, correo):
        session = SessionLocal()
        try:
            cliente = Cliente(nombre=nombre, cedula=cedula, celular=celular, direccion=direccion, correo=correo)
            session.add(cliente)
            session.commit()
            return cliente.id
        finally:
            session.close()

    def actualizar(self, id_cliente, nombre, cedula, celular, direccion, correo):
        session = SessionLocal()
        try:
            cliente = session.query(Cliente).get(id_cliente)
            if cliente is None:
                raise ValueError(f"Cliente {id_cliente} no existe")
            cliente.nombre = nombre
            cliente.cedula = cedula
            cliente.celular = celular
            cliente.direccion = direccion
            cliente.correo = correo
            session.commit()
        finally:
            session.close()
