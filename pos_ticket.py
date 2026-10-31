"""Generador/impresor de tickets POS, nativo de Qt (QPrinter + QPainter, sin
reportlab). Ancho fijo (rollo termico), alto segun el contenido -- igual que
una impresora termica real: no hay "pagina", es un rollo que se corta al final.

generar_ticket_pdf() guarda un PDF (para archivo/regenerar factura despues).
imprimir_ticket() abre el dialogo nativo de Windows para elegir la impresora
(ideal para elegir la termica POS conectada) e imprime directo, sin PDF de por medio.
"""
from PySide6.QtCore import QMarginsF, QPointF, QSizeF
from PySide6.QtGui import QFont, QPageLayout, QPageSize, QPainter
from PySide6.QtPrintSupport import QPrintDialog, QPrinter

ANCHO_MM_DEFAULT = 80
MARGEN_MM = 4
FACTOR_INTERLINEA = 1.4  # alto de linea = tamaño de letra * este factor
TAMANO_ITEM = 7
ALTO_SEPARADOR_MM = 2.5
PT_A_MM = 25.4 / 72


def _armar_comandos(empresa, titulo, encabezado, items, resumen, pie):
    comandos = []
    comandos.append({"tipo": "texto", "texto": empresa.get("nombre") or "Empresa", "size": 11, "negrita": True, "centrado": True})
    for campo in (empresa.get("direccion"), empresa.get("telefono"), empresa.get("email")):
        if campo:
            comandos.append({"tipo": "texto", "texto": str(campo), "size": 7, "negrita": False, "centrado": True})
    if empresa.get("nit"):
        comandos.append({"tipo": "texto", "texto": f"NIT: {empresa['nit']}", "size": 7, "negrita": False, "centrado": True})
    comandos.append({"tipo": "sep"})

    comandos.append({"tipo": "texto", "texto": titulo, "size": 10, "negrita": True, "centrado": True})
    comandos.append({"tipo": "sep"})

    for linea in encabezado:
        comandos.append({"tipo": "texto", "texto": linea, "size": 8, "negrita": False, "centrado": False})
    comandos.append({"tipo": "sep"})

    comandos.append({"tipo": "texto", "texto": "Producto           Cant   Precio    Total", "size": 7, "negrita": True, "centrado": False})
    comandos.append({"tipo": "sep"})
    if items:
        for producto, cantidad, precio, total in items:
            comandos.append({"tipo": "item", "producto": producto, "cantidad": cantidad, "precio": precio, "total": total})
    else:
        comandos.append({"tipo": "texto", "texto": "(sin productos)", "size": 7, "negrita": False, "centrado": False})
    comandos.append({"tipo": "sep"})

    for linea, negrita in resumen:
        comandos.append({"tipo": "texto", "texto": linea, "size": 9 if negrita else 8, "negrita": negrita, "centrado": False})

    if pie:
        comandos.append({"tipo": "sep"})
        for linea in pie:
            comandos.append({"tipo": "texto", "texto": linea, "size": 7, "negrita": False, "centrado": True})

    return comandos


def _alto_cmd_mm(cmd):
    if cmd["tipo"] == "sep":
        return ALTO_SEPARADOR_MM
    size = TAMANO_ITEM if cmd["tipo"] == "item" else cmd["size"]
    return size * FACTOR_INTERLINEA * PT_A_MM


def _texto_derecha(painter, x_derecha_px, y_px, texto):
    # painter.fontMetrics() -- ligado al device real (printer), a diferencia de
    # QFontMetrics(fuente) suelto que usa el DPI de pantalla y descuadra todo.
    ancho = painter.fontMetrics().horizontalAdvance(texto)
    painter.drawText(QPointF(x_derecha_px - ancho, y_px), texto)


def _dibujar(painter, px_por_mm, comandos, ancho_mm, margen_mm):
    def px(valor_mm):
        return valor_mm * px_por_mm

    ancho_util = ancho_mm - 2 * margen_mm
    col_cantidad = margen_mm + 0.56 * ancho_util
    col_precio = margen_mm + 0.76 * ancho_util
    col_total = ancho_mm - margen_mm

    y_mm = 0.0
    for cmd in comandos:
        y_mm += _alto_cmd_mm(cmd)
        y = px(y_mm)
        if cmd["tipo"] == "sep":
            y_linea = y - px(ALTO_SEPARADOR_MM) / 2
            painter.drawLine(QPointF(px(margen_mm), y_linea), QPointF(px(ancho_mm - margen_mm), y_linea))
            continue
        if cmd["tipo"] == "item":
            fuente = QFont("Arial", TAMANO_ITEM)
            painter.setFont(fuente)
            nombre = str(cmd["producto"])
            if len(nombre) > 16:
                nombre = nombre[:15] + "."
            painter.drawText(QPointF(px(margen_mm), y), nombre)
            _texto_derecha(painter, px(col_cantidad), y, str(cmd["cantidad"]))
            _texto_derecha(painter, px(col_precio), y, f"{float(cmd['precio']):,.0f}")
            _texto_derecha(painter, px(col_total), y, f"{float(cmd['total']):,.0f}")
            continue
        fuente = QFont("Arial", cmd["size"])
        fuente.setBold(cmd["negrita"])
        painter.setFont(fuente)
        if cmd["centrado"]:
            ancho_texto = painter.fontMetrics().horizontalAdvance(cmd["texto"])
            x = px(ancho_mm) / 2 - ancho_texto / 2
            painter.drawText(QPointF(x, y), cmd["texto"])
        else:
            painter.drawText(QPointF(px(margen_mm), y), cmd["texto"])


def _configurar_pagina(printer, comandos, ancho_mm, margen_mm):
    alto_mm = sum(_alto_cmd_mm(c) for c in comandos) + 2 * margen_mm
    printer.setPageSize(QPageSize(QSizeF(ancho_mm, alto_mm), QPageSize.Millimeter))
    printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Millimeter)
    return alto_mm


def generar_ticket_pdf(ruta_archivo, empresa, titulo, encabezado, items, resumen, pie=None, ancho_mm=ANCHO_MM_DEFAULT):
    """Guarda el ticket como PDF (para archivo o para regenerar la factura despues)."""
    comandos = _armar_comandos(empresa, titulo, encabezado, items, resumen, pie or [])

    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(ruta_archivo)
    _configurar_pagina(printer, comandos, ancho_mm, MARGEN_MM)

    painter = QPainter(printer)
    px_por_mm = printer.resolution() / 25.4
    _dibujar(painter, px_por_mm, comandos, ancho_mm, MARGEN_MM)
    painter.end()
    return ruta_archivo


def imprimir_ticket(parent_widget, empresa, titulo, encabezado, items, resumen, pie=None, ancho_mm=ANCHO_MM_DEFAULT):
    """Abre el dialogo nativo de Windows para elegir la impresora (la termica
    POS, si hay una instalada) e imprime directo, sin generar un PDF.
    Devuelve True si se envio a imprimir, False si se cancelo el dialogo."""
    comandos = _armar_comandos(empresa, titulo, encabezado, items, resumen, pie or [])

    printer = QPrinter(QPrinter.HighResolution)
    _configurar_pagina(printer, comandos, ancho_mm, MARGEN_MM)

    dialogo = QPrintDialog(printer, parent_widget)
    dialogo.setWindowTitle("Imprimir factura")
    if dialogo.exec() != QPrintDialog.Accepted:
        return False

    painter = QPainter(printer)
    px_por_mm = printer.resolution() / 25.4
    _dibujar(painter, px_por_mm, comandos, ancho_mm, MARGEN_MM)
    painter.end()
    return True
