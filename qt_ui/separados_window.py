"""Pantalla de Separados (ventas a credito/fiado) en PySide6 -- reemplaza
separados.py (Tkinter). Mismo patron que Ventas: carrito, catalogo de
clientes/productos con autocompletado por codigo, factura PDF.
"""
import datetime
import os

from PySide6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QComboBox, QDialog, QHBoxLayout,
    QHeaderView, QInputDialog, QLabel, QLineEdit, QMessageBox, QPushButton,
    QRadioButton, QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget, QCompleter,
)
from PySide6.QtGui import QColor

from Smart_data_syncro.pos_ticket import generar_ticket_pdf, imprimir_ticket
from Smart_data_syncro.qt_ui.theme import QSS
from Smart_data_syncro.services.articulo_service import ArticuloService
from Smart_data_syncro.services.cliente_service import ClienteService
from Smart_data_syncro.services.empresa_service import EmpresaService
from Smart_data_syncro.services.separado_service import SeparadoService
from Smart_data_syncro.services.usuario_service import UsuarioService
from Smart_data_syncro.utils import rutas

BANCOS = ["Bancolombia", "Daviplata"]


class SepararDialog(QDialog):
    """Dos pasos: monto a abonar, despues metodo de pago.
    self.resultado queda con (abono, metodo_pago, banco)."""

    def __init__(self, parent, total_venta):
        super().__init__(parent)
        self.total_venta = total_venta
        self.resultado = None
        self.setWindowTitle("Separar")
        self.setStyleSheet(QSS)
        self.setFixedWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        pag_abono = QWidget()
        v0 = QVBoxLayout(pag_abono)
        v0.addWidget(QLabel(f"Total a pagar: ${total_venta:,.0f}"))
        v0.addWidget(QLabel("Monto a abonar:"))
        self.entry_abono = QLineEdit()
        v0.addWidget(self.entry_abono)
        self.label_error_abono = QLabel("")
        self.label_error_abono.setObjectName("error")
        self.label_error_abono.setWordWrap(True)
        v0.addWidget(self.label_error_abono)
        btn_continuar = QPushButton("Continuar")
        btn_continuar.setObjectName("primario")
        btn_continuar.clicked.connect(self._continuar)
        v0.addWidget(btn_continuar)
        self.stack.addWidget(pag_abono)

        pag_metodo = QWidget()
        v1 = QVBoxLayout(pag_metodo)
        self.label_resumen = QLabel("")
        v1.addWidget(self.label_resumen)
        grupo = QButtonGroup(self)
        fila = QHBoxLayout()
        self.rb_efectivo = QRadioButton("Efectivo")
        self.rb_transferencia = QRadioButton("Transferencia")
        self.rb_efectivo.setChecked(True)
        for rb in (self.rb_efectivo, self.rb_transferencia):
            grupo.addButton(rb)
            fila.addWidget(rb)
        v1.addLayout(fila)
        self.combo_banco = QComboBox()
        self.combo_banco.addItems(BANCOS)
        self.combo_banco.setVisible(False)
        self.rb_transferencia.toggled.connect(self.combo_banco.setVisible)
        v1.addWidget(self.combo_banco)
        btn_confirmar = QPushButton("Confirmar pago")
        btn_confirmar.setObjectName("primario")
        btn_confirmar.clicked.connect(self._confirmar)
        v1.addWidget(btn_confirmar)
        self.stack.addWidget(pag_metodo)

    def _continuar(self):
        self.label_error_abono.setText("")
        try:
            abono = float(self.entry_abono.text().replace(",", "."))
        except ValueError:
            self.label_error_abono.setText("Ingresá un monto válido.")
            return
        if abono <= 0 or abono > self.total_venta:
            self.label_error_abono.setText("El abono debe ser mayor que 0 y menor o igual al total.")
            return
        self._abono = abono
        deuda = self.total_venta - abono
        self.label_resumen.setText(f"Abono: ${abono:,.0f}    Deuda restante: ${deuda:,.0f}")
        self.stack.setCurrentIndex(1)

    def _confirmar(self):
        metodo = "efectivo" if self.rb_efectivo.isChecked() else "transferencia"
        banco = self.combo_banco.currentText() if metodo == "transferencia" else None
        self.resultado = (self._abono, metodo, banco)
        self.accept()


