from Smart_data_syncro.repositories.sucursal_repository import SucursalRepository

class SucursalService:
    def __init__(self, repository = None):
        self.repository = repository or SucursalRepository()

    def listar(self, filtro= None ):
        filtro = (filtro or "").strip()
        if filtro:
            return self.repository.buscar(filtro)
        return self.repository.listar_todas_las_sucursales()

    def _validar (self, nombre):
        if not nombre :
            raise ValueError("Tiene que ingresar un nombre.")

    def crear (self, nombre):
        self._validar(nombre)
        return self.repository.crear(nombre)

    def actualizar(self,id_sucursal, nombre):
        self._validar(nombre)
        self.repository.actualizar(id_sucursal, nombre)

    def eliminar (self, id_sucursal):
        self.repository.eliminar(id_sucursal)