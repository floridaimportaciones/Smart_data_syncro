from Smart_data_syncro.repositories.cliente_repository import ClienteRepository


class ClienteService:
    """Reglas de negocio de clientes. La UI no conoce SQL ni el ORM, solo esto."""

    def __init__(self, repository=None):
        self.repository = repository or ClienteRepository()

    def listar(self, filtro=None):
        filtro = (filtro or "").strip()
        if filtro:
            return self.repository.buscar(filtro)
        return self.repository.listar_todos()

    def _validar(self, nombre, cedula, celular, direccion, correo):
        if not nombre or not cedula or not celular or not direccion or not correo:
            raise ValueError("Todos los campos son obligatorios.")

    def crear(self, nombre, cedula, celular, direccion, correo):
        self._validar(nombre, cedula, celular, direccion, correo)
        return self.repository.crear(nombre, cedula, celular, direccion, correo)

    def actualizar(self, id_cliente, nombre, cedula, celular, direccion, correo):
        self._validar(nombre, cedula, celular, direccion, correo)
        self.repository.actualizar(id_cliente, nombre, cedula, celular, direccion, correo)
