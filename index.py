import sys
from PySide6.QtWidgets import QApplication

from Smart_data_syncro.qt_ui.login_window import LoginWindow
from Smart_data_syncro.qt_ui.main_window import MainWindow


def main():
    # Toda la app ya esta migrada a Qt (login, ventana principal y cada
    # modulo). "Salir" cierra la ventana principal y vuelve a mostrar el
    # login, por eso esto queda en un loop.
    app = QApplication(sys.argv)

    while True:
        login = LoginWindow()
        login.show()
        app.exec()

        if not login.resultado:
            break  # se cerro la ventana de login sin loguearse

        username, permisos_usuario = login.resultado

        main_window = MainWindow(username=username, permisos=permisos_usuario)
        main_window.show()
        app.exec()

        if not main_window.cerrar_sesion_solicitado:
            break  # se cerro la ventana principal (no con "Salir")


if __name__ == "__main__":
    main()
