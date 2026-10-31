"""Estilo compartido para las pantallas Qt nuevas. Cada pantalla que migremos
de Tkinter a PySide6 importa este QSS para que todas se vean consistentes."""

COLOR_PRIMARIO = "#2F6FED"
COLOR_PRIMARIO_HOVER = "#2558C4"
COLOR_FONDO = "#1F2937"
COLOR_TARJETA = "#1F2937"
COLOR_TEXTO = "#FFFFFF"
COLOR_TEXTO_SUAVE = "#6B7280"
COLOR_BORDE = "#E2E8F0"
COLOR_ERROR = "#DC2626"

QSS = f"""
QWidget {{
    background-color: {COLOR_FONDO};
    font-family: "Segoe UI";
    color: {COLOR_TEXTO};
    font-size: 13px;
}}
QFrame#tarjeta {{
    background-color: {COLOR_TARJETA};
    border-radius: 16px;
    border: 1px solid {COLOR_BORDE};
}}
QLabel {{
    background: transparent;
}}
QLabel#titulo {{
    font-size: 22px;
    font-weight: 600;
}}
QLabel#subtitulo {{
    font-size: 13px;
    color: {COLOR_TEXTO_SUAVE};
}}
QLineEdit, QComboBox {{
    border: 1px solid {COLOR_BORDE};
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 13px;
    background-color: {COLOR_TARJETA};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {COLOR_PRIMARIO};
}}
QPushButton#primario {{
    background-color: {COLOR_PRIMARIO};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 11px;
    font-size: 14px;
    font-weight: 600;
}}
QPushButton#primario:hover {{
    background-color: {COLOR_PRIMARIO_HOVER};
}}
QPushButton#enlace {{
    background: transparent;
    border: none;
    color: {COLOR_PRIMARIO};
    font-size: 12px;
}}
QPushButton#enlace:hover {{
    text-decoration: underline;
}}
QLabel#error {{
    color: {COLOR_ERROR};
    font-size: 12px;
}}
"""
