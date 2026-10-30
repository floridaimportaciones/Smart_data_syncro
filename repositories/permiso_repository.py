from Smart_data_syncro.db.engine import SessionLocal
from Smart_data_syncro.db.models import Permiso


class PermisoRepository:
    """Unico lugar del sistema que habla SQL/ORM para la tabla permisos.
    Cada fila es un permiso otorgado: el rol tiene acceso al modulo."""

    def listar_modulos_por_rol(self, rol):
        session = SessionLocal()
        try:
            filas = session.query(Permiso.modulo).filter(Permiso.rol == rol).all()
            return [modulo for (modulo,) in filas]
        finally:
            session.close()

    def listar_todos(self):
        session = SessionLocal()
        try:
            return session.query(Permiso).order_by(Permiso.rol, Permiso.modulo).all()
        finally:
            session.close()

    def otorgar(self, rol, modulo):
        session = SessionLocal()
        try:
            existente = session.query(Permiso).filter(Permiso.rol == rol, Permiso.modulo == modulo).first()
            if existente:
                return existente.id
            permiso = Permiso(rol=rol, modulo=modulo)
            session.add(permiso)
            session.commit()
            return permiso.id
        finally:
            session.close()

    def revocar(self, rol, modulo):
        session = SessionLocal()
        try:
            session.query(Permiso).filter(Permiso.rol == rol, Permiso.modulo == modulo).delete()
            session.commit()
        finally:
            session.close()
