"""Pantalla de Usuarios en PySide6 -- reemplaza usuarios.py (Tkinter).

Se abre desde container.py como ventana aparte, igual que Clientes.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QMessageBox, QAbstractItemView,
)

from Smart_data_syncro.services.usuario_service import UsuarioService
from Smart_data_syncro.services.sucursal_service import SucursalService
from Smart_data_syncro.qt_ui.theme import QSS

ROLES = ["Administrador", "Cajero"]


class UsuarioDialog(QDialog):
    """Formulario para crear o editar un usuario."""

    def __init__(self, parent=None, usuario=None, sucursales=None):
        super().__init__(parent)
        self.usuario = usuario  # None = nuevo, objeto Usuario = edicion
        self.setWindowTitle("Editar usuario" if usuario else "Nuevo usuario")
        self.setStyleSheet(QSS)
        self.setFixedWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)
        self.entry_username = QLineEdit()
        self.entry_password = QLineEdit()
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(ROLES)
        self.combo_sucursal = QComboBox()
        self.combo_sucursal.addItems(sucursales or [])
        form.addRow("Usuario:", self.entry_username)
        form.addRow("Contraseña:", self.entry_password)
        form.addRow("Rol:", self.combo_rol)
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

        if usuario:
            self.entry_username.setText(usuario.username or "")
            self.entry_password.setText(usuario.password or "")
            if usuario.rol in ROLES:
                self.combo_rol.setCurrentText(usuario.rol)
            if usuario.sucursal:
                idx = self.combo_sucursal.findText(usuario.sucursal)
                if idx >= 0:
                    self.combo_sucursal.setCurrentIndex(idx)

    def _guardar(self):
        self.label_error.setText("")
        username = self.entry_username.text().strip()
        password = self.entry_password.text().strip()
        if not username or not password:
            self.label_error.setText("Usuario y contraseña son obligatorios.")
            return
        self.datos = (username, password, self.combo_rol.currentText(), self.combo_sucursal.currentText() or None)
        self.accept()


class UsuariosWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.service = UsuarioService()
        self.sucursal_service = SucursalService()

        self.setWindowTitle("Usuarios")
        self.resize(760, 520)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel("Usuarios")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        barra = QHBoxLayout()
        btn_nuevo = QPushButton("Nuevo usuario")
        btn_nuevo.setObjectName("primario")
        btn_nuevo.clicked.connect(self._nuevo)
        btn_editar = QPushButton("Editar seleccionado")
        btn_editar.clicked.connect(self._editar)
        btn_eliminar = QPushButton("Eliminar seleccionado")
        btn_eliminar.clicked.connect(self._eliminar)
        barra.addWidget(btn_nuevo)
        barra.addWidget(btn_editar)
        barra.addWidget(btn_eliminar)
        barra.addStretch()
        layout.addLayout(barra)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Usuario", "Contraseña", "Rol", "Sucursal"])
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.doubleClicked.connect(self._editar)
        layout.addWidget(self.tabla)

        self._cargar()

    def _nombres_sucursales(self):
        try:
            return [s.nombre for s in self.sucursal_service.listar()]
        except Exception:
            return []

    def _cargar(self):
        try:
            usuarios = self.service.listar()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los usuarios: {e}")
            return
        self.tabla.setRowCount(0)
        for u in usuarios:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            valores = [u.id, u.username, u.password, u.rol, u.sucursal or "No asignada"]
            for col, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor) if valor is not None else "")
                self.tabla.setItem(fila, col, item)

    def _nuevo(self):
        dialogo = UsuarioDialog(self, sucursales=self._nombres_sucursales())
        if dialogo.exec() == QDialog.Accepted:
            username, password, rol, sucursal = dialogo.datos
            try:
                self.service.crear(username, password, rol, sucursal)
            except ValueError as e:
                QMessageBox.warning(self, "Datos inválidos", str(e))
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el usuario: {e}")
                return
            self._cargar()

    def _fila_seleccionada(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Sin selección", "Seleccioná un usuario primero.")
            return None
        return fila

    def _editar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        id_usuario = int(self.tabla.item(fila, 0).text())
        usuario = next((u for u in self.service.listar() if u.id == id_usuario), None)
        if not usuario:
            QMessageBox.critical(self, "Error", "No se encontró el usuario seleccionado.")
            return

        dialogo = UsuarioDialog(self, usuario=usuario, sucursales=self._nombres_sucursales())
        if dialogo.exec() == QDialog.Accepted:
            username, password, rol, sucursal = dialogo.datos
            try:
                self.service.actualizar(id_usuario, username, password, rol, sucursal)
            except ValueError as e:
                QMessageBox.warning(self, "Datos inválidos", str(e))
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el usuario: {e}")
                return
            self._cargar()

    def _eliminar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        id_usuario = int(self.tabla.item(fila, 0).text())
        username = self.tabla.item(fila, 1).text()
        respuesta = QMessageBox.question(
            self, "Confirmar", f"¿Eliminar al usuario '{username}'?",
        )
        if respuesta != QMessageBox.Yes:
            return
        try:
            self.service.eliminar(id_usuario)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar el usuario: {e}")
            return
        self._cargar()
