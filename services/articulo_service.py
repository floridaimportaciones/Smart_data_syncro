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

    @staticmethod
    def _a_float(val):
        """Convierte numeros en formato colombiano/europeo (20.000 = veinte mil,
        5.000,50 = cinco mil con cincuenta) o anglosajon (20,000 / 20.5) a float.
        Si hay coma y punto, el que aparece mas a la derecha es el decimal.
        Si hay uno solo y le siguen exactamente 3 digitos, se asume separador
        de miles (ambiguo, pero es el caso mas comun en precios/costos)."""
        if val is None or val == "":
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip().replace(' ', '')
        if not s:
            return None
        tiene_coma = ',' in s
        tiene_punto = '.' in s
        if tiene_coma and tiene_punto:
            if s.rfind(',') > s.rfind('.'):
                s = s.replace('.', '').replace(',', '.')
            else:
                s = s.replace(',', '')
        elif tiene_coma:
            partes = s.split(',')
            s = s.replace(',', '') if len(partes[-1]) == 3 else s.replace(',', '.')
        elif tiene_punto:
            partes = s.split('.')
            if len(partes[-1]) == 3:
                s = s.replace('.', '')
        try:
            return float(s)
        except Exception:
            return None

    @classmethod
    def _a_int(cls, val):
        f = cls._a_float(val)
        return int(round(f)) if f is not None else None

    def importar_filas(self, rows, sucursal_id_por_nombre, sucursal_id_default=None):
        """Crea o actualiza articulos a partir de filas leidas de Excel/CSV
        (ver excel_import.leer_filas_articulos). Si el codigo ya existe, actualiza
        ese articulo en vez de duplicarlo. Devuelve conteos para mostrarle al usuario."""
        insertados = actualizados = omitidos = errores = 0

        for r in rows:
            try:
                articulo = r.get("articulo")
                articulo = articulo.strip() if isinstance(articulo, str) else None
                codigo = r.get("codigo")
                codigo = str(codigo).strip() if codigo is not None and str(codigo).strip() != '' else None
                precio = self._a_float(r.get("precio"))
                costo = self._a_float(r.get("costo"))
                stock = self._a_int(r.get("stock"))
                stock_min = self._a_int(r.get("stock_minimo"))
                sucursal_nombre = r.get("sucursal")
                sucursal_nombre = sucursal_nombre.strip() if isinstance(sucursal_nombre, str) else None

                if not articulo and not codigo:
                    omitidos += 1
                    continue
                if not codigo:
                    # Sin codigo no hay forma de identificar el articulo para evitar duplicados
                    omitidos += 1
                    continue

                precio_i = precio if precio is not None else 0.0
                costo_i = costo if costo is not None else 0.0
                stock_i = stock if stock is not None else 0
                stock_min_i = stock_min if stock_min is not None else 0
                articulo_i = articulo if articulo else codigo
                sucursal_id_i = sucursal_id_por_nombre.get(sucursal_nombre) if sucursal_nombre else sucursal_id_default

                try:
                    existente = self.repository.obtener_por_codigo(codigo)
                    if existente:
                        self.repository.actualizar_por_id(existente.id, articulo_i, precio_i, costo_i, codigo,
                                                            stock_i, stock_min_i, sucursal_id_i)
                        actualizados += 1
                    else:
                        self.repository.crear(articulo_i, precio_i, costo_i, codigo, stock_i, stock_min_i, sucursal_id_i)
                        insertados += 1
                except Exception:
                    errores += 1
            except Exception:
                errores += 1

        return {"insertados": insertados, "actualizados": actualizados, "omitidos": omitidos, "errores": errores}
