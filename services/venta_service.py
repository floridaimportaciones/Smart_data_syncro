from Smart_data_syncro.repositories.venta_repository import VentaRepository
from Smart_data_syncro.repositories.abono_separado_repository import AbonoSeparadoRepository
from Smart_data_syncro.repositories.separado_repository import SeparadoRepository
from Smart_data_syncro.services.articulo_service import ArticuloService


class VentaService:
    """Registra ventas: crea las filas en ventas y descuenta stock del articulo vendido."""

    def __init__(self, repository=None, abono_repository=None, separado_repository=None, articulo_service=None):
        self.repository = repository or VentaRepository()
        self.abono_repository = abono_repository or AbonoSeparadoRepository()
        self.separado_repository = separado_repository or SeparadoRepository()
        self.articulo_service = articulo_service or ArticuloService()

    def siguiente_numero_factura(self):
        return self.repository.obtener_numero_factura_siguiente()

    def registrar_venta(self, items, fecha, hora, metodo_pago, sucursal, banco, descuento):
        """items: lista de tuplas (factura, cliente, articulo, precio, cantidad, total, costo[, codigo]).
        Crea una fila en ventas por cada item y descuenta stock. El descuento de la
        venta completa se registra solo en la primera fila (por posicion, no por valor)."""
        for idx, item in enumerate(items):
            if len(item) == 7:
                factura, cliente, articulo, precio, cantidad, total, costo = item
                codigo = None
            else:
                factura, cliente, articulo, precio, cantidad, total, costo, codigo = item[:8]

            total_normalizado = str(total).replace(" ", "").replace(",", "")
            descuento_item = descuento if idx == 0 else 0

            self.repository.crear(
                factura, cliente, articulo, precio, cantidad, total_normalizado,
                costo * int(cantidad), fecha, hora, metodo_pago, sucursal, descuento_item, banco,
            )

            try:
                if codigo:
                    self.articulo_service.descontar_stock_por_codigo(codigo, int(cantidad))
                else:
                    self.articulo_service.descontar_stock_por_nombre(articulo, int(cantidad))
            except ValueError as e:
                print(f"[WARN] No se pudo descontar stock de '{articulo}': {e}")

    def registrar_abono(self, factura, fecha, monto, metodo_pago, banco, sucursal):
        self.abono_repository.crear(factura, fecha, monto, metodo_pago, banco, sucursal)

    def listar_reporte(self, sucursal=None):
        """Ventas normales + separados (fiados) ya pagados, fusionados para el reporte."""
        ventas = self.repository.listar_para_reporte(sucursal)
        facturas_ventas = {v[0] for v in ventas}
        separados_pagados = self.separado_repository.listar_pagados_para_reporte(sucursal)
        separados_filtrados = [s for s in separados_pagados if s[0] not in facturas_ventas]
        return ventas + separados_filtrados

    def listar_para_pdf(self, factura):
        return self.repository.listar_para_pdf(factura)

    def obtener_metodo_pago_banco(self, factura):
        return self.repository.obtener_metodo_pago_banco(factura)

    def obtener_desglose_pagos(self, factura):
        """Suma de abonos (efectivo/transferencia) registrados para una factura."""
        efectivo = 0.0
        transferencia = 0.0
        for abono in self.abono_repository.listar_por_factura(factura):
            metodo = (abono.metodo_pago or '').strip().lower()
            monto = float(abono.monto or 0)
            if metodo == 'efectivo':
                efectivo += monto
            elif metodo == 'transferencia':
                transferencia += monto
        return efectivo, transferencia

    def obtener_detalle_factura(self, factura, cliente):
        """Para regenerar/ver una factura: descuento, items formateados, total y desglose de pago."""
        descuento = self.repository.obtener_descuento_por_factura(factura) or 0
        items = self.repository.listar_items_por_factura(factura)
        productos_formato = []
        total_venta = 0.0
        for articulo, precio, cantidad, total, costo, metodo_pago in items:
            total_num = float(str(total).replace(",", "").replace(" ", ""))
            productos_formato.append((factura, cliente, articulo, precio, cantidad, "{:,.0f}".format(total_num), costo))
            total_venta += total_num
        efectivo, transferencia = self.obtener_desglose_pagos(factura)
        return {
            "descuento": float(descuento),
            "productos": productos_formato,
            "total": total_venta,
            "efectivo": efectivo if efectivo else None,
            "transferencia": transferencia if transferencia else None,
        }

    def totales_por_rango(self, fecha_ini, fecha_fin):
        return self.repository.totales_por_rango(fecha_ini, fecha_fin)

    def ganancias_por_rango(self, fecha_ini, fecha_fin):
        return self.repository.ganancias_por_rango(fecha_ini, fecha_fin)

    def ventas_por_mes(self, anio):
        return self.repository.ventas_por_mes(anio)

    def ventas_y_ganancias_por_mes(self, anio):
        return self.repository.ventas_y_ganancias_por_mes(anio)

    def ventas_agrupadas_por_mes_todas(self):
        return self.repository.ventas_agrupadas_por_mes_todas()
