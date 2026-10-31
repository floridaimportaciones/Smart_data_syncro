"""Reportes (PySide6) -- reemplaza reportes.py (Tkinter)."""
import datetime

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView, QDateEdit, QDialog, QFileDialog, QGridLayout,
    QHBoxLayout, QHeaderView, QInputDialog, QLabel, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from Smart_data_syncro.qt_ui.theme import QSS
from Smart_data_syncro.services.articulo_service import ArticuloService
from Smart_data_syncro.services.venta_service import VentaService

MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']


class ReporteRangoDialog(QDialog):
    """Filtro de fecha desde/hasta + tabla de resultado -- reusado por ventas totales y ganancias."""

    def __init__(self, titulo, columnas, consultar_callback, explicacion, parent=None):
        super().__init__(parent)
        self.consultar_callback = consultar_callback
        self.setWindowTitle(titulo)
        self.resize(520, 450)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("titulo")
        layout.addWidget(lbl_titulo)

        filtros = QHBoxLayout()
        self.fecha_desde = QDateEdit(QDate.currentDate())
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_hasta = QDateEdit(QDate.currentDate())
        self.fecha_hasta.setCalendarPopup(True)
        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.setObjectName("primario")
        btn_filtrar.clicked.connect(self._filtrar)
        filtros.addWidget(QLabel("Desde:"))
        filtros.addWidget(self.fecha_desde)
        filtros.addWidget(QLabel("Hasta:"))
        filtros.addWidget(self.fecha_hasta)
        filtros.addWidget(btn_filtrar)
        filtros.addStretch()
        layout.addLayout(filtros)

        self.tabla = QTableWidget(0, len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)

        lbl_explicacion = QLabel(explicacion)
        lbl_explicacion.setWordWrap(True)
        lbl_explicacion.setObjectName("subtitulo")
        layout.addWidget(lbl_explicacion)

    def _filtrar(self):
        fecha_ini = self.fecha_desde.date().toPython()
        fecha_fin = self.fecha_hasta.date().toPython()
        try:
            filas = self.consultar_callback(fecha_ini, fecha_fin)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al consultar la base de datos: {e}")
            return
        self.tabla.setRowCount(0)
        if not filas:
            QMessageBox.information(self, "Sin datos", "No se encontraron datos en ese rango de fechas.")
            return
        for fila in filas:
            r = self.tabla.rowCount()
            self.tabla.insertRow(r)
            for c, valor in enumerate(fila):
                self.tabla.setItem(r, c, QTableWidgetItem(str(valor)))


