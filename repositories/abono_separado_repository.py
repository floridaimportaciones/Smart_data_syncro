from Smart_data_syncro.db.engine import SessionLocal
from Smart_data_syncro.db.models import AbonoSeparado


class AbonoSeparadoRepository:
    """Unico lugar del sistema que habla SQL/ORM para la tabla abonos_separados."""

    def crear(self, factura, fecha, monto, metodo_pago, banco, sucursal):
        session = SessionLocal()
        try:
            abono = AbonoSeparado(
                factura=factura, fecha=fecha, monto=monto,
                metodo_pago=metodo_pago, banco=banco, sucursal=sucursal,
            )
            session.add(abono)
            session.commit()
            return abono.id
        finally:
            session.close()

    def listar_por_factura(self, factura):
        session = SessionLocal()
        try:
            return session.query(AbonoSeparado).filter(AbonoSeparado.factura == factura).all()
        finally:
            session.close()

    def reasignar_factura(self, factura_vieja, factura_nueva):
        session = SessionLocal()
        try:
            session.query(AbonoSeparado).filter(AbonoSeparado.factura == factura_vieja).update(
                {AbonoSeparado.factura: factura_nueva}
            )
            session.commit()
        finally:
            session.close()

    def eliminar_por_factura(self, factura):
        session = SessionLocal()
        try:
            session.query(AbonoSeparado).filter(AbonoSeparado.factura == factura).delete()
            session.commit()
        finally:
            session.close()