class AbonarAdicionalDialog(QDialog):
    """Abono adicional sobre un separado ya existente (desde el reporte)."""

    def __init__(self, parent, deuda_restante):
        super().__init__(parent)
        self.resultado = None
        self.setWindowTitle("Abonar a separado existente")
        self.setStyleSheet(QSS)
        self.setFixedWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        layout.addWidget(QLabel(f"Deuda actual: ${deuda_restante:,.0f}"))
        layout.addWidget(QLabel("Monto a abonar:"))
        self.entry_abono = QLineEdit()
        layout.addWidget(self.entry_abono)

        grupo = QButtonGroup(self)
        fila = QHBoxLayout()
        self.rb_efectivo = QRadioButton("Efectivo")
        self.rb_transferencia = QRadioButton("Transferencia")
        self.rb_efectivo.setChecked(True)
        for rb in (self.rb_efectivo, self.rb_transferencia):
            grupo.addButton(rb)
            fila.addWidget(rb)
        layout.addLayout(fila)
        self.combo_banco = QComboBox()
        self.combo_banco.addItems(BANCOS)
        self.combo_banco.setVisible(False)
        self.rb_transferencia.toggled.connect(self.combo_banco.setVisible)
        layout.addWidget(self.combo_banco)

        self.label_error = QLabel("")
        self.label_error.setObjectName("error")
        self.label_error.setWordWrap(True)
        layout.addWidget(self.label_error)

        btn_confirmar = QPushButton("Confirmar abono")
        btn_confirmar.setObjectName("primario")
        btn_confirmar.clicked.connect(self._confirmar)
        layout.addWidget(btn_confirmar)

    def _confirmar(self):
        self.label_error.setText("")
        try:
            abono = float(self.entry_abono.text().replace(",", "."))
        except ValueError:
            self.label_error.setText("Ingresá un monto válido.")
            return
        metodo = "efectivo" if self.rb_efectivo.isChecked() else "transferencia"
        banco = self.combo_banco.currentText() if metodo == "transferencia" else None
        self.resultado = (abono, metodo, banco)
        self.accept()