class GraficoDialog(QDialog):
    """Grafico de barras embebido (matplotlib + Qt)."""

    def __init__(self, titulo, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.resize(850, 650)
        self.setStyleSheet(QSS)
        self.layout_principal = QVBoxLayout(self)

    def mostrar_figura(self, fig):
        canvas = FigureCanvasQTAgg(fig)
        self.layout_principal.addWidget(canvas)


class ReportesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.venta_service = VentaService()
        self.articulo_service = ArticuloService()

        self.setWindowTitle("Reportes")
        self.resize(900, 420)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        titulo = QLabel("Reportes")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        grid = QGridLayout()
        grid.setSpacing(16)
        layout.addLayout(grid)

        botones = [
            ("Ventas totales", self._reporte_ventas_totales),
            ("Ganancias", self._reporte_ganancias),
            ("Ventas por mes", self._reporte_ventas_por_mes),
            ("Ventas y ganancias por mes", self._grafico_ganancias_por_mes),
            ("Exportar Excel", self._exportar_excel),
        ]
        for i, (texto, callback) in enumerate(botones):
            btn = QPushButton(texto)
            btn.setObjectName("primario")
            btn.setMinimumHeight(100)
            btn.clicked.connect(callback)
            grid.addWidget(btn, i // 3, i % 3)

        layout.addStretch()

    def _reporte_ventas_totales(self):
        def consultar(fecha_ini, fecha_fin):
            cantidad, total = self.venta_service.totales_por_rango(fecha_ini, fecha_fin)
            if cantidad is None:
                return []
            return [(cantidad, f"${total:,.2f}")]

        dialogo = ReporteRangoDialog(
            "Reporte de ventas totales", ["Cantidad de productos vendidos", "Total de ventas"],
            consultar, "El reporte de ventas totales equivale al total de las ventas de los productos "
                       "incluyendo costo y ganancia.", self,
        )
        dialogo.exec()

    def _reporte_ganancias(self):
        def consultar(fecha_ini, fecha_fin):
            ganancias = self.venta_service.ganancias_por_rango(fecha_ini, fecha_fin)
            if ganancias is None:
                return []
            return [(f"${ganancias:,.2f}",)]

        dialogo = ReporteRangoDialog(
            "Reporte de ganancias", ["Ganancias totales"],
            consultar, "El reporte de ganancias equivale a las ventas totales menos el costo de los productos.", self,
        )
        dialogo.exec()

    def _pedir_anio(self):
        anio, ok = QInputDialog.getInt(self, "Año", "Ingrese el año para filtrar:", datetime.datetime.now().year, 2000, 2100)
        return anio if ok else None

    def _reporte_ventas_por_mes(self):
        anio = self._pedir_anio()
        if anio is None:
            return
        try:
            resultados = self.venta_service.ventas_por_mes(anio)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al consultar la base de datos: {e}")
            return

        valores = [0] * 12
        for mes, total in resultados:
            valores[int(mes) - 1] = float(total)

        fig = Figure(figsize=(9, 6), dpi=100)
        ax = fig.add_subplot(111)
        barras = ax.bar(range(12), valores, color="skyblue")
        ax.set_title(f"Ventas por mes en {anio}")
        ax.set_xlabel("Mes")
        ax.set_ylabel("Total de ventas")
        ax.set_xticks(range(12))
        ax.set_xticklabels(MESES)
        ax.grid(True, linestyle="--", alpha=0.7)
        for barra in barras:
            altura = barra.get_height()
            ax.text(barra.get_x() + barra.get_width() / 2, altura, f"${altura:,.2f}", ha="center", va="bottom", fontsize=8)

        dialogo = GraficoDialog(f"Ventas por mes en {anio}", self)
        dialogo.mostrar_figura(fig)
        dialogo.exec()

    def _grafico_ganancias_por_mes(self):
        anio = self._pedir_anio()
        if anio is None:
            return
        try:
            resultados = self.venta_service.ventas_y_ganancias_por_mes(anio)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al consultar la base de datos: {e}")
            return

        ventas = [0] * 12
        ganancias = [0] * 12
        for mes, costo, venta, ganancia in resultados:
            idx = int(mes) - 1
            ventas[idx] = float(venta or 0)
            ganancias[idx] = float(ganancia or 0)

        fig = Figure(figsize=(9, 6), dpi=100)
        ax = fig.add_subplot(111)
        x = range(12)
        ancho = 0.35
        barras1 = ax.bar([i - ancho / 2 for i in x], ventas, ancho, label="Ventas", color="skyblue")
        barras2 = ax.bar([i + ancho / 2 for i in x], ganancias, ancho, label="Ganancias", color="lightgreen")
        ax.set_title(f"Ventas y ganancias por mes en {anio}")
        ax.set_xlabel("Mes")
        ax.set_ylabel("Total")
        ax.set_xticks(x)
        ax.set_xticklabels(MESES)
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.7)
        for barras in (barras1, barras2):
            for barra in barras:
                altura = barra.get_height()
                if altura > 0:
                    ax.text(barra.get_x() + barra.get_width() / 2, altura, f"${altura:,.2f}", ha="center", va="bottom", fontsize=7)

        dialogo = GraficoDialog(f"Ventas y ganancias por mes en {anio}", self)
        dialogo.mostrar_figura(fig)
        dialogo.exec()

    def _exportar_excel(self):
        tipo, ok = QInputDialog.getItem(self, "Exportar a Excel", "¿Qué deseas exportar?", ["Inventario", "Ventas por mes"], 0, False)
        if not ok:
            return
        archivo, _ = QFileDialog.getSaveFileName(self, "Guardar como", "", "Archivos Excel (*.xlsx)")
        if not archivo:
            return
        if not archivo.endswith(".xlsx"):
            archivo += ".xlsx"

        try:
            from openpyxl import Workbook
            libro = Workbook()
            hoja = libro.active

            if tipo == "Inventario":
                hoja.title = "Inventario"
                hoja.append(["ID", "Articulo", "Precio", "Costo", "Codigo", "Stock", "Stock minimo", "Sucursal"])
                for a in self.articulo_service.listar():
                    hoja.append([a.id, a.articulo, a.precio, a.costo, a.codigo, a.stock, a.stock_minimo,
                                 a.sucursal_obj.nombre if a.sucursal_obj else ""])
            else:
                hoja.title = "Ventas"
                hoja.append(["Mes", "Total Ventas"])
                for fila in self.venta_service.ventas_agrupadas_por_mes_todas():
                    hoja.append(fila)

            libro.save(archivo)
            QMessageBox.information(self, "Éxito", f"Datos exportados a {archivo} exitosamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar:\n{e}")
