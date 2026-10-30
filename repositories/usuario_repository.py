from sqlalchemy import String, cast, func, or_

from Smart_data_syncro.db.engine import SessionLocal
from Smart_data_syncro.db.models import Usuario

class UsuarioRepository:

    def listar_todos(self): 
        session=SessionLocal()
        try: 
            return session.query(Usuario).all()
        finally:
            session.close()

    def obtener(self, id_usuario):
        session = SessionLocal()
        try:
            return session.query(Usuario).get(id_usuario)
        finally:
            session.close()

    def obtener_por_username(self, username):
        session = SessionLocal()
        try:
            return session.query(Usuario).filter(Usuario.username == username).first()
        finally:
            session.close()

    def crear(self, username, password,rol, sucursal=None ):
        session=SessionLocal()
        try:
            usuario = Usuario(username=username,  password=password,  rol = rol, sucursal=sucursal)
            session.add(usuario)
            session.commit()
            return usuario.id
        finally: 
            session.close()

    def actualizar(self, id_usuario,username,password,rol,sucursal=None):
        session=SessionLocal()
        try:
            usuario =session.query(Usuario).get(id_usuario)
            if usuario is None:
                raise ValueError(f"Usuario {id_usuario} no existe")
            usuario.username = username
            usuario.password= password
            usuario.rol= rol
            usuario.sucursal = sucursal
            session.commit()
        finally:
            session.close()

    def eliminar(self,  id_usuario):
        session =SessionLocal()
        try:
            usuario = session.query(Usuario).get(id_usuario)
            if usuario is None:
                raise ValueError(f"Usuario {id_usuario} no existe")
            session.delete(usuario)
            session.commit()
        finally: 
            session.close()