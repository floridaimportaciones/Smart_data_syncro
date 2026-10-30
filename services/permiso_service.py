from Smart_data_syncro.repositories.permiso_repository import PermisoRepository

MODULOS = ["Ventas", "Inventario", "Clientes", "Reportes", "Configuracion", "Usuarios"]


class PermisoService:
    """Permisos por rol, leidos de la tabla permisos (antes hardcodeados en permisos.py)."""

    def __init__(self, repository=None):
        self.repository = repository or PermisoRepository()

    def obtener_permisos_por_rol(self, rol):
        """Diccionario {modulo: True/False} con todos los modulos conocidos,
        segun lo que el rol tenga otorgado en la tabla permisos."""
        otorgados = set(self.repository.listar_modulos_por_rol(rol))
        return {modulo: modulo in otorgados for modulo in MODULOS}

    def tiene_acceso(self, rol, modulo):
        return modulo in self.repository.listar_modulos_por_rol(rol)

    def otorgar(self, rol, modulo):
        if modulo not in MODULOS:
            raise ValueError(f"Módulo desconocido: '{modulo}'")
        self.repository.otorgar(rol, modulo)

    def revocar(self, rol, modulo):
        self.repository.revocar(rol, modulo)

    def listar_todos(self):
        return self.repository.listar_todos()
