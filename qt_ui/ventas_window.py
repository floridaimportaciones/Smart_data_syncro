"""Pantalla de Ventas en PySide6 -- reemplaza ventas.py (Tkinter).

Se abre desde container.py como ventana aparte, mismo patron que los demas
modulos ya migrados. Necesita el username logueado para saber la sucursal.
"""
import datetime
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QMessageBox, QAbstractItemView, QRadioButton, QButtonGroup,
    QStackedWidget, QCompleter,
)

from Smart_data_syncro.services.articulo_service import ArticuloService
from Smart_data_syncro.services.cliente_service import ClienteService
from Smart_data_syncro.services.usuario_service import UsuarioService
from Smart_data_syncro.services.venta_service import VentaService
from Smart_data_syncro.services.empresa_service import EmpresaService
from Smart_data_syncro.utils import rutas
from Smart_data_syncro.pos_ticket import generar_ticket_pdf, imprimir_ticket
from Smart_data_syncro.qt_ui.theme import QSS

BANCOS = ["Bancolombia", "Daviplata"]


class PagoDialog(QDialog):
    """Metodo de pago para cerrar la venta. self.resultado queda con
    (metodo_pago, banco, cantidad_pagada, efectivo_monto, transferencia_monto)."""

    def __init__(self, parent, total_venta):
        super().__init__(parent)
        self.total_venta = total_venta
        self.resultado = None
        self.setWindowTitle("Realizar pago")
        self.setStyleSheet(QSS)
        self.setFixedWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        layout.addWidget(QLabel(f"Total a pagar: ${total_venta:,.0f}"))

        self.grupo = QButtonGroup(self)
        fila_radios = QHBoxLayout()
        self.rb_efectivo = QRadioButton("Efectivo")
        self.rb_transferencia = QRadioButton("Transferencia")
        self.rb_tarjeta = QRadioButton("Tarjeta")
        self.rb_parcial = QRadioButton("Pago parcial")
        self.rb_efectivo.setChecked(True)
        for rb in (self.rb_efectivo, self.rb_transferencia, self.rb_tarjeta, self.rb_parcial):
            self.grupo.addButton(rb)
            fila_radios.addWidget(rb)
        layout.addLayout(fila_radios)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Efectivo
        pag_efectivo = QWidget()
        f1 = QFormLayout(pag_efectivo)
        self.entry_pagado = QLineEdit()
        f1.addRow("Monto pagado:", self.entry_pagado)
        self.stack.addWidget(pag_efectivo)

        # Transferencia
        pag_transferencia = QWidget()
        f2 = QFormLayout(pag_transferencia)
        self.combo_banco_transferencia = QComboBox()
        self.combo_banco_transferencia.addItems(BANCOS)
        f2.addRow("Banco:", self.combo_banco_transferencia)
        self.stack.addWidget(pag_transferencia)

        # Tarjeta
        pag_tarjeta = QWidget()
        QVBoxLayout(pag_tarjeta).addWidget(QLabel("Pago con tarjeta."))
        self.stack.addWidget(pag_tarjeta)

        # Pago parcial
        pag_parcial = QWidget()
        f4 = QFormLayout(pag_parcial)
        self.entry_efectivo_parcial = QLineEdit()
        self.entry_transferencia_parcial = QLineEdit()
        self.combo_banco_parcial = QComboBox()
        self.combo_banco_parcial.addItems(BANCOS)
        f4.addRow("Efectivo:", self.entry_efectivo_parcial)
        f4.addRow("Transferencia:", self.entry_transferencia_parcial)
        f4.addRow("Banco (si hay transferencia):", self.combo_banco_parcial)
        self.stack.addWidget(pag_parcial)

        self.rb_efectivo.toggled.connect(lambda c: c and self.stack.setCurrentIndex(0))
        self.rb_transferencia.toggled.connect(lambda c: c and self.stack.setCurrentIndex(1))
        self.rb_tarjeta.toggled.connect(lambda c: c and self.stack.setCurrentIndex(2))
        self.rb_parcial.toggled.connect(lambda c: c and self.stack.setCurrentIndex(3))

        self.label_error = QLabel("")
        self.label_error.setObjectName("error")
        self.label_error.setWordWrap(True)
        layout.addWidget(self.label_error)

        btn_confirmar = QPushButton("Confirmar pago")
        btn_confirmar.setObjectName("primario")
        btn_confirmar.clicked.connect(self._confirmar)
        layout.addWidget(btn_confirmar)

    def _confirmar(self):
        self.label_error.setText("")
        if self.rb_efectivo.isChecked():
            try:
                pagado = float(self.entry_pagado.text().replace(",", "."))
            except ValueError:
                self.label_error.setText("Ingresá un monto válido.")
                return
            if pagado < self.total_venta:
                self.label_error.setText("El monto pagado es menor al total.")
                return
            self.resultado = ("efectivo", None, pagado, None, None)
        elif self.rb_transferencia.isChecked():
            self.resultado = ("transferencia", self.combo_banco_transferencia.currentText(), self.total_venta, None, None)
        elif self.rb_tarjeta.isChecked():
            self.resultado = ("tarjeta", None, self.total_venta, None, None)
        else:
            try:
                ef = float(self.entry_efectivo_parcial.text().replace(",", ".") or 0)
                tr = float(self.entry_transferencia_parcial.text().replace(",", ".") or 0)
            except ValueError:
                self.label_error.setText("Ingresá montos numéricos válidos.")
                return
            if tr > self.total_venta:
                self.label_error.setText("La transferencia no puede ser mayor que el total.")
                return
            requerido_ef = max(self.total_venta - tr, 0)
            if ef < requerido_ef:
                self.label_error.setText(f"Efectivo insuficiente. Faltan ${requerido_ef - ef:,.0f}.")
                return
            banco = self.combo_banco_parcial.currentText() if tr > 0 else None
            self.resultado = ("pago parcial", banco, ef + tr, ef, tr)
        self.accept()


