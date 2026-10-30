from sqlalchemy import func, or_

from Smart_data_syncro.db.engine import SessionLocal
from Smart_data_syncro.db.models import Separado, AbonoSeparado


class SeparadoRepository:
    """Unico lugar del sistema que habla SQL/ORM para la tabla separados (ventas a credito/fiado)."""

    def crear(self, factura, cliente, producto, precio, cantidad, total, abono, deuda_restante,
              estado_deuda, fecha_separado, fecha_alerta, sucursal, metodo_pago, banco):
        session = SessionLocal()
        try:
            separado = Separado(
                factura=factura, cliente=cliente, producto=producto, precio=precio,
                cantidad=cantidad, total=total, abono=abono, deuda_restante=deuda_restante,
                estado_deuda=estado_deuda, fecha_separado=fecha_separado, fecha_alerta=fecha_alerta,
                alerta_mostrada=0, sucursal=sucursal, metodo_pago=metodo_pago, banco=banco,
            )
            session.add(separado)
            session.commit()
            return separado.id
        finally:
            session.close()

    def listar_pendientes(self, sucursal=None, factura=None, cliente=None):
        session = SessionLocal()
        try:
            query = session.query(Separado).filter(Separado.estado_deuda != 'pagado')
            if sucursal:
                query = query.filter(or_(Separado.sucursal == sucursal, Separado.sucursal.is_(None)))
            if factura:
                query = query.filter(Separado.factura == factura)
            if cliente:
                query = query.filter(Separado.cliente.like(f"%{cliente}%"))
            return query.order_by(Separado.fecha_separado.desc()).all()
        finally:
            session.close()

    def listar_vencidos(self, hoy):
        session = SessionLocal()
        try:
            return (
                session.query(Separado)
                .filter(Separado.estado_deuda == 'pendiente', Separado.fecha_alerta <= hoy)
                .all()
            )
        finally:
            session.close()

    def obtener_factura_maxima(self):
        session = SessionLocal()
        try:
            return session.query(func.max(Separado.factura)).scalar() or 0
        finally:
            session.close()

    def listar_por_factura(self, factura):
        session = SessionLocal()
        try:
            return session.query(Separado).filter(Separado.factura == factura).all()
        finally:
            session.close()

    def listar_items_por_factura(self, factura):
        session = SessionLocal()
        try:
            query = session.query(
                Separado.producto, Separado.cantidad, Separado.precio, Separado.total,
            ).filter(Separado.factura == factura)
            return [tuple(fila) for fila in query.all()]
        finally:
            session.close()

    def obtener_cabecera(self, factura):
        """Datos comunes a todas las filas de una factura (abono, deuda, metodo de pago...)."""
        session = SessionLocal()
        try:
            fila = session.query(Separado).filter(Separado.factura == factura).first()
            if fila is None:
                return None
            return {
                "cliente": fila.cliente,
                "abono": fila.abono or 0,
                "deuda_restante": float(fila.deuda_restante or 0),
                "metodo_pago": fila.metodo_pago,
                "banco": fila.banco,
                "fecha_separado": fila.fecha_separado,
                "sucursal": fila.sucursal,
            }
        finally:
            session.close()

    def actualizar_abono(self, factura, monto_abonado, nueva_deuda_restante, nuevo_estado):
        """Suma el abono y fija la deuda/estado en TODAS las filas de la factura
        (cada fila es una linea de producto del mismo separado, comparten estos campos)."""
        session = SessionLocal()
        try:
            filas = session.query(Separado).filter(Separado.factura == factura).all()
            for fila in filas:
                fila.abono = (fila.abono or 0) + monto_abonado
                fila.deuda_restante = nueva_deuda_restante
                fila.estado_deuda = nuevo_estado
            session.commit()
        finally:
            session.close()

    def eliminar_por_factura(self, factura):
        session = SessionLocal()
        try:
            session.query(Separado).filter(Separado.factura == factura).delete()
            session.commit()
        finally:
            session.close()

    def listar_pagados_para_reporte(self, sucursal=None):
        session = SessionLocal()
        try:
            query = session.query(Separado).filter(Separado.estado_deuda == 'pagado')
            if sucursal:
                query = query.filter(Separado.sucursal == sucursal)
            separados = query.order_by(Separado.fecha_separado.desc()).all()

            facturas = [s.factura for s in separados]
            ultima_fecha_abono = {}
            if facturas:
                filas = (
                    session.query(AbonoSeparado.factura, func.max(AbonoSeparado.fecha))
                    .filter(AbonoSeparado.factura.in_(facturas))
                    .group_by(AbonoSeparado.factura)
                    .all()
                )
                ultima_fecha_abono = dict(filas)

            resultado = []
            for s in separados:
                fecha = ultima_fecha_abono.get(s.factura) or s.fecha_separado
                resultado.append((
                    s.factura, s.cliente, s.producto, s.precio, s.cantidad, s.total,
                    0, fecha, '', s.metodo_pago, s.sucursal, '',
                ))
            return resultado
        finally:
            session.close()
