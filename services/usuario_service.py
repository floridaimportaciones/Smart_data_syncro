from Smart_data_syncro.repositories.usuario_repository import UsuarioRepository

class UsuarioService:
    def __init__(self,  repository=None):
        self.repository = repository or UsuarioRepository()

    def listar(self):
        return self.repository.listar_todos()

    def obtener_por_username(self, username):
        return self.repository.obtener_por_username(username)

    def _validar(self, username, password,rol):
        if not username or not password or not rol:
            raise ValueError("Todos los campos son obligatorios")

    def crear(self, username, password,rol,sucursal = None): 
        self._validar(username, password,rol)
        return self.repository.crear(username, password,rol,sucursal)

    def actualizar(self, id_usuario,username,password,rol,sucursal):
        self._validar(username, password,rol)
        self.repository.actualizar(id_usuario, username,password,rol,sucursal)
    
    def eliminar(self, id_usuario):
        self.repository.eliminar(id_usuario)


    