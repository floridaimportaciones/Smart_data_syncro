from sqlalchemy import String, cast, func, or_

from Smart_data_syncro.db.engine import SessionLocal
from Smart_data_syncro.db.models import Empresa

class EmpresaRepository:
    def obtener(self):
        session = SessionLocal()
        try:
            return session.query(Empresa).filter(Empresa.id == 1).first()
        finally:
            session.close()

    def guardar(self, nombre, direccion, telefono, email, website=None, nit=None, codigo_registro=None):
        session = SessionLocal()
        try:
            empresa = session.query(Empresa).filter(Empresa.id == 1).first()
            if empresa is None:
                empresa = Empresa(id=1, nombre=nombre, direccion=direccion, telefono=telefono, email=email,
                                   website=website, nit=nit, codigo_registro=codigo_registro)
                session.add(empresa)
            else:
                empresa.nombre = nombre
                empresa.direccion = direccion
                empresa.telefono = telefono
                empresa.email = email
                # Solo pisar estos campos opcionales si vino un valor nuevo; si no,
                # se preserva lo que ya habia (evita que un guardado parcial los borre).
                if website is not None:
                    empresa.website = website
                if nit is not None:
                    empresa.nit = nit
                if codigo_registro is not None:
                    empresa.codigo_registro = codigo_registro
            session.commit()
        finally:
            session.close()

    


