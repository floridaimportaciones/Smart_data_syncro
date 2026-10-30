from Smart_data_syncro.repositories.empresa_repository import EmpresaRepository

class EmpresaService:
    def __init__(self, repository= None):
        self.repository = repository or EmpresaRepository()

    def obtener(self):
        return self.repository.obtener()
    
    def _validar(self, nombre, direccion, telefono, email):
        if not nombre or not direccion or not telefono or not email:
            raise  ValueError("Todos los campos tienen que estar llenos")

    def guardar(self, nombre, direccion, telefono, email, website=None, nit=None):
        self._validar(nombre,direccion,telefono, email)
        self.repository.guardar(nombre,direccion,telefono,email , website , nit )

    