class VentasWindow(QWidget):
    def __init__(self, username=None):
        super().__init__()
        self.username = username
        self.articulo_service = ArticuloService()
        self.cliente_service = ClienteService()
        self.usuario_service = UsuarioService()
        self.venta_service = VentaService(articulo_service=self.articulo_service)
        self.empresa_service = EmpresaService()

        self.sucursal = self._obtener_sucursal_usuario()
        self.numero_factura = self.venta_service.siguiente_numero_factura()
        self.productos_seleccionados = []  # (factura, cliente, producto, precio, cantidad, total_cop, costo, codigo)

        self.setWindowTitle("Ventas")
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
        titulo = QLabel("Ventas")
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
        btn_limpiar = QPushButton("Limpiar carrito")
        btn_limpiar.clicked.connect(self._limpiar_carrito)
        btn_reporte = QPushButton("Ver ventas realizadas")
        btn_reporte.clicked.connect(self._ver_reporte)
        fila_inferior.addWidget(btn_editar)
        fila_inferior.addWidget(btn_eliminar)
        fila_inferior.addWidget(btn_limpiar)
        fila_inferior.addWidget(btn_reporte)
        fila_inferior.addStretch()

        fila_inferior.addWidget(QLabel("Descuento:"))
        self.entry_descuento = QLineEdit()
        self.entry_descuento.setFixedWidth(90)
        self.entry_descuento.setText("0")
        self.entry_descuento.textChanged.connect(self._calcular_total)
        fila_inferior.addWidget(self.entry_descuento)

        self.label_total = QLabel("Precio a pagar: $0")
        self.label_total.setObjectName("titulo")
        fila_inferior.addWidget(self.label_total)

        btn_cobrar = QPushButton("Cobrar")
        btn_cobrar.setObjectName("primario")
        btn_cobrar.clicked.connect(self._cobrar)
        fila_inferior.addWidget(btn_cobrar)

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

        codigo_final = (art.codigo or "").strip() or None
        total = cantidad * art.precio
        total_cop = f"{total:,.0f}"

        self.tabla.insertRow(self.tabla.rowCount())
        fila = self.tabla.rowCount() - 1
        self.tabla.setItem(fila, 0, QTableWidgetItem(art.articulo))
        self.tabla.setItem(fila, 1, QTableWidgetItem(f"{art.precio:,.0f}"))
        self.tabla.setItem(fila, 2, QTableWidgetItem(str(cantidad)))
        self.tabla.setItem(fila, 3, QTableWidgetItem(total_cop))

        self.productos_seleccionados.append(
            (self.numero_factura, cliente, art.articulo, float(art.precio), cantidad, total_cop, float(art.costo), codigo_final)
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
        try:
            descuento = float(self.entry_descuento.text().replace(",", ".")) if self.entry_descuento.text() else 0
        except ValueError:
            descuento = 0
        total_final = max(total - descuento, 0)
        self.label_total.setText(f"Precio a pagar: ${total_final:,.0f}")
        self.total_con_descuento = total_final
        self.descuento_actual = descuento

    def _eliminar_articulo(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.critical(self, "Error", "No seleccionaste ningún artículo.")
            return
        articulo = self.tabla.item(fila, 0).text()
        self.tabla.removeRow(fila)
        self.productos_seleccionados = [p for p in self.productos_seleccionados if p[2] != articulo]
        self._calcular_total()

    def _editar_articulo(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.critical(self, "Error", "No seleccionaste ningún artículo.")
            return
        articulo = self.tabla.item(fila, 0).text()
        cantidad_actual = self.tabla.item(fila, 2).text()

        from PySide6.QtWidgets import QInputDialog
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
                codigo_existente = p[7] if len(p) >= 8 else None
                self.productos_seleccionados[idx] = (
                    self.numero_factura, cliente, articulo, art.precio, nueva_cantidad, total_cop, art.costo, codigo_existente,
                )
                break
        self._calcular_total()

    def _limpiar_carrito(self):
        self.tabla.setRowCount(0)
        self.productos_seleccionados.clear()
        self._calcular_total()

    def _limpiar_campos(self):
        self.tabla.setRowCount(0)
        self.combo_cliente.setCurrentText("")
        self.combo_producto.setCurrentText("")
        self.entry_cantidad.clear()
        self.label_total.setText("Precio a pagar: $0")

    # ---------- checkout ----------

    def _cobrar(self):
        if self.tabla.rowCount() == 0:
            QMessageBox.critical(self, "Error", "No hay productos seleccionados para realizar el pago.")
            return
        self._calcular_total()
        dialogo = PagoDialog(self, self.total_con_descuento)
        if dialogo.exec() != QDialog.Accepted or not dialogo.resultado:
            return
        metodo_pago, banco, cantidad_pagada, efectivo_monto, transferencia_monto = dialogo.resultado
        self._procesar_pago(metodo_pago, banco, cantidad_pagada, efectivo_monto, transferencia_monto)

    def _procesar_pago(self, metodo_pago, banco, cantidad_pagada, efectivo_monto, transferencia_monto):
        total_venta = self.total_con_descuento
        descuento = getattr(self, "descuento_actual", 0)
        cliente = self.combo_cliente.currentText().strip()

        if not self.sucursal_valida():
            return

        try:
            self.venta_service.registrar_venta(
                self.productos_seleccionados, datetime.datetime.now().strftime("%Y-%m-%d"),
                datetime.datetime.now().strftime("%H:%M:%S"), metodo_pago, self._sucursal_venta, banco, descuento,
            )
            if metodo_pago == "pago parcial":
                fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
                if efectivo_monto and efectivo_monto > 0:
                    self.venta_service.registrar_abono(self.numero_factura, fecha_actual, efectivo_monto, "efectivo", None, self._sucursal_venta)
                if transferencia_monto and transferencia_monto > 0:
                    self.venta_service.registrar_abono(self.numero_factura, fecha_actual, transferencia_monto, "transferencia", banco, self._sucursal_venta)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al registrar la venta: {e}")
            return

        try:
            self.generar_factura_pdf(
                total_venta, cliente, descuento=descuento, banco=banco,
                efectivo_pagado=efectivo_monto if efectivo_monto and efectivo_monto > 0 else None,
                transferencia_pagada=transferencia_monto if transferencia_monto and transferencia_monto > 0 else None,
            )
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"La venta se registró pero no se pudo generar el PDF: {e}")

        self.numero_factura += 1
        self.label_factura.setText(f"Factura: {self.numero_factura}")
        self.productos_seleccionados = []
        self._limpiar_campos()

    def sucursal_valida(self):
        sucursal_venta = None
        if self.username:
            usuario = self.usuario_service.obtener_por_username(self.username.strip())
            if usuario:
                if usuario.rol and usuario.rol.lower() in ["admin", "administrador"]:
                    sucursal_venta = "ADMIN"
                else:
                    sucursal_venta = usuario.sucursal
        if not sucursal_venta or sucursal_venta == "None":
            QMessageBox.critical(self, "Error", f"El usuario '{self.username}' no tiene una sucursal asignada. Contactá al administrador.")
            return False
        self._sucursal_venta = sucursal_venta
        return True

    # ---------- factura PDF ----------

    def generar_factura_pdf(self, total_venta, cliente, num_factura=None, descuento=0, banco=None, efectivo_pagado=None, transferencia_pagada=None):
        if num_factura is None:
            num_factura = self.numero_factura
        factura_path = rutas(f"facturas/factura_{num_factura}.pdf")
        os.makedirs(os.path.dirname(factura_path), exist_ok=True)

        info_empresa = self.empresa_service.obtener()
        if info_empresa:
            empresa = {
                "nombre": info_empresa.nombre, "direccion": info_empresa.direccion,
                "telefono": info_empresa.telefono, "email": info_empresa.email, "nit": info_empresa.nit,
            }
        else:
            empresa = {"nombre": "Empresa no configurada"}

        try:
            metodo_result = self.venta_service.obtener_metodo_pago_banco(num_factura)
            metodo = metodo_result[0] if metodo_result and metodo_result[0] else "No especificado"
            banco_val = banco if banco else (metodo_result[1] if metodo_result and len(metodo_result) > 1 else None)
        except Exception:
            metodo, banco_val = "No especificado", banco

        metodo_str = str(metodo).upper()

        if num_factura != self.numero_factura:
            try:
                productos_factura = self.venta_service.listar_para_pdf(num_factura)
            except Exception:
                productos_factura = []
        else:
            productos_factura = [(p[2], p[4], p[3], p[5]) for p in self.productos_seleccionados]

        items_ticket = []
        for producto, cantidad, precio, total in productos_factura:
            if isinstance(precio, str):
                precio = float(precio.replace(",", "").replace(" ", ""))
            if isinstance(total, str):
                total = float(total.replace(",", "").replace(" ", ""))
            items_ticket.append((producto, cantidad, precio, total))

        encabezado = [
            f"Factura: {num_factura}",
            f"Fecha: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
            f"Cliente: {cliente or 'No especificado'}",
            f"Método de pago: {metodo_str}",
        ]
        if "TRANSFERENCIA" in metodo_str and banco_val:
            encabezado.append(f"Banco: {banco_val}")

        resumen = [(f"Total bruto: ${total_venta:,.0f}", False)]
        if descuento and descuento > 0:
            resumen.append((f"Descuento: -${descuento:,.0f}", False))
        total_neto = max(total_venta - descuento, 0)
        resumen.append((f"TOTAL A PAGAR: ${total_neto:,.0f}", True))
        if efectivo_pagado and efectivo_pagado > 0:
            resumen.append((f"Pago efectivo: ${efectivo_pagado:,.0f}", False))
        if transferencia_pagada and transferencia_pagada > 0:
            resumen.append((f"Pago transferencia: ${transferencia_pagada:,.0f}", False))

        pie = [
            "¡Gracias por su compra!",
            "Los productos no tienen cambio ni devolución.",
            "Conserve este ticket para cualquier reclamo (30 días).",
        ]
        generar_ticket_pdf(factura_path, empresa, "FACTURA DE VENTA", encabezado, items_ticket, resumen, pie)

        if os.path.exists(factura_path):
            try:
                impreso = imprimir_ticket(self, empresa, "FACTURA DE VENTA", encabezado, items_ticket, resumen, pie)
            except Exception as e:
                impreso = False
                QMessageBox.warning(self, "Impresión", f"No se pudo imprimir: {e}")
            if impreso:
                QMessageBox.information(self, "Éxito", f"La factura {num_factura} se generó e imprimió correctamente.")
            else:
                QMessageBox.information(self, "Éxito", f"La factura {num_factura} se generó correctamente (guardada en {factura_path}).")

    # ---------- reporte ----------

    def _ver_reporte(self):
        from Smart_data_syncro.qt_ui.ventas_reporte_window import VentasReporteWindow
        self._ventana_reporte = VentasReporteWindow(self.venta_service, self.sucursal, self.generar_factura_pdf)
        self._ventana_reporte.show()
