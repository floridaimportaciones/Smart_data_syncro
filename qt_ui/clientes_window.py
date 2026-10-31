"""Pantalla de Clientes en PySide6 -- reemplaza clientes.py (Tkinter).

Se abre desde container.py como una ventana aparte (ver Container.clientes()):
Tkinter se pausa mientras esta ventana esta abierta, y retoma cuando se cierra.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QFormLayout,
    QMessageBox, QAbstractItemView,
)

from Smart_data_syncro.services.cliente_service import ClienteService
from Smart_data_syncro.qt_ui.theme import QSS


class ClienteDialog(QDialog):
    """Formulario para crear o editar un cliente."""

    def __init__(self, parent=None, cliente=None):
        super().__init__(parent)
        self.cliente = cliente  # None = nuevo, objeto Cliente = edicion
        self.setWindowTitle("Editar cliente" if cliente else "Nuevo cliente")
        self.setStyleSheet(QSS)
        self.setFixedWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)
        self.entry_nombre = QLineEdit()
        self.entry_cedula = QLineEdit()
        self.entry_celular = QLineEdit()
        self.entry_direccion = QLineEdit()
        self.entry_correo = QLineEdit()
        form.addRow("Nombre:", self.entry_nombre)
        form.addRow("Cédula o NIT:", self.entry_cedula)
        form.addRow("Celular:", self.entry_celular)
        form.addRow("Dirección:", self.entry_direccion)
        form.addRow("Correo:", self.entry_correo)
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

        if cliente:
            self.entry_nombre.setText(cliente.nombre or "")
            self.entry_cedula.setText(str(cliente.cedula) if cliente.cedula else "")
            self.entry_celular.setText(str(cliente.celular) if cliente.celular else "")
            self.entry_direccion.setText(cliente.direccion or "")
            self.entry_correo.setText(cliente.correo or "")

    def _guardar(self):
        self.label_error.setText("")
        self.datos = (
            self.entry_nombre.text().strip(),
            self.entry_cedula.text().strip(),
            self.entry_celular.text().strip(),
            self.entry_direccion.text().strip(),
            self.entry_correo.text().strip(),
        )
        self.accept()


class ClientesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.service = ClienteService()

        self.setWindowTitle("Clientes")
        self.resize(820, 520)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel("Clientes")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        barra = QHBoxLayout()
        self.entry_buscar = QLineEdit()
        self.entry_buscar.setPlaceholderText("Buscar por nombre, cédula, celular, dirección o correo…")
        self.entry_buscar.textChanged.connect(self._filtrar)
        btn_nuevo = QPushButton("Nuevo cliente")
        btn_nuevo.setObjectName("primario")
        btn_nuevo.clicked.connect(self._nuevo)
        btn_editar = QPushButton("Editar seleccionado")
        btn_editar.clicked.connect(self._editar)
        barra.addWidget(self.entry_buscar)
        barra.addWidget(btn_nuevo)
        barra.addWidget(btn_editar)
        layout.addLayout(barra)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Cédula", "Celular", "Dirección", "Correo"])
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.tabla.doubleClicked.connect(self._editar)
        layout.addWidget(self.tabla)

        self._cargar()

    def _cargar(self, filtro=None):
        try:
            clientes = self.service.listar(filtro)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los clientes: {e}")
            return
        self.tabla.setRowCount(0)
        for c in clientes:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            valores = [c.id, c.nombre, c.cedula, c.celular, c.direccion, c.correo]
            for col, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor) if valor is not None else "")
                self.tabla.setItem(fila, col, item)

    def _filtrar(self, texto):
        self._cargar(texto)

    def _nuevo(self):
        dialogo = ClienteDialog(self)
        if dialogo.exec() == QDialog.Accepted:
            nombre, cedula, celular, direccion, correo = dialogo.datos
            try:
                self.service.crear(nombre, cedula, celular, direccion, correo)
            except ValueError as e:
                QMessageBox.warning(self, "Campos inválidos", str(e))
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo registrar el cliente: {e}")
                return
            self._cargar(self.entry_buscar.text())

    def _editar(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Sin selección", "Seleccioná un cliente para editar.")
            return
        id_cliente = int(self.tabla.item(fila, 0).text())
        cliente = next((c for c in self.service.listar() if c.id == id_cliente), None)
        if not cliente:
            QMessageBox.critical(self, "Error", "No se encontró el cliente seleccionado.")
            return

        dialogo = ClienteDialog(self, cliente=cliente)
        if dialogo.exec() == QDialog.Accepted:
            nombre, cedula, celular, direccion, correo = dialogo.datos
            try:
                self.service.actualizar(id_cliente, nombre, cedula, celular, direccion, correo)
            except ValueError as e:
                QMessageBox.warning(self, "Campos inválidos", str(e))
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el cliente: {e}")
                return
            self._cargar(self.entry_buscar.text())
