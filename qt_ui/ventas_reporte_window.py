"""Reporte de ventas realizadas (PySide6) -- reemplaza ver_ventas_realizadas() de ventas.py."""
import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView,
)

from Smart_data_syncro.qt_ui.theme import QSS

COLUMNAS = ["Factura", "Cliente", "Producto", "Precio", "Cantidad", "Total", "Descuento", "Fecha", "Hora", "Método", "Sucursal", "Banco"]


class VentasReporteWindow(QWidget):
    def __init__(self, venta_service, sucursal, generar_pdf_callback):
        super().__init__()
        self.venta_service = venta_service
        self.sucursal = sucursal
        self.generar_pdf_callback = generar_pdf_callback
        self.ventas = []

        self.setWindowTitle("Ventas realizadas")
        self.resize(1050, 600)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel("Ventas realizadas")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        filtros = QHBoxLayout()
        self.entry_fecha = QLineEdit(datetime.datetime.now().strftime("%d-%m-%Y"))
        self.entry_fecha.setFixedWidth(100)
        self.entry_factura = QLineEdit()
        self.entry_factura.setPlaceholderText("Factura")
        self.entry_factura.setFixedWidth(90)
        self.entry_cliente = QLineEdit()
        self.entry_cliente.setPlaceholderText("Cliente")
        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.setObjectName("primario")
        btn_filtrar.clicked.connect(self._filtrar)
        filtros.addWidget(QLabel("Fecha (dd-mm-aaaa):"))
        filtros.addWidget(self.entry_fecha)
        filtros.addWidget(self.entry_factura)
        filtros.addWidget(self.entry_cliente)
        filtros.addWidget(btn_filtrar)
        filtros.addStretch()
        layout.addLayout(filtros)

        self.tabla = QTableWidget(0, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.tabla)

        fila_inferior = QHBoxLayout()
        self.label_total = QLabel("Total del día: $0")
        self.label_total.setObjectName("titulo")
        fila_inferior.addWidget(self.label_total)
        fila_inferior.addStretch()
        btn_ver_factura = QPushButton("Ver factura")
        btn_ver_factura.clicked.connect(self._ver_factura)
        fila_inferior.addWidget(btn_ver_factura)
        layout.addLayout(fila_inferior)

        self._cargar()
        self._filtrar()

    def _cargar(self):
        try:
            self.ventas = self.venta_service.listar_reporte(self.sucursal)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las ventas: {e}")
            self.ventas = []

    def _filtrar(self):
        fecha_txt = self.entry_fecha.text().strip()
        factura_txt = self.entry_factura.text().strip()
        cliente_txt = self.entry_cliente.text().strip().lower()

        try:
            fecha_objetivo = datetime.datetime.strptime(fecha_txt, "%d-%m-%Y").strftime("%Y-%m-%d") if fecha_txt else None
        except ValueError:
            QMessageBox.critical(self, "Error", "Formato de fecha inválido. Usá DD-MM-AAAA.")
            return

        self.tabla.setRowCount(0)
        total_dia = 0.0
        for venta in self.ventas:
            factura, cliente, producto, precio, cantidad, total, descuento, fecha, hora, metodo, sucursal, banco = venta
            fecha_simple = str(fecha)[:10]
            if fecha_objetivo and fecha_simple != fecha_objetivo:
                continue
            if factura_txt and str(factura) != factura_txt:
                continue
            if cliente_txt and cliente_txt not in str(cliente).lower():
                continue

            try:
                total_num = float(str(total).replace(",", "").replace(" ", ""))
            except ValueError:
                total_num = 0.0
            total_dia += total_num

            try:
                fecha_mostrar = datetime.datetime.strptime(fecha_simple, "%Y-%m-%d").strftime("%d-%m-%Y")
            except ValueError:
                fecha_mostrar = fecha_simple

            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            valores = [factura, cliente, producto, precio, cantidad, f"{total_num:,.0f}", descuento, fecha_mostrar, hora, metodo, sucursal, banco or ""]
            for col, valor in enumerate(valores):
                self.tabla.setItem(fila, col, QTableWidgetItem(str(valor) if valor is not None else ""))

        self.label_total.setText(f"Total: ${total_dia:,.0f}")

    def _ver_factura(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Sin selección", "Seleccioná una venta.")
            return
        num_factura = self.tabla.item(fila, 0).text()
        cliente = self.tabla.item(fila, 1).text()
        try:
            detalle = self.venta_service.obtener_detalle_factura(num_factura, cliente)
            if not detalle["productos"]:
                QMessageBox.warning(self, "Sin datos", "No se encontraron productos para esta factura.")
                return
            self.generar_pdf_callback(
                detalle["total"], cliente, num_factura=num_factura, descuento=detalle["descuento"],
                efectivo_pagado=detalle["efectivo"], transferencia_pagada=detalle["transferencia"],
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al regenerar la factura: {e}")
