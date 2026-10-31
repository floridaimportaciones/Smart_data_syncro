"""Ventana principal (PySide6) -- reemplaza manager.py + container.py (Tkinter).
Barra de botones por modulo (segun permisos) + Salir. Cada modulo se abre en
una ventana aparte: se bloquea con un QEventLoop local (no QApplication.exec()
global) atado al cierre de esa ventana puntual, ya que esta ventana principal
se queda abierta de fondo -- ya no hay Tkinter corriendo detras.
"""
import os

from PySide6.QtCore import QEventLoop, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from Smart_data_syncro.qt_ui.theme import QSS
from Smart_data_syncro.utils import rutas

MODULOS = [
    ("Ventas", "imagenes/btnventas.png", "_abrir_ventas"),
    ("Inventario", "imagenes/btninventario.png", "_abrir_inventario"),
    ("Separados", "imagenes/separado.png", "_abrir_separados"),
    ("Clientes", "imagenes/btnclientes.png", "_abrir_clientes"),
    ("Reportes", "imagenes/btnreportes.png", "_abrir_reportes"),
    ("Configuracion", "imagenes/btnconfiguraciones.png", "_abrir_configuracion"),
    ("Usuarios", "imagenes/btnusuarios.png", "_abrir_usuarios"),
]


class MainWindow(QWidget):
    def __init__(self, username=None, permisos=None):
        super().__init__()
        self.username = username
        self.permisos = permisos or {}
        self.cerrar_sesion_solicitado = False

        self.setWindowTitle("Smart Data Syncro")
        self.resize(1100, 650)
        self.setStyleSheet(QSS)
        icono = rutas("icono.ico")
        if os.path.exists(icono):
            self.setWindowIcon(QIcon(icono))

        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        barra = QHBoxLayout()
        barra.setContentsMargins(16, 12, 16, 12)
        barra.setSpacing(8)

        for nombre, icono, metodo in MODULOS:
            if not self.permisos.get(nombre, False):
                continue
            btn = QPushButton(nombre)
            ruta_icono = rutas(icono)
            if os.path.exists(ruta_icono):
                btn.setIcon(QIcon(ruta_icono))
                btn.setIconSize(QSize(24, 24))
            btn.clicked.connect(getattr(self, metodo))
            barra.addWidget(btn)

        barra.addStretch()

        if self.username:
            label_usuario = QLabel(self.username)
            label_usuario.setObjectName("subtitulo")
            barra.addWidget(label_usuario)

        btn_salir = QPushButton("Salir")
        ruta_logout = rutas("imagenes/logout.png")
        if os.path.exists(ruta_logout):
            btn_salir.setIcon(QIcon(ruta_logout))
        btn_salir.clicked.connect(self._cerrar_sesion)
        barra.addWidget(btn_salir)

        layout.addLayout(barra)

        if not any(self.permisos.get(nombre, False) for nombre, _, _ in MODULOS):
            aviso = QLabel("No tenés acceso a ningún módulo. Contactá al administrador.")
            aviso.setObjectName("error")
            aviso.setAlignment(Qt.AlignCenter)
            layout.addWidget(aviso, 1)
        else:
            layout.addStretch()

    def _cerrar_sesion(self):
        self.cerrar_sesion_solicitado = True
        self.close()

    def _abrir_modal(self, ventana):
        ventana.setAttribute(Qt.WA_DeleteOnClose)
        loop = QEventLoop()
        ventana.destroyed.connect(loop.quit)
        ventana.show()
        loop.exec()

    def _abrir_ventas(self):
        from Smart_data_syncro.qt_ui.ventas_window import VentasWindow
        self._abrir_modal(VentasWindow(username=self.username))

    def _abrir_inventario(self):
        from Smart_data_syncro.qt_ui.inventario_window import InventarioWindow
        self._abrir_modal(InventarioWindow())

    def _abrir_separados(self):
        from Smart_data_syncro.qt_ui.separados_window import SeparadosWindow
        self._abrir_modal(SeparadosWindow(username=self.username))

    def _abrir_clientes(self):
        from Smart_data_syncro.qt_ui.clientes_window import ClientesWindow
        self._abrir_modal(ClientesWindow())

    def _abrir_reportes(self):
        from Smart_data_syncro.qt_ui.reportes_window import ReportesWindow
        self._abrir_modal(ReportesWindow())

    def _abrir_configuracion(self):
        from Smart_data_syncro.qt_ui.configuracion_window import ConfiguracionWindow
        self._abrir_modal(ConfiguracionWindow())

    def _abrir_usuarios(self):
        from Smart_data_syncro.qt_ui.usuarios_window import UsuariosWindow
        self._abrir_modal(UsuariosWindow())
