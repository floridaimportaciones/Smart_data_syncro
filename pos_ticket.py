"""Generador de tickets POS: ancho fijo (rollo termico), alto segun el contenido.
Lo usan ventas.py y separados.py para no duplicar el dibujo de la factura."""
from reportlab.lib.units import mm as MM
from reportlab.pdfgen import canvas

ANCHO_MM_DEFAULT = 80
MARGEN_MM = 4
FACTOR_INTERLINEA = 1.4  # alto de linea = tamaño de letra * este factor, evita que el texto pise la linea de abajo
TAMANO_ITEM = 7
ALTO_SEPARADOR_MM = 2.5


def _cmd_texto(texto, size=8, negrita=False, centrado=False):
    return {"tipo": "texto", "texto": texto, "size": size, "negrita": negrita, "centrado": centrado}


def _cmd_item(producto, cantidad, precio, total):
    return {"tipo": "item", "producto": producto, "cantidad": cantidad, "precio": precio, "total": total}


def _cmd_sep():
    return {"tipo": "sep"}


def generar_ticket_pdf(ruta_archivo, empresa, titulo, encabezado, items, resumen, pie=None, ancho_mm=ANCHO_MM_DEFAULT):
    """Genera un ticket POS y lo guarda en ruta_archivo. Ancho fijo, alto calculado
    segun el contenido (como una impresora termica real: no hay "pagina", es un rollo).

    empresa: dict con nombre/direccion/telefono/email
    titulo: texto del encabezado, ej "FACTURA DE VENTA"
    encabezado: lista de strings ya armados, ej ["Factura: 123", "Fecha: ...", "Cliente: ..."]
    items: lista de tuplas (producto, cantidad, precio, total)
    resumen: lista de (texto, negrita) ya armados, ej [("Total: $1.000", True)]
    pie: lista de strings centrados al final (opcional)
    """
    pie = pie or []
    ancho = ancho_mm * MM
    margen = MARGEN_MM * MM
    ancho_util = ancho - 2 * margen

    comandos = []
    comandos.append(_cmd_texto(empresa.get("nombre") or "Empresa", size=11, negrita=True, centrado=True))
    for campo in (empresa.get("direccion"), empresa.get("telefono"), empresa.get("email")):
        if campo:
            comandos.append(_cmd_texto(str(campo), size=7, centrado=True))
    if empresa.get("nit"):
        comandos.append(_cmd_texto(f"NIT: {empresa['nit']}", size=7, centrado=True))
    comandos.append(_cmd_sep())

    comandos.append(_cmd_texto(titulo, size=10, negrita=True, centrado=True))
    comandos.append(_cmd_sep())

    for linea in encabezado:
        comandos.append(_cmd_texto(linea, size=8))
    comandos.append(_cmd_sep())

    comandos.append(_cmd_texto("Producto           Cant   Precio    Total", size=7, negrita=True))
    comandos.append(_cmd_sep())
    if items:
        for producto, cantidad, precio, total in items:
            comandos.append(_cmd_item(producto, cantidad, precio, total))
    else:
        comandos.append(_cmd_texto("(sin productos)", size=7))
    comandos.append(_cmd_sep())

    for linea, negrita in resumen:
        comandos.append(_cmd_texto(linea, size=9 if negrita else 8, negrita=negrita))

    if pie:
        comandos.append(_cmd_sep())
        for linea in pie:
            comandos.append(_cmd_texto(linea, size=7, centrado=True))

    def alto_cmd(cmd):
        # Alto de linea proporcional al tamaño de letra, para que el texto nunca pise
        # la linea separadora ni la fila de abajo (en puntos, mismo que el tamaño de fuente).
        if cmd["tipo"] == "sep":
            return ALTO_SEPARADOR_MM * MM
        if cmd["tipo"] == "item":
            return TAMANO_ITEM * FACTOR_INTERLINEA
        return cmd["size"] * FACTOR_INTERLINEA

    alto_contenido = sum(alto_cmd(cmd) for cmd in comandos)
    alto = alto_contenido + 2 * margen

    c = canvas.Canvas(ruta_archivo, pagesize=(ancho, alto))
    y = alto - margen

    col_cantidad = margen + 0.56 * ancho_util
    col_precio = margen + 0.76 * ancho_util
    col_total = ancho - margen

    for cmd in comandos:
        y -= alto_cmd(cmd)
        if cmd["tipo"] == "sep":
            c.setLineWidth(0.5)
            c.line(margen, y + ALTO_SEPARADOR_MM * MM / 2, ancho - margen, y + ALTO_SEPARADOR_MM * MM / 2)
            continue
        if cmd["tipo"] == "item":
            nombre = str(cmd["producto"])
            if len(nombre) > 16:
                nombre = nombre[:15] + "."
            c.setFont("Helvetica", TAMANO_ITEM)
            c.drawString(margen, y, nombre)
            c.drawRightString(col_cantidad, y, str(cmd["cantidad"]))
            c.drawRightString(col_precio, y, f"{float(cmd['precio']):,.0f}")
            c.drawRightString(col_total, y, f"{float(cmd['total']):,.0f}")
            continue
        c.setFont("Helvetica-Bold" if cmd["negrita"] else "Helvetica", cmd["size"])
        if cmd["centrado"]:
            c.drawCentredString(ancho / 2, y, cmd["texto"])
        else:
            c.drawString(margen, y, cmd["texto"])

    c.save()
    return ruta_archivo
