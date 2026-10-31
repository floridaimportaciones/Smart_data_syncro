"""Lectura de archivos Excel/CSV para importar articulos. Separado de la UI para
que lo pueda usar tanto la ventana Qt como (si hiciera falta) cualquier otro lugar.
Solo lee y normaliza encabezados -- la logica de negocio (crear/actualizar) vive
en ArticuloService.importar_filas.
"""
import os
import csv
import unicodedata

ENCABEZADOS_SOPORTADOS = {
    "articulo": "articulo",
    "articulo nombre": "articulo",
    "nombre": "articulo",
    "producto": "articulo",
    "descripcion": "articulo",
    "detalle": "articulo",

    "precio": "precio",
    "costo": "costo",
    "codigo": "codigo",
    "cod": "codigo",
    "codigo de barras": "codigo",
    "codigo barras": "codigo",
    "sku": "codigo",
    "referencia": "codigo",
    "ean": "codigo",
    "upc": "codigo",

    "stock": "stock",
    "stock minimo": "stock_minimo",
    "stock mínimo": "stock_minimo",
    "stock min": "stock_minimo",
    "sucursal": "sucursal",
}


def _norm_texto(s):
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    s = s.strip()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return s.lower()


def leer_filas_articulos(file_path):
    """Lee un .xlsx/.xlsm o .csv y devuelve una lista de dicts con las claves
    conocidas (articulo, precio, costo, codigo, stock, stock_minimo, sucursal),
    valores crudos sin convertir todavia. Encabezados no sensibles a acentos/mayusculas."""
    ext = os.path.splitext(file_path)[1].lower()
    rows = []
    headers_map = {}

    if ext in (".xlsx", ".xlsm"):
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        ws = wb.active
        primero = True
        for row in ws.iter_rows(values_only=True):
            if primero:
                for idx, h in enumerate(row or []):
                    key = _norm_texto(h)
                    if key in ENCABEZADOS_SOPORTADOS:
                        headers_map[idx] = ENCABEZADOS_SOPORTADOS[key]
                primero = False
                continue
            if not headers_map:
                break
            rd = {}
            for idx, val in enumerate(row or []):
                if idx in headers_map:
                    rd[headers_map[idx]] = val
            if any(v not in (None, "") for v in rd.values()):
                rows.append(rd)
    else:
        with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
            sample = f.read(2048)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            except Exception:
                dialect = csv.excel
            reader = csv.reader(f, dialect)
            try:
                headers = next(reader)
            except StopIteration:
                return []
            for idx, h in enumerate(headers):
                key = _norm_texto(h)
                if key in ENCABEZADOS_SOPORTADOS:
                    headers_map[idx] = ENCABEZADOS_SOPORTADOS[key]
            for row in reader:
                rd = {}
                for idx, val in enumerate(row):
                    if idx in headers_map:
                        rd[headers_map[idx]] = val
                if any(v not in (None, "") for v in rd.values()):
                    rows.append(rd)

    return rows
