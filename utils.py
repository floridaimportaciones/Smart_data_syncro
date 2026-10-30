import sys
import os
from PIL import Image

def rutas(ruta):
    try:
        rutabase = sys._MEIPASS
    except Exception:
        rutabase = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(rutabase, ruta)

DB_PATH = rutas("database.db")

def imagen_segura(ruta, tamano=(30, 30)):
    try:
        return Image.open(ruta)
    except Exception:
        return Image.new("RGBA", tamano, (0, 0, 0, 0))
