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

    def guardar(self, nombre, direccion, telefono, email, website=None, nit=None):
        session = SessionLocal()
        try:
            empresa = session.query(Empresa).filter(Empresa.id == 1).first()
            if empresa is None:
                empresa = Empresa(id=1, nombre=nombre, direccion=direccion,
                                   telefono=telefono, email=email, website=website, nit=nit)
                session.add(empresa)
            else:
                empresa.nombre = nombre
                empresa.direccion = direccion
                empresa.telefono = telefono
                empresa.email = email
                empresa.website = website
                empresa.nit = nit
            session.commit()
        finally:
            session.close()

    


