from Smart_data_syncro.repositories.articulo_repository import ArticuloRepository


class ArticuloService:
    """Reglas de negocio de articulos. La UI no conoce SQL ni el ORM, solo esto."""

    def __init__(self, repository=None):
        self.repository = repository or ArticuloRepository()

    def listar(self, filtro=None):
        filtro = (filtro or "").strip()
        if filtro:
            return self.repository.buscar(filtro)
        return self.repository.listar_todos()

    def obtener_por_codigo(self, codigo):
        codigo = (codigo or "").strip()
        if not codigo:
            return None
        return self.repository.obtener_por_codigo(codigo)

    def obtener_por_nombre(self, nombre):
        return self.repository.obtener_por_nombre(nombre)

    def _validar(self, articulo, precio, costo, codigo, stock, stock_minimo, sucursal_id):
        if not articulo or not codigo or sucursal_id is None:
            raise ValueError("Todos los campos son obligatorios.")
        if precio is None or costo is None or stock is None or stock_minimo is None:
            raise ValueError("Precio, costo, stock y stock mínimo deben ser números.")

    def crear(self, articulo, precio, costo, codigo, stock, stock_minimo, sucursal_id):
        codigo = (codigo or "").strip()
        self._validar(articulo, precio, costo, codigo, stock, stock_minimo, sucursal_id)
        if self.repository.obtener_por_codigo(codigo):
            raise ValueError(f"Ya existe un artículo con el código '{codigo}'.")
        return self.repository.crear(articulo, precio, costo, codigo, stock, stock_minimo, sucursal_id)

    def actualizar(self, id_articulo, articulo, precio, costo, codigo, stock, stock_minimo, sucursal_id):
        codigo = (codigo or "").strip()
        self._validar(articulo, precio, costo, codigo, stock, stock_minimo, sucursal_id)
        existente = self.repository.obtener_por_codigo(codigo)
        if existente and existente.id != id_articulo:
            raise ValueError(f"Ya existe un artículo con el código '{codigo}'.")
        self.repository.actualizar_por_id(id_articulo, articulo, precio, costo, codigo, stock, stock_minimo, sucursal_id)

    def eliminar(self, id_articulo):
        self.repository.eliminar(id_articulo)

    def descontar_stock_por_codigo(self, codigo, cantidad):
        art = self.obtener_por_codigo(codigo)
        if not art:
            raise ValueError(f"No existe artículo con código '{codigo}'")
        self.repository.descontar_stock(art.id, cantidad)

    def descontar_stock_por_nombre(self, nombre, cantidad):
        art = self.repository.obtener_por_nombre(nombre)
        if not art:
            raise ValueError(f"No existe artículo '{nombre}'")
        self.repository.descontar_stock(art.id, cantidad)

    def restaurar_stock_por_nombre(self, nombre, cantidad):
        art = self.repository.obtener_por_nombre(nombre)
        if not art:
            raise ValueError(f"No existe artículo '{nombre}'")
        self.repository.restaurar_stock(art.id, cantidad)
