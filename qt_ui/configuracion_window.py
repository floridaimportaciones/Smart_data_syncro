"""Pantalla de Configuracion en PySide6 -- reemplaza configuracion.py (Tkinter).

Agrupa: Sucursales (ventana aparte), Mi Empresa (dialogo), y copia de
seguridad / restauracion de la base de datos (operacion de archivo directa).
"""
import shutil

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QDialog, QFormLayout, QMessageBox, QFileDialog,
)

from Smart_data_syncro.services.empresa_service import EmpresaService
from Smart_data_syncro.utils import DB_PATH
from Smart_data_syncro.qt_ui.theme import QSS


class EmpresaDialog(QDialog):
    def __init__(self, parent=None, service=None):
        super().__init__(parent)
        self.service = service or EmpresaService()
        self.setWindowTitle("Mi Empresa")
        self.setStyleSheet(QSS)
        self.setFixedWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)
        self.entry_nombre = QLineEdit()
        self.entry_direccion = QLineEdit()
        self.entry_telefono = QLineEdit()
        self.entry_email = QLineEdit()
        self.entry_nit = QLineEdit()
        self.entry_website = QLineEdit()
        self.entry_codigo_registro = QLineEdit()
        form.addRow("Nombre:", self.entry_nombre)
        form.addRow("Dirección:", self.entry_direccion)
        form.addRow("Teléfono:", self.entry_telefono)
        form.addRow("Correo:", self.entry_email)
        form.addRow("NIT:", self.entry_nit)
        form.addRow("Sitio web:", self.entry_website)
        form.addRow("Código de registro:", self.entry_codigo_registro)
        layout.addLayout(form)

        nota = QLabel("El código de registro es el que se pide al crear una cuenta nueva (botón \"Registrate\" del login).")
        nota.setObjectName("subtitulo")
        nota.setWordWrap(True)
        layout.addWidget(nota)

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

        self._cargar()

    def _cargar(self):
        try:
            empresa = self.service.obtener()
        except Exception as e:
            self.label_error.setText(f"No se pudo cargar la información: {e}")
            return
        if empresa:
            self.entry_nombre.setText(empresa.nombre or "")
            self.entry_direccion.setText(empresa.direccion or "")
            self.entry_telefono.setText(empresa.telefono or "")
            self.entry_email.setText(empresa.email or "")
            self.entry_nit.setText(empresa.nit or "")
            self.entry_website.setText(empresa.website or "")
            self.entry_codigo_registro.setText(empresa.codigo_registro or "")

    def _guardar(self):
        self.label_error.setText("")
        try:
            self.service.guardar(
                self.entry_nombre.text().strip(),
                self.entry_direccion.text().strip(),
                self.entry_telefono.text().strip(),
                self.entry_email.text().strip(),
                website=self.entry_website.text().strip() or None,
                nit=self.entry_nit.text().strip() or None,
                codigo_registro=self.entry_codigo_registro.text().strip() or None,
            )
        except ValueError as e:
            self.label_error.setText(str(e))
            return
        except Exception as e:
            self.label_error.setText(f"Error al guardar: {e}")
            return
        QMessageBox.information(self, "Éxito", "Información de la empresa guardada correctamente.")
        self.accept()


class ConfiguracionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuración")
        self.resize(480, 360)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        titulo = QLabel("Configuración")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        grilla = QGridLayout()
        grilla.setSpacing(12)

        botones = [
            ("Sucursales", self._abrir_sucursales),
            ("Mi Empresa", self._abrir_empresa),
            ("Permisos", self._abrir_permisos),
            ("Copia de seguridad", self._copia_seguridad),
            ("Restaurar base de datos", self._restaurar_db),
        ]
        for i, (texto, accion) in enumerate(botones):
            btn = QPushButton(texto)
            btn.setObjectName("primario")
            btn.setMinimumHeight(70)
            btn.clicked.connect(accion)
            grilla.addWidget(btn, i // 2, i % 2)

        layout.addLayout(grilla)
        layout.addStretch()

    def _abrir_sucursales(self):
        from Smart_data_syncro.qt_ui.sucursales_window import SucursalesWindow
        self._ventana_sucursales = SucursalesWindow()
        self._ventana_sucursales.show()

    def _abrir_empresa(self):
        dialogo = EmpresaDialog(self)
        dialogo.exec()

    def _abrir_permisos(self):
        from Smart_data_syncro.qt_ui.permisos_window import PermisosWindow
        self._ventana_permisos = PermisosWindow()
        self._ventana_permisos.show()

    def _copia_seguridad(self):
        archivo, _ = QFileDialog.getSaveFileName(self, "Guardar copia de seguridad", "", "SQLite DB (*.db)")
        if not archivo:
            return
        try:
            shutil.copyfile(DB_PATH, archivo)
            QMessageBox.information(self, "Éxito", f"Copia de seguridad guardada en {archivo}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo hacer la copia de seguridad: {e}")

    def _restaurar_db(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar copia de seguridad", "", "SQLite DB (*.db)")
        if not archivo:
            return
        respuesta = QMessageBox.question(
            self, "Confirmar", "Esto reemplaza toda la base de datos actual. ¿Continuar?",
        )
        if respuesta != QMessageBox.Yes:
            return
        try:
            shutil.copyfile(archivo, DB_PATH)
            QMessageBox.information(self, "Éxito", "Base de datos restaurada correctamente. Reiniciá la aplicación.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo restaurar la base de datos: {e}")
