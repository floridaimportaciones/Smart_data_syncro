"""Pantalla de Inventario en PySide6 -- reemplaza inventario.py (Tkinter).

Se abre desde container.py como ventana aparte, mismo patron que los demas
modulos ya migrados.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QMessageBox, QAbstractItemView, QFileDialog,
)

from Smart_data_syncro.services.articulo_service import ArticuloService
from Smart_data_syncro.services.sucursal_service import SucursalService
from Smart_data_syncro.excel_import import leer_filas_articulos
from Smart_data_syncro.qt_ui.theme import QSS

COLOR_STOCK_BAJO = QColor("#FFCCCC")


class ArticuloDialog(QDialog):
    def __init__(self, parent=None, articulo=None, sucursales=None):
        super().__init__(parent)
        self.articulo = articulo  # None = nuevo
        self.setWindowTitle("Editar artículo" if articulo else "Nuevo artículo")
        self.setStyleSheet(QSS)
        self.setFixedWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)
        self.entry_articulo = QLineEdit()
        self.entry_codigo = QLineEdit()
        self.entry_precio = QLineEdit()
        self.entry_costo = QLineEdit()
        self.entry_stock = QLineEdit()
        self.entry_stock_minimo = QLineEdit()
        self.combo_sucursal = QComboBox()
        self.combo_sucursal.addItems(sucursales or [])
        form.addRow("Artículo:", self.entry_articulo)
        form.addRow("Código:", self.entry_codigo)
        form.addRow("Precio:", self.entry_precio)
        form.addRow("Costo:", self.entry_costo)
        form.addRow("Stock:", self.entry_stock)
        form.addRow("Stock mínimo:", self.entry_stock_minimo)
        form.addRow("Sucursal:", self.combo_sucursal)
        layout.addLayout(form)

        self.label_error = QLabel("")
        self.label_error.setObjectName("error")
        self.label_error.setWordWrap(True)
        layout.addWidget(self.label_error)

        botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setObjectName("primario")
        btn_guardar.clicked.connect(self._guardar)
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)
        layout.addLayout(botones)

        if articulo:
            self.entry_articulo.setText(articulo.articulo or "")
            self.entry_codigo.setText(articulo.codigo or "")
            self.entry_precio.setText(str(articulo.precio))
            self.entry_costo.setText(str(articulo.costo))
            self.entry_stock.setText(str(articulo.stock))
            self.entry_stock_minimo.setText(str(articulo.stock_minimo))
            if articulo.sucursal_obj:
                idx = self.combo_sucursal.findText(articulo.sucursal_obj.nombre)
                if idx >= 0:
                    self.combo_sucursal.setCurrentIndex(idx)

    def _guardar(self):
        self.label_error.setText("")
        nombre = self.entry_articulo.text().strip()
        codigo = self.entry_codigo.text().strip()
        if not nombre or not codigo:
            self.label_error.setText("Artículo y código son obligatorios.")
            return
        try:
            precio = float(self.entry_precio.text().replace(",", "."))
            costo = float(self.entry_costo.text().replace(",", "."))
            stock = int(self.entry_stock.text())
            stock_minimo = int(self.entry_stock_minimo.text())
        except ValueError:
            self.label_error.setText("Precio, costo, stock y stock mínimo deben ser números.")
            return
        self.datos = (nombre, precio, costo, codigo, stock, stock_minimo, self.combo_sucursal.currentText())
        self.accept()


class InventarioWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.service = ArticuloService()
        self.sucursal_service = SucursalService()

        self.setWindowTitle("Inventario")
        self.resize(900, 560)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel("Inventario")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        barra = QHBoxLayout()
        self.entry_buscar = QLineEdit()
        self.entry_buscar.setPlaceholderText("Buscar por artículo o código…")
        self.entry_buscar.textChanged.connect(self._filtrar)
        btn_nuevo = QPushButton("Nuevo artículo")
        btn_nuevo.setObjectName("primario")
        btn_nuevo.clicked.connect(self._nuevo)
        btn_editar = QPushButton("Editar")
        btn_editar.clicked.connect(self._editar)
        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.clicked.connect(self._eliminar)
        btn_importar = QPushButton("Importar Excel/CSV")
        btn_importar.clicked.connect(self._importar)
        barra.addWidget(self.entry_buscar)
        barra.addWidget(btn_nuevo)
        barra.addWidget(btn_editar)
        barra.addWidget(btn_eliminar)
        barra.addWidget(btn_importar)
        layout.addLayout(barra)

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(["Artículo", "Precio", "Costo", "Código", "Stock", "Stock mínimo", "Sucursal"])
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla.doubleClicked.connect(self._editar)
        layout.addWidget(self.tabla)

        self._cargar()

    def _nombres_sucursales(self):
        try:
            return [s.nombre for s in self.sucursal_service.listar()]
        except Exception:
            return []

    def _cargar(self, filtro=None):
        try:
            articulos = self.service.listar(filtro)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los artículos: {e}")
            return
        self.tabla.setRowCount(0)
        for a in articulos:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            sucursal_nombre = a.sucursal_obj.nombre if a.sucursal_obj else ""
            valores = [a.articulo, f"${a.precio:,.2f}", f"${a.costo:,.2f}", a.codigo, a.stock, a.stock_minimo, sucursal_nombre]
            bajo_stock = a.stock_minimo is not None and a.stock < a.stock_minimo
            for col, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor) if valor is not None else "")
                if bajo_stock:
                    item.setBackground(COLOR_STOCK_BAJO)
                self.tabla.setItem(fila, col, item)
            self.tabla.item(fila, 0).setData(Qt.UserRole, a.id)

    def _filtrar(self, texto):
        self._cargar(texto)

    def _nuevo(self):
        dialogo = ArticuloDialog(self, sucursales=self._nombres_sucursales())
        if dialogo.exec() == QDialog.Accepted:
            nombre, precio, costo, codigo, stock, stock_minimo, sucursal_nombre = dialogo.datos
            sucursal_id = self._id_sucursal(sucursal_nombre)
            try:
                self.service.crear(nombre, precio, costo, codigo, stock, stock_minimo, sucursal_id)
            except ValueError as e:
                QMessageBox.warning(self, "Datos inválidos", str(e))
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el artículo: {e}")
                return
            self._cargar(self.entry_buscar.text())

    def _id_sucursal(self, nombre):
        for s in self.sucursal_service.listar():
            if s.nombre == nombre:
                return s.id
        return None

    def _fila_seleccionada(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Sin selección", "Seleccioná un artículo primero.")
            return None
        return fila

    def _editar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        id_articulo = self.tabla.item(fila, 0).data(Qt.UserRole)
        articulo = next((a for a in self.service.listar() if a.id == id_articulo), None)
        if not articulo:
            QMessageBox.critical(self, "Error", "No se encontró el artículo seleccionado.")
            return

        dialogo = ArticuloDialog(self, articulo=articulo, sucursales=self._nombres_sucursales())
        if dialogo.exec() == QDialog.Accepted:
            nombre, precio, costo, codigo, stock, stock_minimo, sucursal_nombre = dialogo.datos
            sucursal_id = self._id_sucursal(sucursal_nombre)
            try:
                self.service.actualizar(id_articulo, nombre, precio, costo, codigo, stock, stock_minimo, sucursal_id)
            except ValueError as e:
                QMessageBox.warning(self, "Datos inválidos", str(e))
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el artículo: {e}")
                return
            self._cargar(self.entry_buscar.text())

    def _eliminar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        id_articulo = self.tabla.item(fila, 0).data(Qt.UserRole)
        nombre = self.tabla.item(fila, 0).text()
        respuesta = QMessageBox.question(self, "Confirmar", f"¿Eliminar el artículo '{nombre}'?")
        if respuesta != QMessageBox.Yes:
            return
        try:
            self.service.eliminar(id_articulo)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar el artículo: {e}")
            return
        self._cargar(self.entry_buscar.text())

    def _importar(self):
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccioná el archivo de Excel/CSV", "",
            "Excel o CSV (*.xlsx *.xlsm *.csv);;Todos (*.*)",
        )
        if not archivo:
            return
        try:
            rows = leer_filas_articulos(archivo)
        except ImportError:
            QMessageBox.critical(self, "Falta dependencia", "Para leer archivos Excel (.xlsx) se requiere el paquete 'openpyxl'.")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo: {e}")
            return
        if not rows:
            QMessageBox.warning(self, "Sin datos", "No se encontraron filas válidas en el archivo.")
            return

        sucursales = self.sucursal_service.listar()
        mapa_sucursales = {s.nombre: s.id for s in sucursales}
        sucursal_default = sucursales[0].id if sucursales else None

        resultado = self.service.importar_filas(rows, mapa_sucursales, sucursal_default)
        self._cargar()
        QMessageBox.information(
            self, "Importación completada",
            f"Artículos insertados: {resultado['insertados']}\n"
            f"Artículos actualizados: {resultado['actualizados']}\n"
            f"Filas omitidas: {resultado['omitidos']}\n"
            f"Filas con error: {resultado['errores']}",
        )
