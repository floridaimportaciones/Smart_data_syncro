from sqlalchemy import func

from Smart_data_syncro.db.engine import SessionLocal
from Smart_data_syncro.db.models import Venta


class VentaRepository:
    """Unico lugar del sistema que habla SQL/ORM para la tabla ventas."""

    def crear(self, factura, cliente, articulo, precio, cantidad, total, costo, fecha, hora,
              metodo_pago, sucursal, descuento, banco):
        session = SessionLocal()
        try:
            venta = Venta(
                factura=factura, cliente=cliente, articulo=articulo, precio=precio,
                cantidad=cantidad, total=total, costo=costo, fecha=fecha, hora=hora,
                metodo_pago=metodo_pago, sucursal=sucursal, descuento=descuento, banco=banco,
            )
            session.add(venta)
            session.commit()
            return venta.id
        finally:
            session.close()

    def obtener_numero_factura_siguiente(self):
        session = SessionLocal()
        try:
            maximo = session.query(func.max(Venta.factura)).scalar()
            return (maximo or 0) + 1
        finally:
            session.close()

    def obtener_factura_maxima(self):
        session = SessionLocal()
        try:
            return session.query(func.max(Venta.factura)).scalar() or 0
        finally:
            session.close()

    def listar_para_reporte(self, sucursal=None):
        session = SessionLocal()
        try:
            query = session.query(
                Venta.factura, Venta.cliente, Venta.articulo, Venta.precio, Venta.cantidad,
                Venta.total, Venta.descuento, Venta.fecha, Venta.hora, Venta.metodo_pago,
                Venta.sucursal, Venta.banco,
            )
            if sucursal:
                query = query.filter(Venta.sucursal == sucursal)
            query = query.order_by(Venta.fecha.desc(), Venta.hora.desc())
            return [tuple(fila) for fila in query.all()]
        finally:
            session.close()

    def obtener_descuento_por_factura(self, factura):
        session = SessionLocal()
        try:
            return (
                session.query(Venta.descuento)
                .filter(Venta.factura == factura, Venta.descuento > 0)
                .limit(1)
                .scalar()
            )
        finally:
            session.close()

    def listar_items_por_factura(self, factura):
        session = SessionLocal()
        try:
            query = session.query(
                Venta.articulo, Venta.precio, Venta.cantidad, Venta.total, Venta.costo, Venta.metodo_pago,
            ).filter(Venta.factura == factura)
            return [tuple(fila) for fila in query.all()]
        finally:
            session.close()

    def listar_para_pdf(self, factura):
        session = SessionLocal()
        try:
            query = session.query(
                Venta.articulo, Venta.cantidad, Venta.precio, Venta.total,
            ).filter(Venta.factura == factura)
            return [tuple(fila) for fila in query.all()]
        finally:
            session.close()

    def obtener_metodo_pago_banco(self, factura):
        session = SessionLocal()
        try:
            return (
                session.query(Venta.metodo_pago, Venta.banco)
                .filter(Venta.factura == factura)
                .distinct()
                .first()
            )
        finally:
            session.close()

    def totales_por_rango(self, fecha_ini, fecha_fin):
        session = SessionLocal()
        try:
            return session.query(
                func.sum(Venta.cantidad), func.sum(Venta.total),
            ).filter(Venta.fecha.between(fecha_ini, fecha_fin)).one()
        finally:
            session.close()

    def ganancias_por_rango(self, fecha_ini, fecha_fin):
        session = SessionLocal()
        try:
            # Venta.costo ya guarda el costo total de la linea (costo_unitario * cantidad,
            # ver VentaService.registrar_venta), no hay que volver a multiplicar por cantidad.
            total, costo_total = session.query(
                func.sum(Venta.total), func.sum(Venta.costo),
            ).filter(Venta.fecha.between(fecha_ini, fecha_fin)).one()
            if total is None:
                return None
            return total - (costo_total or 0)
        finally:
            session.close()

    def ventas_por_mes(self, anio):
        session = SessionLocal()
        try:
            mes = func.strftime('%m', Venta.fecha)
            query = (
                session.query(mes, func.sum(Venta.total))
                .filter(func.strftime('%Y', Venta.fecha) == str(anio))
                .group_by(mes)
                .order_by(mes)
            )
            return query.all()
        finally:
            session.close()

    def ventas_y_ganancias_por_mes(self, anio):
        session = SessionLocal()
        try:
            # Venta.costo ya guarda el costo total de la linea, no se multiplica por cantidad.
            mes = func.strftime('%m', Venta.fecha)
            query = (
                session.query(
                    mes,
                    func.sum(Venta.costo),
                    func.sum(Venta.total),
                    func.sum(Venta.total) - func.sum(Venta.costo),
                )
                .filter(func.strftime('%Y', Venta.fecha) == str(anio))
                .group_by(mes)
                .order_by(mes)
            )
            return query.all()
        finally:
            session.close()

    def ventas_agrupadas_por_mes_todas(self):
        session = SessionLocal()
        try:
            mes = func.strftime('%Y-%m', Venta.fecha)
            query = session.query(mes, func.sum(Venta.total)).group_by(mes).order_by(mes)
            return [tuple(fila) for fila in query.all()]
        finally:
            session.close()
