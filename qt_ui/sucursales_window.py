"""Pantalla de Sucursales en PySide6 -- reemplaza la seccion de sucursales de configuracion.py."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QFormLayout,
    QMessageBox, QAbstractItemView,
)

from Smart_data_syncro.services.sucursal_service import SucursalService
from Smart_data_syncro.qt_ui.theme import QSS


class SucursalDialog(QDialog):
    def __init__(self, parent=None, sucursal=None):
        super().__init__(parent)
        self.sucursal = sucursal
        self.setWindowTitle("Editar sucursal" if sucursal else "Nueva sucursal")
        self.setStyleSheet(QSS)
        self.setFixedWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        form = QFormLayout()
        self.entry_nombre = QLineEdit()
        form.addRow("Nombre:", self.entry_nombre)
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

        if sucursal:
            self.entry_nombre.setText(sucursal.nombre or "")

    def _guardar(self):
        nombre = self.entry_nombre.text().strip()
        if not nombre:
            self.label_error.setText("El nombre no puede estar vacío.")
            return
        self.nombre = nombre
        self.accept()


class SucursalesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.service = SucursalService()

        self.setWindowTitle("Sucursales")
        self.resize(500, 480)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel("Sucursales")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        barra = QHBoxLayout()
        btn_nueva = QPushButton("Nueva sucursal")
        btn_nueva.setObjectName("primario")
        btn_nueva.clicked.connect(self._nueva)
        btn_editar = QPushButton("Editar")
        btn_editar.clicked.connect(self._editar)
        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.clicked.connect(self._eliminar)
        barra.addWidget(btn_nueva)
        barra.addWidget(btn_editar)
        barra.addWidget(btn_eliminar)
        barra.addStretch()
        layout.addLayout(barra)

        self.tabla = QTableWidget(0, 2)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre"])
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.doubleClicked.connect(self._editar)
        layout.addWidget(self.tabla)

        self._cargar()

    def _cargar(self):
        try:
            sucursales = self.service.listar()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las sucursales: {e}")
            return
        self.tabla.setRowCount(0)
        for s in sucursales:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            self.tabla.setItem(fila, 0, QTableWidgetItem(str(s.id)))
            self.tabla.setItem(fila, 1, QTableWidgetItem(s.nombre or ""))

    def _nueva(self):
        dialogo = SucursalDialog(self)
        if dialogo.exec() == QDialog.Accepted:
            try:
                self.service.crear(dialogo.nombre)
            except ValueError as e:
                QMessageBox.warning(self, "Datos inválidos", str(e))
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la sucursal: {e}")
                return
            self._cargar()

    def _fila_seleccionada(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Sin selección", "Seleccioná una sucursal primero.")
            return None
        return fila

    def _editar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        id_sucursal = int(self.tabla.item(fila, 0).text())
        sucursal = next((s for s in self.service.listar() if s.id == id_sucursal), None)
        if not sucursal:
            QMessageBox.critical(self, "Error", "No se encontró la sucursal seleccionada.")
            return
        dialogo = SucursalDialog(self, sucursal=sucursal)
        if dialogo.exec() == QDialog.Accepted:
            try:
                self.service.actualizar(id_sucursal, dialogo.nombre)
            except ValueError as e:
                QMessageBox.warning(self, "Datos inválidos", str(e))
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar la sucursal: {e}")
                return
            self._cargar()

    def _eliminar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        id_sucursal = int(self.tabla.item(fila, 0).text())
        nombre = self.tabla.item(fila, 1).text()
        respuesta = QMessageBox.question(self, "Confirmar", f"¿Eliminar la sucursal '{nombre}'?")
        if respuesta != QMessageBox.Yes:
            return
        try:
            self.service.eliminar(id_sucursal)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar la sucursal: {e}")
            return
        self._cargar()
