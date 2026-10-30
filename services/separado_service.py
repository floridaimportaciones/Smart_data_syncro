import datetime

from Smart_data_syncro.repositories.separado_repository import SeparadoRepository
from Smart_data_syncro.repositories.abono_separado_repository import AbonoSeparadoRepository
from Smart_data_syncro.repositories.venta_repository import VentaRepository
from Smart_data_syncro.services.articulo_service import ArticuloService


class SeparadoService:
    """Ventas a credito/fiado: registra el separado inicial, abonos adicionales,
    devuelve stock si se borra, y convierte en venta cuando queda totalmente pagado."""

    def __init__(self, repository=None, abono_repository=None, venta_repository=None, articulo_service=None):
        self.repository = repository or SeparadoRepository()
        self.abono_repository = abono_repository or AbonoSeparadoRepository()
        self.venta_repository = venta_repository or VentaRepository()
        self.articulo_service = articulo_service or ArticuloService()

    def siguiente_numero_factura(self):
        # Comparte numeracion con ventas: el maximo de ambas tablas + 1, nunca se repite.
        maximo = max(self.venta_repository.obtener_factura_maxima(), self.repository.obtener_factura_maxima())
        return maximo + 1

    def listar_pendientes(self, sucursal=None, factura=None, cliente=None):
        return self.repository.listar_pendientes(sucursal, factura, cliente)

    def listar_vencidos(self):
        hoy = datetime.datetime.now().strftime("%Y-%m-%d")
        return self.repository.listar_vencidos(hoy)

    def registrar_separado(self, items, abono, metodo_pago, banco, sucursal):
        """items: lista de tuplas (factura, cliente, producto, precio, cantidad, total, costo).
        Crea una fila por producto (todas comparten abono/deuda/estado), descuenta stock
        y devuelve el numero de factura usado."""
        factura = self.siguiente_numero_factura()
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
        fecha_alerta = (datetime.datetime.now() + datetime.timedelta(days=61)).strftime("%Y-%m-%d")
        total_venta = sum(float(str(item[5]).replace(",", "").replace(" ", "")) for item in items)
        deuda_restante = total_venta - abono
        estado_deuda = "pendiente" if deuda_restante > 0 else "pagado"

        for item in items:
            _, cliente, producto, precio, cantidad, total, costo = item
            total_num = float(str(total).replace(",", "").replace(" ", ""))
            self.repository.crear(
                factura, cliente, producto, precio, cantidad, total_num, abono, deuda_restante,
                estado_deuda, fecha_actual, fecha_alerta, sucursal, metodo_pago, banco,
            )
            try:
                self.articulo_service.descontar_stock_por_nombre(producto, int(cantidad))
            except ValueError as e:
                print(f"[WARN] No se pudo descontar stock de '{producto}': {e}")

        return factura

    def obtener_historial_abonos(self, factura):
        cabecera = self.repository.obtener_cabecera(factura)
        if cabecera is None:
            return None
        abonos_adicionales = self.abono_repository.listar_por_factura(factura)
        suma_adicionales = sum(float(a.monto or 0) for a in abonos_adicionales)
        abono_inicial = max(cabecera["abono"] - suma_adicionales, 0)
        return {
            "abono_inicial": abono_inicial,
            "metodo_inicial": cabecera["metodo_pago"],
            "banco_inicial": cabecera["banco"],
            "fecha_inicial": cabecera["fecha_separado"],
            "abonos_adicionales": [(a.fecha, a.monto, a.metodo_pago, a.banco) for a in abonos_adicionales],
            "deuda_restante": cabecera["deuda_restante"],
        }

    def registrar_abono_adicional(self, factura, monto, metodo_pago, banco, sucursal):
        cabecera = self.repository.obtener_cabecera(factura)
        if cabecera is None:
            raise ValueError(f"Separado {factura} no existe")
        deuda_actual = cabecera["deuda_restante"]
        if monto <= 0 or monto > deuda_actual:
            raise ValueError("El abono debe ser mayor que 0 y menor o igual a la deuda.")
        fecha = datetime.datetime.now().strftime("%Y-%m-%d")
        self.abono_repository.crear(factura, fecha, monto, metodo_pago, banco, sucursal)
        nueva_deuda = deuda_actual - monto
        nuevo_estado = "pagado" if nueva_deuda <= 0 else "pendiente"
        self.repository.actualizar_abono(factura, monto, nueva_deuda, nuevo_estado)
        return nueva_deuda

    def eliminar_separado(self, factura):
        items = self.repository.listar_items_por_factura(factura)
        for producto, cantidad, _, _ in items:
            try:
                self.articulo_service.restaurar_stock_por_nombre(producto, int(cantidad))
            except ValueError as e:
                print(f"[WARN] No se pudo devolver stock de '{producto}': {e}")
        self.repository.eliminar_por_factura(factura)
        self.abono_repository.eliminar_por_factura(factura)

    def obtener_resumen_factura(self, factura):
        """Para generar/ver la factura PDF de un separado: productos, total, abonado y deuda."""
        cabecera = self.repository.obtener_cabecera(factura)
        if cabecera is None:
            return None
        items = self.repository.listar_items_por_factura(factura)
        total_venta = sum(float(str(total).replace(",", "").replace(" ", "")) for _, _, _, total in items)
        return {
            "cliente": cabecera["cliente"],
            "metodo_pago": cabecera["metodo_pago"],
            "banco": cabecera["banco"],
            "productos": items,
            "total_venta": total_venta,
            "total_abonado": cabecera["abono"],
            "deuda_restante": cabecera["deuda_restante"],
        }

    def mover_a_venta(self, factura, sucursal_usuario):
        """Convierte un separado totalmente pagado en una venta normal."""
        filas = self.repository.listar_por_factura(factura)
        if not filas:
            raise ValueError("No se encontraron productos para el separado.")

        primera = filas[0]
        cliente = primera.cliente
        metodo_pago_inicial = primera.metodo_pago
        banco_inicial = primera.banco
        sucursal_original = primera.sucursal
        sucursal_final = sucursal_usuario if sucursal_usuario else sucursal_original
        if not sucursal_final or sucursal_final == "None":
            sucursal_final = sucursal_original if sucursal_original and sucursal_original != "None" else None

        nuevo_numero_factura = self.siguiente_numero_factura()

        metodos = set()
        bancos_transfer = set()
        efectivo_total = 0.0
        transferencia_total = 0.0
        if metodo_pago_inicial:
            m = metodo_pago_inicial.strip().lower()
            metodos.add(m)
            if m == 'transferencia' and banco_inicial:
                bancos_transfer.add(banco_inicial)

        abono_total_col = float(primera.abono or 0)
        abonos_adicionales = self.abono_repository.listar_por_factura(factura)
        suma_abonos_adic = 0.0
        for ab in abonos_adicionales:
            if ab.metodo_pago:
                m = ab.metodo_pago.strip().lower()
                if m:
                    metodos.add(m)
                if m == 'transferencia' and ab.banco:
                    bancos_transfer.add(ab.banco)
                monto_f = float(ab.monto or 0)
                if m == 'efectivo':
                    efectivo_total += monto_f
                elif m == 'transferencia':
                    transferencia_total += monto_f
                suma_abonos_adic += monto_f

        abono_inicial_real = max(abono_total_col - suma_abonos_adic, 0.0)
        if abono_inicial_real > 0 and metodo_pago_inicial:
            m = metodo_pago_inicial.strip().lower()
            if m == 'efectivo':
                efectivo_total += abono_inicial_real
            elif m == 'transferencia':
                transferencia_total += abono_inicial_real

        if metodos == {'transferencia'}:
            metodo_pago_final = 'transferencia'
        elif metodos == {'efectivo'}:
            metodo_pago_final = 'efectivo'
        elif 'efectivo' in metodos and 'transferencia' in metodos:
            metodo_pago_final = 'efectivo y transferencia'
        elif len(metodos) == 0:
            metodo_pago_final = metodo_pago_inicial or 'No especificado'
        else:
            metodo_pago_final = ' y '.join(sorted(metodos))
        banco_final = ' / '.join(sorted({b for b in bancos_transfer if b})) if 'transferencia' in metodos else banco_inicial

        # Registrar el abono inicial en el historial si aun no estaba ahi, antes de reasignar factura
        if abono_inicial_real > 0:
            fecha_ini = primera.fecha_separado or datetime.datetime.now().strftime("%Y-%m-%d")
            self.abono_repository.crear(factura, fecha_ini, abono_inicial_real, metodo_pago_inicial, banco_inicial, sucursal_final)

        self.abono_repository.reasignar_factura(factura, nuevo_numero_factura)

        fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d")
        hora_ahora = datetime.datetime.now().strftime("%H:%M:%S")
        for fila in filas:
            self.venta_repository.crear(
                nuevo_numero_factura, cliente, fila.producto, fila.precio, fila.cantidad, fila.total,
                0, fecha_hoy, hora_ahora, metodo_pago_final, sucursal_final, 0, banco_final,
            )

        self.repository.eliminar_por_factura(factura)

        return {
            "nuevo_numero_factura": nuevo_numero_factura,
            "cliente": cliente,
            "productos": [(f.producto, f.cantidad, f.precio, f.total) for f in filas],
            "total_venta": sum(float(f.total or 0) for f in filas),
            "metodo_pago_final": metodo_pago_final,
            "banco_final": banco_final,
            "efectivo_total": efectivo_total,
            "transferencia_total": transferencia_total,
        }

    def listar_reporte_pagados(self, sucursal=None):
        return self.repository.listar_pagados_para_reporte(sucursal)
