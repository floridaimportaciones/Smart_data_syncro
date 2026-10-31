"""Pantalla de administracion de permisos (PySide6) -- antes no existia UI
para esto, la tabla permisos solo se podia tocar a mano. Un checkbox por
rol/modulo; tocarlo otorga o revoca el acceso al toque."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QHeaderView, QLabel, QMessageBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from Smart_data_syncro.qt_ui.theme import QSS
from Smart_data_syncro.qt_ui.usuarios_window import ROLES
from Smart_data_syncro.services.permiso_service import MODULOS, PermisoService


class PermisosWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.service = PermisoService()

        self.setWindowTitle("Permisos")
        self.resize(560, 320)
        self.setStyleSheet(QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel("Permisos por rol")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        subtitulo = QLabel("Marcá los módulos a los que cada rol tiene acceso.")
        subtitulo.setObjectName("subtitulo")
        layout.addWidget(subtitulo)

        self.tabla = QTableWidget(len(ROLES), len(MODULOS))
        self.tabla.setHorizontalHeaderLabels(MODULOS)
        self.tabla.setVerticalHeaderLabels(ROLES)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)

        self._cargando = True
        self._cargar()
        self._cargando = False

        self.tabla.itemChanged.connect(self._on_item_changed)

    def _cargar(self):
        for fila, rol in enumerate(ROLES):
            otorgados = self.service.obtener_permisos_por_rol(rol)
            for columna, modulo in enumerate(MODULOS):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                item.setCheckState(Qt.Checked if otorgados.get(modulo) else Qt.Unchecked)
                self.tabla.setItem(fila, columna, item)

    def _on_item_changed(self, item):
        if self._cargando:
            return
        rol = ROLES[item.row()]
        modulo = MODULOS[item.column()]
        try:
            if item.checkState() == Qt.Checked:
                self.service.otorgar(rol, modulo)
            else:
                self.service.revocar(rol, modulo)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar el permiso: {e}")