class HistorialAbonosDialog(QDialog):
    def __init__(self, parent, separado_service, factura, cliente, producto, deuda_restante, sucursal, on_pagado_total):
        super().__init__(parent)
        self.separado_service = separado_service
        self.factura = factura
        self.sucursal = sucursal
        self.on_pagado_total = on_pagado_total  # callback(factura) cuando la deuda llega a 0

        self.setWindowTitle(f"Historial de abonos - Factura {factura}")
        self.setStyleSheet(QSS)
        self.resize(560, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        titulo = QLabel(f"Historial de abonos para {cliente} - {producto}")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        self.label_resumen_inicial = QLabel("")
        self.label_resumen_inicial.setWordWrap(True)
        layout.addWidget(self.label_resumen_inicial)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Monto", "Método", "Banco"])
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)

        self.label_deuda = QLabel(f"Deuda restante: ${deuda_restante:,.0f}")
        self.label_deuda.setObjectName("titulo")
        layout.addWidget(self.label_deuda)

        self.deuda_restante = deuda_restante
        self.btn_abonar = QPushButton("Abonar")
        self.btn_abonar.setObjectName("primario")
        self.btn_abonar.clicked.connect(self._abonar)
        layout.addWidget(self.btn_abonar)
        self.btn_abonar.setVisible(self.deuda_restante > 0)

        self._cargar()

    def _cargar(self):
        self.tabla.setRowCount(0)
        try:
            historial = self.separado_service.obtener_historial_abonos(self.factura)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar abonos: {e}")
            return
        if not historial:
            return

        abono_inicial = historial["abono_inicial"]
        if abono_inicial and abono_inicial > 0:
            resumen = f"Abono inicial: ${abono_inicial:,.0f} - Método: {historial['metodo_inicial'] or 'No especificado'}"
            if historial["banco_inicial"]:
                resumen += f" - Banco: {historial['banco_inicial']}"
            if historial["fecha_inicial"]:
                resumen += f" - Fecha: {historial['fecha_inicial']}"
            self.label_resumen_inicial.setText(resumen)
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            valores = [historial["fecha_inicial"] or "", abono_inicial, historial["metodo_inicial"] or "", historial["banco_inicial"] or ""]
            for c, v in enumerate(valores):
                self.tabla.setItem(fila, c, QTableWidgetItem(str(v)))

        for fecha, monto, metodo, banco in historial["abonos_adicionales"]:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            for c, v in enumerate((fecha, monto, metodo, banco)):
                self.tabla.setItem(fila, c, QTableWidgetItem(str(v) if v is not None else ""))

    def _abonar(self):
        dialogo = AbonarAdicionalDialog(self, self.deuda_restante)
        if dialogo.exec() != QDialog.Accepted or not dialogo.resultado:
            return
        abono, metodo, banco = dialogo.resultado
        try:
            nueva_deuda = self.separado_service.registrar_abono_adicional(self.factura, abono, metodo, banco, self.sucursal)
        except ValueError as e:
            QMessageBox.warning(self, "Datos inválidos", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al registrar abono: {e}")
            return

        self.deuda_restante = nueva_deuda
        self.label_deuda.setText(f"Deuda restante: ${nueva_deuda:,.0f}")
        self.btn_abonar.setVisible(nueva_deuda > 0)
        self._cargar()
        QMessageBox.information(self, "Éxito", "Abono registrado correctamente.")

        if nueva_deuda <= 0:
            self.on_pagado_total(self.factura)
            self.accept()


class SeparadosReporteWindow(QWidget):
    COLUMNAS = ["Factura", "Cliente", "Producto", "Total", "Abono", "Deuda", "Método", "Banco", "Estado", "Fecha", "Fecha Alerta"]

    def __init__(self, separado_service, sucursal, username, generar_factura_callback):
        super().__init__()
        self.separado_service = separado_service
        self.sucursal = sucursal
        self.username = username
        self.generar_factura_callback = generar_factura_callback

        self.setWindowTitle("Separados realizados")
        self.resize(1100, 600)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel("Separados realizados")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        filtros = QHBoxLayout()
        self.entry_factura = QLineEdit()
        self.entry_factura.setPlaceholderText("Factura")
        self.entry_factura.setFixedWidth(100)
        self.entry_cliente = QLineEdit()
        self.entry_cliente.setPlaceholderText("Cliente")
        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.setObjectName("primario")
        btn_filtrar.clicked.connect(self._filtrar)
        filtros.addWidget(QLabel("Factura:"))
        filtros.addWidget(self.entry_factura)
        filtros.addWidget(QLabel("Cliente:"))
        filtros.addWidget(self.entry_cliente)
        filtros.addWidget(btn_filtrar)
        filtros.addStretch()
        layout.addLayout(filtros)

        self.tabla = QTableWidget(0, len(self.COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(self.COLUMNAS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.tabla)

        botones = QHBoxLayout()
        btn_historial = QPushButton("Ver Historial / Abonar")
        btn_historial.clicked.connect(self._abrir_historial)
        btn_borrar = QPushButton("Borrar Separado")
        btn_borrar.setStyleSheet("background-color: #DC2626; color: white;")
        btn_borrar.clicked.connect(self._borrar)
        btn_ver_factura = QPushButton("Ver Factura")
        btn_ver_factura.clicked.connect(self._ver_factura)
        botones.addWidget(btn_historial)
        botones.addWidget(btn_borrar)
        botones.addStretch()
        botones.addWidget(btn_ver_factura)
        layout.addLayout(botones)

        self._avisar_vencidos()
        self._cargar()

    def _avisar_vencidos(self):
        try:
            vencidos = self.separado_service.listar_vencidos()
        except Exception:
            vencidos = []
        if vencidos:
            mensaje = "Separados vencidos (más de 60 días):\n\n"
            for v in vencidos:
                mensaje += f"Factura: {v.factura} | Cliente: {v.cliente} | Fecha alerta: {v.fecha_alerta}\n"
            QMessageBox.warning(self, "Separados vencidos", mensaje)

    def _cargar(self, factura_filtro=None, cliente_filtro=None):
        try:
            filas = self.separado_service.listar_pendientes(self.sucursal, factura_filtro, cliente_filtro)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar separados: {e}")
            return
        hoy = datetime.datetime.now().strftime("%Y-%m-%d")
        self.tabla.setRowCount(0)
        for s in filas:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            valores = [s.factura, s.cliente, s.producto, s.total, s.abono, s.deuda_restante,
                       s.metodo_pago, s.banco, s.estado_deuda, s.fecha_separado, s.fecha_alerta]
            vencido = bool(s.fecha_alerta) and s.fecha_alerta <= hoy
            for c, v in enumerate(valores):
                item = QTableWidgetItem(str(v) if v is not None else "")
                if vencido:
                    item.setBackground(QColor("#FFCCCC"))
                self.tabla.setItem(fila, c, item)

    def _filtrar(self):
        factura = self.entry_factura.text().strip() or None
        cliente = self.entry_cliente.text().strip() or None
        self._cargar(factura, cliente)

    def _fila_seleccionada(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Sin selección", "Seleccioná un separado primero.")
            return None
        return fila

    def _abrir_historial(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        factura = self.tabla.item(fila, 0).text()
        cliente = self.tabla.item(fila, 1).text()
        producto = self.tabla.item(fila, 2).text()
        deuda_restante = float(self.tabla.item(fila, 5).text())

        dialogo = HistorialAbonosDialog(self, self.separado_service, factura, cliente, producto, deuda_restante, self.sucursal, self._mover_a_venta)
        dialogo.exec()
        self._cargar()

    def _mover_a_venta(self, factura_separado):
        try:
            resultado = self.separado_service.mover_a_venta(factura_separado, self.sucursal)

            resumen_cierre = {
                "cliente": resultado["cliente"],
                "metodo_pago": resultado["metodo_pago_final"],
                "banco": resultado["banco_final"],
                "productos": resultado["productos"],
                "total_venta": resultado["total_venta"],
                "total_abonado": resultado["total_venta"],
                "deuda_restante": 0,
            }
            self.generar_factura_callback(factura_separado, resumen=resumen_cierre)

            from Smart_data_syncro.qt_ui.ventas_window import VentasWindow
            ventas_temp = VentasWindow(username=self.username)
            ventas_temp.generar_factura_pdf(
                resultado["total_venta"],
                resultado["cliente"],
                num_factura=resultado["nuevo_numero_factura"],
                banco=resultado["banco_final"],
                efectivo_pagado=resultado["efectivo_total"] if resultado["efectivo_total"] > 0 else None,
                transferencia_pagada=resultado["transferencia_total"] if resultado["transferencia_total"] > 0 else None,
            )
            QMessageBox.information(
                self, "Éxito",
                f"El separado con factura {factura_separado} se ha convertido en una venta "
                f"con factura {resultado['nuevo_numero_factura']}.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al convertir el separado a venta: {e}")

    def _borrar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        factura = self.tabla.item(fila, 0).text()
        cliente = self.tabla.item(fila, 1).text()
        producto = self.tabla.item(fila, 2).text()
        respuesta = QMessageBox.question(
            self, "Confirmar borrado",
            f"¿Está seguro de que desea borrar el separado?\n\n"
            f"Factura: {factura}\nCliente: {cliente}\nProducto: {producto}\n\n"
            f"Esta acción devolverá el stock y no se puede deshacer.",
        )
        if respuesta != QMessageBox.Yes:
            return
        try:
            self.separado_service.eliminar_separado(factura)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al borrar el separado: {e}")
            return
        QMessageBox.information(self, "Éxito", f"El separado con factura {factura} ha sido borrado correctamente.\nEl stock ha sido devuelto.")
        self._cargar()

    def _ver_factura(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        factura = self.tabla.item(fila, 0).text()
        nombre_archivo = rutas(f"facturas/factura_separado_{factura}.pdf")
        try:
            self.generar_factura_callback(factura, imprimir=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generando la factura PDF: {e}")
            return
        if os.path.exists(nombre_archivo):
            QMessageBox.information(self, "Éxito", f"La factura {factura} se ha generado correctamente\nRuta: {nombre_archivo}")
        else:
            QMessageBox.critical(self, "Error", f"No se encontró el archivo: {nombre_archivo}")


class SeparadosWindow(QWidget):
    def __init__(self, username=None):
        super().__init__()
        self.username = username
        self.articulo_service = ArticuloService()
        self.cliente_service = ClienteService()
        self.usuario_service = UsuarioService()
        self.separado_service = SeparadoService(articulo_service=self.articulo_service)
        self.empresa_service = EmpresaService()

        self.sucursal = self._obtener_sucursal_usuario()
        self.numero_factura = self.separado_service.siguiente_numero_factura()
        self.productos_seleccionados = []  # (factura, cliente, producto, precio, cantidad, total_cop, costo)

        self.setWindowTitle("Separados")
        self.resize(1000, 640)
        self.setStyleSheet(QSS)

        self._construir_ui()
        self._cargar_clientes()
        self._cargar_productos()

    # ---------- construccion de UI ----------

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        fila_titulo = QHBoxLayout()
        titulo = QLabel("Separados")
        titulo.setObjectName("titulo")
        fila_titulo.addWidget(titulo)
        fila_titulo.addStretch()
        self.label_factura = QLabel(f"Factura: {self.numero_factura}")
        fila_titulo.addWidget(self.label_factura)
        layout.addLayout(fila_titulo)

        form = QHBoxLayout()
        self.combo_cliente = QComboBox()
        self.combo_cliente.setEditable(True)
        self.combo_cliente.setInsertPolicy(QComboBox.NoInsert)
        self.combo_producto = QComboBox()
        self.combo_producto.setEditable(True)
        self.combo_producto.setInsertPolicy(QComboBox.NoInsert)
        self.combo_producto.lineEdit().returnPressed.connect(self._agregar_articulo)
        self.entry_cantidad = QLineEdit()
        self.entry_cantidad.setPlaceholderText("Cant.")
        self.entry_cantidad.setFixedWidth(70)
        self.label_stock = QLabel("Stock: -")
        btn_agregar = QPushButton("Agregar")
        btn_agregar.setObjectName("primario")
        btn_agregar.clicked.connect(self._agregar_articulo)

        form.addWidget(QLabel("Cliente:"))
        form.addWidget(self.combo_cliente, 2)
        form.addWidget(QLabel("Producto:"))
        form.addWidget(self.combo_producto, 2)
        form.addWidget(self.entry_cantidad)
        form.addWidget(self.label_stock)
        form.addWidget(btn_agregar)
        layout.addLayout(form)

        self.combo_producto.currentTextChanged.connect(self._actualizar_stock)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Producto", "Precio", "Cantidad", "Total"])
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.tabla)

        fila_inferior = QHBoxLayout()
        btn_editar = QPushButton("Editar cantidad")
        btn_editar.clicked.connect(self._editar_articulo)
        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.clicked.connect(self._eliminar_articulo)
        btn_limpiar = QPushButton("Limpiar lista")
        btn_limpiar.clicked.connect(self._limpiar_carrito)
        btn_reporte = QPushButton("Ver separados")
        btn_reporte.clicked.connect(self._ver_reporte)
        fila_inferior.addWidget(btn_editar)
        fila_inferior.addWidget(btn_eliminar)
        fila_inferior.addWidget(btn_limpiar)
        fila_inferior.addWidget(btn_reporte)
        fila_inferior.addStretch()

        self.label_total = QLabel("Precio a Pagar: $0")
        self.label_total.setObjectName("titulo")
        fila_inferior.addWidget(self.label_total)

        btn_separar = QPushButton("Separar")
        btn_separar.setObjectName("primario")
        btn_separar.clicked.connect(self._separar)
        fila_inferior.addWidget(btn_separar)

        layout.addLayout(fila_inferior)

    # ---------- carga de catalogos ----------

    def _obtener_sucursal_usuario(self):
        if not self.username:
            return None
        try:
            usuario = self.usuario_service.obtener_por_username(self.username)
            if usuario:
                if usuario.rol and usuario.rol.lower() in ["admin", "administrador"]:
                    return None
                return usuario.sucursal
            return None
        except Exception:
            return None

    def cargar_clientes(self):
        self._cargar_clientes()

    def _cargar_clientes(self):
        try:
            self.clientes = [c.nombre for c in self.cliente_service.listar()]
        except Exception:
            self.clientes = []
        self.combo_cliente.clear()
        self.combo_cliente.addItems(self.clientes)
        self.combo_cliente.setCurrentText("")
        self.combo_cliente.setCompleter(QCompleter(self.clientes, self))

    def cargar_productos(self):
        self._cargar_productos()

    def _cargar_productos(self):
        try:
            articulos = self.articulo_service.listar()
            if self.sucursal:
                articulos = [a for a in articulos if a.sucursal_obj and a.sucursal_obj.nombre == self.sucursal]
        except Exception:
            articulos = []
        self.products = [{"id": a.id, "nombre": a.articulo, "codigo": a.codigo} for a in articulos]
        textos = [self._texto_producto(p) for p in self.products]
        self.combo_producto.clear()
        self.combo_producto.addItems(textos)
        self.combo_producto.setCurrentText("")
        self.combo_producto.setCompleter(QCompleter(textos, self))

    def _texto_producto(self, p):
        codigo = (p.get("codigo") or "").strip()
        return f"{p['nombre']} [{codigo}]" if codigo else p["nombre"]

    def _extraer_codigo(self, valor):
        if not valor:
            return None
        val = str(valor).strip()
        if val.endswith("]") and "[" in val:
            return val[val.rfind("[") + 1:-1].strip()
        for p in self.products:
            codigo = (p.get("codigo") or "").strip()
            if codigo and val == codigo:
                return codigo
        coincidencias = [p for p in self.products if p["nombre"] == val]
        if len(coincidencias) == 1:
            return (coincidencias[0].get("codigo") or "").strip() or None
        return None

    # ---------- carrito ----------

    def _actualizar_stock(self, texto):
        codigo = self._extraer_codigo(texto)
        art = self.articulo_service.obtener_por_codigo(codigo) if codigo else None
        self.label_stock.setText(f"Stock: {art.stock}" if art else "Stock: -")

    def _agregar_articulo(self):
        self.numero_factura = self.separado_service.siguiente_numero_factura()
        self.label_factura.setText(f"Factura: {self.numero_factura}")

        cliente = self.combo_cliente.currentText().strip()
        producto_val = self.combo_producto.currentText().strip()
        cantidad_txt = self.entry_cantidad.text().strip()

        if not cliente:
            QMessageBox.critical(self, "Error", "Por favor, seleccioná un cliente.")
            return
        if not producto_val:
            QMessageBox.critical(self, "Error", "Por favor, seleccioná un producto.")
            return
        if not cantidad_txt.isdigit() or int(cantidad_txt) <= 0:
            QMessageBox.critical(self, "Error", "Por favor, ingresá una cantidad válida.")
            return
        cantidad = int(cantidad_txt)

        codigo = self._extraer_codigo(producto_val)
        art = None
        if codigo:
            art = self.articulo_service.obtener_por_codigo(codigo)
            if not art:
                QMessageBox.critical(self, "Error", "No se encontró un artículo con ese código.")
                return
        else:
            art = self.articulo_service.obtener_por_nombre(producto_val)
            if not art:
                coincidencias = self.articulo_service.listar(producto_val)
                art = coincidencias[0] if coincidencias else None
            if not art:
                QMessageBox.critical(self, "Error", "No se encontró el producto. Escribí el nombre exacto o usá el código.")
                return

        if cantidad > art.stock:
            QMessageBox.critical(self, "Error", f"No hay suficiente stock. Solo hay {art.stock} unidades disponibles.")
            return

        total = cantidad * art.precio
        total_cop = f"{total:,.0f}"

        self.tabla.insertRow(self.tabla.rowCount())
        fila = self.tabla.rowCount() - 1
        self.tabla.setItem(fila, 0, QTableWidgetItem(art.articulo))
        self.tabla.setItem(fila, 1, QTableWidgetItem(f"{art.precio:,.0f}"))
        self.tabla.setItem(fila, 2, QTableWidgetItem(str(cantidad)))
        self.tabla.setItem(fila, 3, QTableWidgetItem(total_cop))

        self.productos_seleccionados.append(
            (self.numero_factura, cliente, art.articulo, float(art.precio), cantidad, total_cop, float(art.costo))
        )
        self._calcular_total()
        self.entry_cantidad.clear()
        if codigo:
            self.combo_producto.setCurrentText("")

    def _calcular_total(self):
        total = 0.0
        for fila in range(self.tabla.rowCount()):
            try:
                total += float(self.tabla.item(fila, 3).text().replace(",", "").replace(" ", ""))
            except (ValueError, AttributeError):
                continue
        self.label_total.setText(f"Precio a Pagar: ${total:,.0f}")
        self.total_actual = total

    def _eliminar_articulo(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.critical(self, "Error", "No ha seleccionado ningún artículo.")
            return
        articulo = self.tabla.item(fila, 0).text()
        self.tabla.removeRow(fila)
        self.productos_seleccionados = [p for p in self.productos_seleccionados if p[2] != articulo]
        self._calcular_total()

    def _editar_articulo(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.critical(self, "Error", "No ha seleccionado ningún artículo.")
            return
        articulo = self.tabla.item(fila, 0).text()
        cantidad_actual = self.tabla.item(fila, 2).text()

        nueva_cantidad, ok = QInputDialog.getInt(self, "Editar artículo", "Nueva cantidad:", int(cantidad_actual), 1)
        if not ok:
            return

        art = self.articulo_service.obtener_por_nombre(articulo)
        if not art:
            QMessageBox.critical(self, "Error", "Producto no encontrado.")
            return
        if nueva_cantidad > art.stock:
            QMessageBox.critical(self, "Error", f"No hay suficiente stock. Solo hay {art.stock} unidades disponibles.")
            return

        total = art.precio * nueva_cantidad
        total_cop = f"{total:,.0f}"
        self.tabla.setItem(fila, 2, QTableWidgetItem(str(nueva_cantidad)))
        self.tabla.setItem(fila, 3, QTableWidgetItem(total_cop))

        cliente = self.combo_cliente.currentText().strip()
        for idx, p in enumerate(self.productos_seleccionados):
            if p[2] == articulo:
                self.productos_seleccionados[idx] = (
                    self.numero_factura, cliente, articulo, art.precio, nueva_cantidad, total_cop, art.costo,
                )
                break
        self._calcular_total()

    def _limpiar_carrito(self):
        self.tabla.setRowCount(0)
        self.productos_seleccionados.clear()
        self._calcular_total()

    # ---------- checkout ----------

    def _separar(self):
        if self.tabla.rowCount() == 0:
            QMessageBox.critical(self, "Error", "No hay productos seleccionados para realizar el pago.")
            return
        self._calcular_total()
        dialogo = SepararDialog(self, self.total_actual)
        if dialogo.exec() != QDialog.Accepted or not dialogo.resultado:
            return
        abono, metodo, banco = dialogo.resultado
        self._procesar_separado(abono, metodo, banco)

    def _procesar_separado(self, abono, metodo, banco):
        try:
            factura_real = self.separado_service.registrar_separado(
                self.productos_seleccionados, abono, metodo, banco, self.sucursal,
            )
            self.generar_factura_separado(factura_real)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al registrar el separado: {e}")
            return

        QMessageBox.information(self, "Separado registrado", "El separado se ha registrado correctamente.")
        self.numero_factura = self.separado_service.siguiente_numero_factura()
        self.label_factura.setText(f"Factura: {self.numero_factura}")
        self.productos_seleccionados = []
        self._limpiar_carrito()

    # ---------- factura PDF ----------

    def generar_factura_separado(self, num_factura, resumen=None, imprimir=False):
        """`resumen` ya calculado se usa cuando el separado ya se borro de la
        base (p. ej. al convertir a venta). `imprimir=True` abre el dialogo
        nativo de impresion (QPrintDialog) despues de guardar el PDF."""
        try:
            if resumen is None:
                resumen = self.separado_service.obtener_resumen_factura(num_factura)
            if resumen is None:
                print(f"No se encontró el separado {num_factura} para generar la factura")
                return
            cliente = resumen["cliente"]
            metodo_pago = resumen["metodo_pago"]
            banco = resumen["banco"]
            productos_factura = resumen["productos"]
            total_venta = resumen["total_venta"]
            total_abonado = resumen["total_abonado"]
            deuda_restante = resumen["deuda_restante"]

            nombre_archivo = rutas(f"facturas/factura_separado_{num_factura}.pdf")
            os.makedirs(os.path.dirname(nombre_archivo), exist_ok=True)

            info_empresa = self.empresa_service.obtener()
            if info_empresa:
                empresa = {
                    "nombre": info_empresa.nombre, "direccion": info_empresa.direccion,
                    "telefono": info_empresa.telefono, "email": info_empresa.email,
                    "nit": info_empresa.nit,
                }
            else:
                empresa = {
                    "nombre": "Empresa no configurada", "direccion": "Dirección no configurada",
                    "telefono": "Teléfono no configurado", "email": "Email no configurado",
                }

            encabezado = [
                f"Factura: {num_factura}",
                f"Fecha: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
                f"Cliente: {cliente}",
                f"Método de pago: {metodo_pago}{' - ' + banco if banco else ''}",
            ]

            items_ticket = []
            for prod, cant, precio, total in productos_factura:
                try:
                    precio_float = float(str(precio).replace(",", "").replace(" ", ""))
                except Exception:
                    precio_float = 0
                try:
                    total_float = float(str(total).replace(",", "").replace(" ", ""))
                except Exception:
                    total_float = 0
                items_ticket.append((prod, cant, precio_float, total_float))

            resumen_ticket = [
                (f"Total venta: ${total_venta:,.0f}", False),
                (f"Total abonado: ${total_abonado:,.0f}", False),
                (f"Deuda restante: ${deuda_restante:,.0f}", True),
            ]
            pie = ["Conserve este ticket, es su comprobante de separado."]

            generar_ticket_pdf(nombre_archivo, empresa, "FACTURA DE SEPARADO", encabezado, items_ticket, resumen_ticket, pie)

            if imprimir:
                imprimir_ticket(self, empresa, "FACTURA DE SEPARADO", encabezado, items_ticket, resumen_ticket, pie)
        except Exception as e:
            print(f"Error generando factura de separado: {e}")

    # ---------- reporte ----------

    def _ver_reporte(self):
        self._ventana_reporte = SeparadosReporteWindow(
            self.separado_service, self.sucursal, self.username, self.generar_factura_separado,
        )
        self._ventana_reporte.show()
