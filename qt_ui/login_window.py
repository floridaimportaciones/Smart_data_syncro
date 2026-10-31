"""Pantalla de login en PySide6 -- primera pantalla del nuevo diseno, reemplaza login.py.

Uso: se corre su propio QApplication, el resultado de la autenticacion queda en
self.resultado = (username, permisos_dict) si el usuario se logueo, o None si
cerro la ventana sin loguearse. index.py arranca esto antes de levantar la app
Tkinter existente.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame,
    QComboBox, QMessageBox, QStackedWidget,
)

from Smart_data_syncro.services.usuario_service import UsuarioService
from Smart_data_syncro.services.empresa_service import EmpresaService
import Smart_data_syncro.permisos as permisos
from Smart_data_syncro.qt_ui.theme import QSS


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.usuario_service = UsuarioService()
        self.empresa_service = EmpresaService()
        self.resultado = None

        self.setWindowTitle("Smart Data Syncro — Iniciar sesión")
        self.resize(420, 520)
        self.setStyleSheet(QSS)

        self.stack = QStackedWidget()
        layout_raiz = QVBoxLayout(self)
        layout_raiz.addWidget(self.stack)

        self.pagina_login = self._construir_login()
        self.pagina_registro = self._construir_registro()
        self.stack.addWidget(self.pagina_login)
        self.stack.addWidget(self.pagina_registro)
        self.stack.setCurrentWidget(self.pagina_login)

    def _tarjeta(self):
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        tarjeta.setFixedWidth(340)
        return tarjeta

    def _construir_login(self):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setAlignment(Qt.AlignCenter)

        tarjeta = self._tarjeta()
        v = QVBoxLayout(tarjeta)
        v.setContentsMargins(28, 28, 28, 28)
        v.setSpacing(10)

        titulo = QLabel("Smart Data Syncro")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignCenter)
        subtitulo = QLabel("Iniciá sesión para continuar")
        subtitulo.setObjectName("subtitulo")
        subtitulo.setAlignment(Qt.AlignCenter)

        self.entry_usuario = QLineEdit()
        self.entry_usuario.setPlaceholderText("Usuario")

        self.entry_password = QLineEdit()
        self.entry_password.setPlaceholderText("Contraseña")
        self.entry_password.setEchoMode(QLineEdit.Password)
        self.entry_password.returnPressed.connect(self._intentar_login)

        self.label_error = QLabel("")
        self.label_error.setObjectName("error")
        self.label_error.setAlignment(Qt.AlignCenter)
        self.label_error.setWordWrap(True)

        btn_login = QPushButton("Iniciar sesión")
        btn_login.setObjectName("primario")
        btn_login.clicked.connect(self._intentar_login)

        btn_registro = QPushButton("¿No tenés cuenta? Registrate")
        btn_registro.setObjectName("enlace")
        btn_registro.clicked.connect(lambda: self.stack.setCurrentWidget(self.pagina_registro))

        v.addWidget(titulo)
        v.addWidget(subtitulo)
        v.addSpacing(12)
        v.addWidget(self.entry_usuario)
        v.addWidget(self.entry_password)
        v.addWidget(self.label_error)
        v.addSpacing(4)
        v.addWidget(btn_login)
        v.addWidget(btn_registro, alignment=Qt.AlignCenter)

        layout.addWidget(tarjeta, alignment=Qt.AlignCenter)
        return pagina

    def _construir_registro(self):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setAlignment(Qt.AlignCenter)

        tarjeta = self._tarjeta()
        v = QVBoxLayout(tarjeta)
        v.setContentsMargins(28, 28, 28, 28)
        v.setSpacing(10)

        titulo = QLabel("Crear cuenta")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignCenter)

        self.reg_usuario = QLineEdit()
        self.reg_usuario.setPlaceholderText("Usuario")
        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText("Contraseña (mínimo 6 caracteres)")
        self.reg_password.setEchoMode(QLineEdit.Password)
        self.combo_rol = QComboBox()
        self.combo_rol.addItems(["Cajero", "Administrador"])
        self.reg_codigo = QLineEdit()
        self.reg_codigo.setPlaceholderText("Código de registro")
        self.reg_codigo.setEchoMode(QLineEdit.Password)

        self.label_error_registro = QLabel("")
        self.label_error_registro.setObjectName("error")
        self.label_error_registro.setAlignment(Qt.AlignCenter)
        self.label_error_registro.setWordWrap(True)

        btn_crear = QPushButton("Crear cuenta")
        btn_crear.setObjectName("primario")
        btn_crear.clicked.connect(self._intentar_registro)

        btn_volver = QPushButton("Ya tengo cuenta, volver")
        btn_volver.setObjectName("enlace")
        btn_volver.clicked.connect(lambda: self.stack.setCurrentWidget(self.pagina_login))

        v.addWidget(titulo)
        v.addSpacing(8)
        v.addWidget(self.reg_usuario)
        v.addWidget(self.reg_password)
        v.addWidget(self.combo_rol)
        v.addWidget(self.reg_codigo)
        v.addWidget(self.label_error_registro)
        v.addSpacing(4)
        v.addWidget(btn_crear)
        v.addWidget(btn_volver, alignment=Qt.AlignCenter)

        layout.addWidget(tarjeta, alignment=Qt.AlignCenter)
        return pagina

    def _intentar_login(self):
        usuario = self.entry_usuario.text().strip()
        clave = self.entry_password.text()
        self.label_error.setText("")

        if not usuario or not clave:
            self.label_error.setText("Completá usuario y contraseña.")
            return

        try:
            u = self.usuario_service.obtener_por_username(usuario)
        except Exception as e:
            self.label_error.setText(f"Error de conexión: {e}")
            return

        if not u:
            self.label_error.setText("Usuario no encontrado.")
            self.entry_password.clear()
            return

        if clave != u.password:
            self.label_error.setText("Usuario o contraseña incorrectos.")
            self.entry_password.clear()
            return

        rol = u.rol
        if rol.lower() in ["admin", "administrador"]:
            rol = "Administrador"
        elif rol.lower() in ["cajero", "caja"]:
            rol = "Cajero"

        permisos_usuario = permisos.obtener_permisos_por_rol(rol)
        if not permisos_usuario or not any(permisos_usuario.values()):
            self.label_error.setText("El rol no tiene permisos definidos. Contactá a un administrador.")
            return

        self.resultado = (usuario, permisos_usuario)
        self.close()

    def _intentar_registro(self):
        usuario = self.reg_usuario.text().strip()
        clave = self.reg_password.text()
        codigo = self.reg_codigo.text().strip()
        rol = self.combo_rol.currentText()
        self.label_error_registro.setText("")

        if not usuario or not clave:
            self.label_error_registro.setText("Completá usuario y contraseña.")
            return
        if len(clave) < 6:
            self.label_error_registro.setText("La contraseña debe tener al menos 6 caracteres.")
            return

        try:
            if not self.empresa_service.validar_codigo_registro(codigo):
                self.label_error_registro.setText("Código de registro incorrecto.")
                return
        except ValueError as e:
            self.label_error_registro.setText(str(e))
            return
        except Exception as e:
            self.label_error_registro.setText(f"Error de conexión: {e}")
            return

        try:
            self.usuario_service.crear(usuario, clave, rol, sucursal=None)
        except ValueError as e:
            self.label_error_registro.setText(str(e))
            return
        except Exception as e:
            self.label_error_registro.setText(f"Error al crear la cuenta: {e}")
            return

        QMessageBox.information(self, "Cuenta creada", "Tu cuenta fue creada correctamente. Iniciá sesión.")
        self.reg_usuario.clear()
        self.reg_password.clear()
        self.reg_codigo.clear()
        self.stack.setCurrentWidget(self.pagina_login)
        self.entry_usuario.setText(usuario)
