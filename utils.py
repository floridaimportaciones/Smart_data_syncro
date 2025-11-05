import sys
import os

def rutas(ruta):
    try:
        rutabase = sys._MEIPASS
    except Exception:
        rutabase = os.path.abspath(".")
    return os.path.join(rutabase, ruta)
