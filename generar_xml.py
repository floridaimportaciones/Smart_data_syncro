def generar_xml_ubl21(venta_data, cliente_data, productos, empresa_data, num_factura, fecha, hora):
    """
    Genera un XML mínimo UBL 2.1 para facturación electrónica DIAN/FacturaTech.
    Args:
        venta_data: dict con info de la venta (total, descuento, etc)
        cliente_data: dict con info del cliente
        productos: lista de dicts con info de cada producto
        empresa_data: dict con info de la empresa
        num_factura: número de factura
        fecha: fecha de la venta (YYYY-MM-DD)
        hora: hora de la venta (HH:MM:SS)
    Returns:
        xml_str: XML como string
    """
    from lxml import etree
    import uuid
    NSMAP = {
        None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
    }
    root = etree.Element("Invoice", nsmap=NSMAP)
    cbc = "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}"
    cac = "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}"
    ext = "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}"

    # UBLExtensions (obligatorio)
    ubl_exts = etree.SubElement(root, ext+"UBLExtensions")
    ubl_ext = etree.SubElement(ubl_exts, ext+"UBLExtension")
    etree.SubElement(ubl_ext, ext+"ExtensionContent")

    # CustomizationID y ProfileID (obligatorio DIAN)
    etree.SubElement(root, cbc+"CustomizationID").text = "10"
    etree.SubElement(root, cbc+"ProfileID").text = "1"
    # ProfileExecutionID (obligatorio DIAN)
    etree.SubElement(root, cbc+"ProfileExecutionID").text = "2"
    # Note (opcional, pero a veces requerido)
    etree.SubElement(root, cbc+"Note").text = "Factura generada por sistema de ventas."
    # AccountingCost (opcional, pero a veces requerido)
    etree.SubElement(root, cbc+"AccountingCost").text = "Venta mostrador"
    # Referencia adicional de documento (obligatorio DIAN)
    add_doc_ref = etree.SubElement(root, cac+"AdditionalDocumentReference")
    etree.SubElement(add_doc_ref, cbc+"ID").text = str(num_factura)
    etree.SubElement(add_doc_ref, cbc+"DocumentType").text = "Factura"
    # ID de la factura
    etree.SubElement(root, cbc+"ID").text = str(num_factura)
    # UUID (obligatorio, dummy)
    etree.SubElement(root, cbc+"UUID").text = str(uuid.uuid4())
    # Tipo de factura (01 = factura de venta)
    etree.SubElement(root, cbc+"InvoiceTypeCode").text = "01"
    # Fecha y hora
    etree.SubElement(root, cbc+"IssueDate").text = str(fecha)
    etree.SubElement(root, cbc+"IssueTime").text = str(hora)
    # Moneda
    moneda = str(venta_data.get("moneda", "COP"))
    etree.SubElement(root, cbc+"DocumentCurrencyCode").text = moneda
    # Cantidad de líneas: se agrega después de los InvoiceLine para cumplir la regla FAD16

    # Firma digital (estructura dummy pero más completa)
    signature = etree.SubElement(root, cac+"Signature")
    etree.SubElement(signature, cbc+"ID").text = "IDSign"
    signatory_party = etree.SubElement(signature, cac+"SignatoryParty")
    party_ident = etree.SubElement(signatory_party, cac+"PartyIdentification")
    etree.SubElement(party_ident, cbc+"ID").text = str(empresa_data.get("nit", ""))
    party_name_sig = etree.SubElement(signatory_party, cac+"PartyName")
    etree.SubElement(party_name_sig, cbc+"Name").text = str(empresa_data.get("nombre", ""))
    digital_sig = etree.SubElement(signature, cac+"DigitalSignatureAttachment")
    ext_ref = etree.SubElement(digital_sig, cac+"ExternalReference")
    etree.SubElement(ext_ref, cbc+"URI").text = "#signature"

    # Emisor (empresa) - estructura UBL/DIAN
    acc_party = etree.SubElement(root, cac+"AccountingSupplierParty")
    party = etree.SubElement(acc_party, cac+"Party")
    party_ident = etree.SubElement(party, cac+"PartyIdentification")
    etree.SubElement(party_ident, cbc+"ID").text = str(empresa_data.get("nit", ""))
    party_name = etree.SubElement(party, cac+"PartyName")
    etree.SubElement(party_name, cbc+"Name").text = str(empresa_data.get("nombre", ""))
    party_legal = etree.SubElement(party, cac+"PartyLegalEntity")
    etree.SubElement(party_legal, cbc+"RegistrationName").text = str(empresa_data.get("nombre", ""))
    etree.SubElement(party_legal, cbc+"CompanyID", schemeID="31").text = str(empresa_data.get("nit", ""))
    # NIT emisor en PartyTaxScheme
    party_tax = etree.SubElement(party, cac+"PartyTaxScheme")
    etree.SubElement(party_tax, cbc+"CompanyID", schemeID="31").text = str(empresa_data.get("nit", ""))
    etree.SubElement(party_tax, cbc+"TaxLevelCode").text = "O-99"
    tax_scheme = etree.SubElement(party_tax, cac+"TaxScheme")
    etree.SubElement(tax_scheme, cbc+"ID").text = "01"
    etree.SubElement(tax_scheme, cbc+"Name").text = "IVA"

    # Adquiriente (cliente) - estructura UBL/DIAN
    acc_party2 = etree.SubElement(root, cac+"AccountingCustomerParty")
    party2 = etree.SubElement(acc_party2, cac+"Party")
    party_ident2 = etree.SubElement(party2, cac+"PartyIdentification")
    etree.SubElement(party_ident2, cbc+"ID").text = str(cliente_data.get("nit", ""))
    party_name2 = etree.SubElement(party2, cac+"PartyName")
    etree.SubElement(party_name2, cbc+"Name").text = str(cliente_data.get("nombre", ""))
    party_legal2 = etree.SubElement(party2, cac+"PartyLegalEntity")
    etree.SubElement(party_legal2, cbc+"RegistrationName").text = str(cliente_data.get("nombre", ""))
    etree.SubElement(party_legal2, cbc+"CompanyID", schemeID="31").text = str(cliente_data.get("nit", ""))
    # NIT cliente en PartyTaxScheme
    party_tax2 = etree.SubElement(party2, cac+"PartyTaxScheme")
    etree.SubElement(party_tax2, cbc+"CompanyID", schemeID="31").text = str(cliente_data.get("nit", ""))
    etree.SubElement(party_tax2, cbc+"TaxLevelCode").text = "O-99"
    tax_scheme2 = etree.SubElement(party_tax2, cac+"TaxScheme")
    etree.SubElement(tax_scheme2, cbc+"ID").text = "01"
    etree.SubElement(tax_scheme2, cbc+"Name").text = "IVA"

    # Dirección del emisor (empresa)
    address = etree.SubElement(party, cac+"PostalAddress")
    etree.SubElement(address, cbc+"ID").text = empresa_data.get("codigo_postal", "170001")
    etree.SubElement(address, cbc+"CityName").text = empresa_data.get("ciudad", "MANIZALES")
    etree.SubElement(address, cbc+"CountrySubentity").text = empresa_data.get("departamento", "CALDAS")
    etree.SubElement(address, cbc+"CountrySubentityCode").text = empresa_data.get("codigo_departamento", "17")
    etree.SubElement(address, cbc+"AddressLine").text = empresa_data.get("direccion", "CR 43 A 15 SUR 15 ED XEROX OF 802")
    country = etree.SubElement(address, cac+"Country")
    etree.SubElement(country, cbc+"IdentificationCode").text = empresa_data.get("codigo_pais", "CO")

    # Dirección del adquiriente (cliente)
    address2 = etree.SubElement(party2, cac+"PostalAddress")
    etree.SubElement(address2, cbc+"ID").text = str(cliente_data.get("codigo_postal", "170001"))
    etree.SubElement(address2, cbc+"CityName").text = str(cliente_data.get("ciudad", "MANIZALES"))
    etree.SubElement(address2, cbc+"CountrySubentity").text = str(cliente_data.get("departamento", "CALDAS"))
    etree.SubElement(address2, cbc+"CountrySubentityCode").text = str(cliente_data.get("codigo_departamento", "17"))
    etree.SubElement(address2, cbc+"AddressLine").text = str(cliente_data.get("direccion", "CL 1 # 1-1"))
    country2 = etree.SubElement(address2, cac+"Country")
    etree.SubElement(country2, cbc+"IdentificationCode").text = str(cliente_data.get("codigo_pais", "CO"))

    # Medios de pago (obligatorio DIAN)
    payment_means = etree.SubElement(root, cac+"PaymentMeans")
    etree.SubElement(payment_means, cbc+"PaymentMeansCode").text = "10"  # 10 = Efectivo
    etree.SubElement(payment_means, cbc+"PaymentID").text = str(num_factura)

    # Condiciones de pago (obligatorio DIAN)
    payment_terms = etree.SubElement(root, cac+"PaymentTerms")
    etree.SubElement(payment_terms, cbc+"ID").text = "1"
    etree.SubElement(payment_terms, cbc+"PaymentMeansID").text = "Contado"

    # Impuestos (dummy IVA 19%)
    # Calcular suma base imponible (sin IVA) y suma IVA
    suma_base_imponible = 0.0
    suma_iva = 0.0
    for prod in productos:
        cantidad = float(prod.get("cantidad", 1))
        precio_unit = float(prod.get("precio", 0))
        valor_total_linea = cantidad * precio_unit
        base_imponible = round(valor_total_linea / 1.19, 2)
        iva_linea = round(valor_total_linea - base_imponible, 2)
        suma_base_imponible += base_imponible
        suma_iva += iva_linea

    tax_total = etree.SubElement(root, cac+"TaxTotal")
    etree.SubElement(tax_total, cbc+"TaxAmount", currencyID=moneda).text = f"{suma_iva:.2f}"
    tax_subtotal = etree.SubElement(tax_total, cac+"TaxSubtotal")
    etree.SubElement(tax_subtotal, cbc+"TaxableAmount", currencyID=moneda).text = f"{suma_base_imponible:.2f}"
    etree.SubElement(tax_subtotal, cbc+"TaxAmount", currencyID=moneda).text = f"{suma_iva:.2f}"
    tax_category = etree.SubElement(tax_subtotal, cac+"TaxCategory")
    tax_scheme = etree.SubElement(tax_category, cac+"TaxScheme")
    etree.SubElement(tax_scheme, cbc+"ID").text = "01"
    etree.SubElement(tax_scheme, cbc+"Name").text = "IVA"
    etree.SubElement(tax_scheme, cbc+"TaxTypeCode").text = "01"

    # Totales
    legal_monetary = etree.SubElement(root, cac+"LegalMonetaryTotal")
    total_con_iva = suma_base_imponible + suma_iva
    etree.SubElement(legal_monetary, cbc+"LineExtensionAmount", currencyID=moneda).text = f"{total_con_iva:.2f}"
    # Si no hay base imponible, TOT_3 debe ser 0.00
    tax_exclusive = suma_base_imponible if suma_base_imponible > 0 else 0.0
    etree.SubElement(legal_monetary, cbc+"TaxExclusiveAmount", currencyID=moneda).text = f"{tax_exclusive:.2f}"
    etree.SubElement(legal_monetary, cbc+"TaxInclusiveAmount", currencyID=moneda).text = f"{total_con_iva:.2f}"
    etree.SubElement(legal_monetary, cbc+"PayableAmount", currencyID=moneda).text = f"{total_con_iva:.2f}"

    # Detalle de productos (líneas)

    for idx, prod in enumerate(productos, 1):
        inv_line = etree.SubElement(root, cac+"InvoiceLine")
        etree.SubElement(inv_line, cbc+"ID").text = str(idx)
        etree.SubElement(inv_line, cbc+"InvoicedQuantity").text = str(prod.get("cantidad", 1))
        etree.SubElement(inv_line, cbc+"LineExtensionAmount", currencyID=moneda).text = str(prod.get("precio", 0))
        item = etree.SubElement(inv_line, cac+"Item")
        etree.SubElement(item, cbc+"Description").text = str(prod.get("nombre", ""))
        price = etree.SubElement(inv_line, cac+"Price")
        etree.SubElement(price, cbc+"PriceAmount", currencyID=moneda).text = str(prod.get("precio", 0))

    # Cantidad de líneas: debe ir después de los InvoiceLine
    etree.SubElement(root, cbc+"LineCountNumeric").text = str(len(productos))

    xml_str = etree.tostring(root, pretty_print=True, encoding="utf-8").decode("utf-8")
    # Guardar el XML en una carpeta aparte
    import os
    xml_dir = os.path.abspath('xml_facturas')
    if not os.path.exists(xml_dir):
        os.makedirs(xml_dir)
    xml_filename = f"factura_ubl21_{num_factura}.xml"
    xml_path = os.path.join(xml_dir, xml_filename)
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    try:
        from tkinter import messagebox
        messagebox.showinfo("XML UBL 2.1 guardado", f"El archivo XML UBL 2.1 se guardó en:\n{xml_path}")
    except Exception:
        pass
    return xml_str
def generar_xml_factura_dian(venta_data, cliente_data, productos, empresa_data, num_factura, fecha, hora):
    """
    Genera un XML compatible con DIAN/FacturaTech para una venta.
    Args:
        venta_data: dict con info de la venta (total, descuento, etc)
        cliente_data: dict con info del cliente
        productos: lista de dicts con info de cada producto
        empresa_data: dict con info de la empresa
        num_factura: número de factura
        fecha: fecha de la venta
        hora: hora de la venta
    Returns:
        xml_str: XML como string
    """
    from lxml import etree
    root = etree.Element("FACTURA")
    # ...resto del código...
    # (Mover LineCountNumeric al final, después de los ITE)
    # ENC
    enc = etree.SubElement(root, "ENC")
    etree.SubElement(enc, "ENC_1").text = "INVOIC"
    etree.SubElement(enc, "ENC_2").text = str(empresa_data.get("nit", ""))
    etree.SubElement(enc, "ENC_3").text = str(cliente_data.get("nit", ""))
    etree.SubElement(enc, "ENC_4").text = "UBL 2.1"
    etree.SubElement(enc, "ENC_5").text = "DIAN 2.1"
    # ENC_6 debe ser el folio, dentro del rango 33621 a 33720
    folio_inicio = 33621
    folio_final = 33720
    rango_total = folio_final - folio_inicio + 1  # 100 números disponibles
    
    try:
        num_factura_int = int(num_factura)
        # Calcular el folio basado en el número de factura usando módulo para que sea cíclico
        folio_offset = (num_factura_int - 1) % rango_total  # -1 porque empezamos desde factura 1
        folio = folio_inicio + folio_offset
    except Exception:
        folio = folio_inicio
    
    etree.SubElement(enc, "ENC_6").text = f"TCFA{folio}"
    etree.SubElement(enc, "ENC_9").text = "01"
    etree.SubElement(enc, "ENC_10").text = str(venta_data.get("moneda", "COP"))
    etree.SubElement(enc, "ENC_15").text = str(len(productos))
    etree.SubElement(enc, "ENC_20").text = "2"
    etree.SubElement(enc, "ENC_21").text = "10"

    emi = etree.SubElement(root, "EMI")
    etree.SubElement(emi, "EMI_1").text = "1"  
    etree.SubElement(emi, "EMI_2").text = "901143311"  
    etree.SubElement(emi, "EMI_3").text = "31"  # Tipo de organización
    etree.SubElement(emi, "EMI_4").text = "48"  
    etree.SubElement(emi, "EMI_6").text = "FACTURATECH SA. DE CV"  # Razón social
    etree.SubElement(emi, "EMI_7").text = "FACTURATECH SA. DE CV"  # Nombre comercial
    etree.SubElement(emi, "EMI_10").text = "CR 43 A 15 SUR 15 ED XEROX OF 802"  # Dirección
    etree.SubElement(emi, "EMI_11").text = "17"  # Código departamento Caldas
    etree.SubElement(emi, "EMI_13").text = "MANIZALES"  # Ciudad
    etree.SubElement(emi, "EMI_15").text = "CO"  # País
    etree.SubElement(emi, "EMI_19").text = "Caldas"  # Nombre departamento
    etree.SubElement(emi, "EMI_22").text = "8"  # Código de responsabilidad fiscal
    etree.SubElement(emi, "EMI_23").text = "17001"  # Código municipio Manizales
    etree.SubElement(emi, "EMI_24").text = "FACTURATECH SA. DE CV"  # Nombre contacto
    # TAC
    tac = etree.SubElement(emi, "TAC")
    etree.SubElement(tac, "TAC_1").text = "R-99-PN"
    # DFE
    dfe = etree.SubElement(emi, "DFE")
    etree.SubElement(dfe, "DFE_1").text = "17001"  # Código municipio Manizales
    etree.SubElement(dfe, "DFE_2").text = "17"     # Código departamento Caldas
    etree.SubElement(dfe, "DFE_3").text = "CO"     # Código país
    etree.SubElement(dfe, "DFE_4").text = "170001" # Código postal (ejemplo válido para Manizales)
    etree.SubElement(dfe, "DFE_5").text = "Colombia" # Nombre país
    etree.SubElement(dfe, "DFE_6").text = "Caldas"   # Nombre departamento
    etree.SubElement(dfe, "DFE_7").text = "MANIZALES" # Nombre ciudad
    etree.SubElement(dfe, "DFE_8").text = "CR 43 A 15 SUR 15 ED XEROX OF 802" # Dirección

    # ICC
    icc = etree.SubElement(emi, "ICC")
    etree.SubElement(icc, "ICC_1").text = str(num_factura)
    etree.SubElement(icc, "ICC_9").text = f"TCFA"

    # CDE: correo electrónico obligatorio si existe, si no, poner uno genérico válido
    cde = etree.SubElement(emi, "CDE")
    etree.SubElement(cde, "CDE_1").text = "1"
    etree.SubElement(cde, "CDE_2").text = str(cliente_data.get("nombre", ""))
    etree.SubElement(cde, "CDE_3").text = str(cliente_data.get("telefono", ""))
    correo_cde = cliente_data.get("email")
    if not correo_cde or correo_cde.lower() in ("null", "n/a", "undefined", ""):
        correo_cde = "cliente@correo.com"
    etree.SubElement(cde, "CDE_4").text = correo_cde

    # GTE
    gte = etree.SubElement(emi, "GTE")
    etree.SubElement(gte, "GTE_1").text = "1"
    etree.SubElement(gte, "GTE_2").text = "IVA"

    # ADQ (Adquiriente/Cliente)
    adq = etree.SubElement(root, "ADQ")
    etree.SubElement(adq, "ADQ_1").text = "1"  # Tipo de persona
    etree.SubElement(adq, "ADQ_2").text = str(cliente_data.get("nit", ""))  # Identificador adquiriente
    etree.SubElement(adq, "ADQ_3").text = "31"  # Tipo de documento
    etree.SubElement(adq, "ADQ_6").text = str(cliente_data.get("nombre", ""))  # Razón social
    etree.SubElement(adq, "ADQ_7").text = str(cliente_data.get("apellido", ""))  # Nombre comercial (si aplica)
    etree.SubElement(adq, "ADQ_10").text = str(cliente_data.get("direccion", "calle 123"))  # Dirección libre
    etree.SubElement(adq, "ADQ_11").text = "17"  # Código departamento Caldas
    etree.SubElement(adq, "ADQ_13").text = "MANIZALES"  # Nombre ciudad
    etree.SubElement(adq, "ADQ_14").text = "170001"  # Código postal válido para Manizales
    etree.SubElement(adq, "ADQ_15").text = "CO"  # Código país
    etree.SubElement(adq, "ADQ_19").text = "Caldas"  # Nombre departamento
    etree.SubElement(adq, "ADQ_21").text = "Colombia"  # Nombre país
    etree.SubElement(adq, "ADQ_22").text = "1"  # DV NIT (si aplica)
    etree.SubElement(adq, "ADQ_23").text = "17001"  # Código municipio Manizales
    # TCR
    tcr = etree.SubElement(adq, "TCR")
    etree.SubElement(tcr, "TCR_1").text = "R-99-PN"
    # ILA
    ila = etree.SubElement(adq, "ILA")
    etree.SubElement(ila, "ILA_1").text = str(cliente_data.get("nombre", ""))
    etree.SubElement(ila, "ILA_2").text = str(cliente_data.get("nit", ""))
    etree.SubElement(ila, "ILA_3").text = "31"
    etree.SubElement(ila, "ILA_4").text = "1"
    # DFA
    dfa = etree.SubElement(adq, "DFA")
    # DFA: datos fiscales correctos para Manizales, Caldas
    etree.SubElement(dfa, "DFA_1").text = "CO"  # País
    etree.SubElement(dfa, "DFA_2").text = "17"  # Código departamento Caldas según DIAN
    etree.SubElement(dfa, "DFA_3").text = "17001"  # Código municipio Manizales
    etree.SubElement(dfa, "DFA_4").text = "17001"  # Código municipio Manizales
    etree.SubElement(dfa, "DFA_5").text = "Colombia"
    etree.SubElement(dfa, "DFA_6").text = "Caldas"
    correo_dfa = cliente_data.get("email")
    if not correo_dfa or correo_dfa.lower() in ("null", "n/a", "undefined", ""):
        correo_dfa = "cliente@correo.com"
    etree.SubElement(dfa, "DFA_7").text = correo_dfa
    etree.SubElement(dfa, "DFA_8").text = str(cliente_data.get("direccion", "calle 123"))
    # ICR
    icr = etree.SubElement(adq, "ICR")
    etree.SubElement(icr, "ICR_1").text = str(num_factura)
    # CDA: correo electrónico obligatorio si existe, si no, poner uno genérico válido
    cda = etree.SubElement(adq, "CDA")
    etree.SubElement(cda, "CDA_1").text = "1"
    etree.SubElement(cda, "CDA_2").text = str(cliente_data.get("nombre", ""))
    etree.SubElement(cda, "CDA_3").text = str(cliente_data.get("telefono", ""))
    correo_cda = cliente_data.get("email")
    if not correo_cda or correo_cda.lower() in ("null", "n/a", "undefined", ""):
        correo_cda = "cliente@correo.com"
    etree.SubElement(cda, "CDA_4").text = correo_cda
    # GTA
    gta = etree.SubElement(adq, "GTA")
    etree.SubElement(gta, "GTA_1").text = "1"
    etree.SubElement(gta, "GTA_2").text = "IVA"

    
    # Calcular totales según reglas DIAN/FacturaTech
    moneda = str(venta_data.get("moneda", "COP"))
    # Calcular suma de ITE_5 y lista de IIM_4 (base imponible de cada línea)
    suma_bruto = 0.0
    lista_base_imponible = []
    productos_sin_iva = True
    for prod in productos:
        cantidad = float(prod.get("cantidad", 1))
        precio_unit = float(prod.get("precio", 0))
        valor_total_linea = cantidad * precio_unit
        suma_bruto += valor_total_linea
        lista_base_imponible.append(0.0)

    # Si los productos ya incluyen IVA, no sumar IVA adicional en los totales
    suma_iva = 0.0
    suma_descuento = float(venta_data.get("descuento", 0))
    suma_cargo = float(venta_data.get("cargo", 0)) if "cargo" in venta_data else 0.0
    suma_anticipo = float(venta_data.get("anticipo", 0)) if "anticipo" in venta_data else 0.0

    # TOT_1: suma de ITE_5 (valor bruto antes de tributos)
    tot_1 = round(suma_bruto, 2)
    tot_2 = moneda
    # TOT_3: base imponible, igual a suma de IIM_4 (suma de base imponible de cada línea)
    suma_base_imponible = sum(lista_base_imponible)
   
    tot_3 = 0.00
    tot_4 = moneda
    # TOT_7: valor bruto más tributos = suma_bruto (ya incluye IVA)
    tot_7 = round(suma_bruto, 2)
    tot_8 = moneda
    # TOT_5: valor a pagar = TOT_7 - descuentos a nivel total (DSC) + cargos a nivel total (CHG) - anticipos (PREPAID)
    tot_5 = round(tot_7 - suma_descuento + suma_cargo - suma_anticipo, 2)
    tot_6 = moneda

    tot = etree.SubElement(root, "TOT")
    etree.SubElement(tot, "TOT_1").text = f"{tot_1:.2f}"
    etree.SubElement(tot, "TOT_2").text = tot_2
    etree.SubElement(tot, "TOT_3").text = f"{tot_3:.2f}"
    etree.SubElement(tot, "TOT_4").text = tot_4
    etree.SubElement(tot, "TOT_5").text = f"{tot_5:.2f}"
    etree.SubElement(tot, "TOT_6").text = tot_6
    etree.SubElement(tot, "TOT_7").text = f"{tot_7:.2f}"
    etree.SubElement(tot, "TOT_8").text = tot_8

    drf = etree.SubElement(root, "DRF")
    etree.SubElement(drf, "DRF_1").text = "201911110152"
    etree.SubElement(drf, "DRF_2").text = "2019-11-11"
    etree.SubElement(drf, "DRF_3").text = "2030-12-31"
    etree.SubElement(drf, "DRF_4").text = "TCFA"
    etree.SubElement(drf, "DRF_5").text = "33621"
    etree.SubElement(drf, "DRF_6").text = "33720"

    # MEP (Medio de pago)
    mep = etree.SubElement(root, "MEP")
    etree.SubElement(mep, "MEP_1").text = "10"
    etree.SubElement(mep, "MEP_2").text = "1"
    etree.SubElement(mep, "MEP_3").text = f"{fecha}T{hora}"

    # ITE (Detalle de productos)

    for idx, prod in enumerate(productos, 1):
        ite = etree.SubElement(root, "ITE")
        cantidad = float(prod.get("cantidad", 1))
        precio_unit = float(prod.get("precio", 0))
        valor_total_linea = cantidad * precio_unit
        base_imponible = 0.00
        etree.SubElement(ite, "ITE_1").text = str(idx)
        etree.SubElement(ite, "ITE_3").text = str(int(cantidad))
        etree.SubElement(ite, "ITE_4").text = "94"
        etree.SubElement(ite, "ITE_5").text = f"{valor_total_linea:.2f}"
        etree.SubElement(ite, "ITE_6").text = moneda
        etree.SubElement(ite, "IIM_4").text = f"{base_imponible:.2f}"
        etree.SubElement(ite, "ITE_7").text = f"{precio_unit:.2f}"
        etree.SubElement(ite, "ITE_8").text = moneda
        etree.SubElement(ite, "ITE_10").text = prod.get("nombre", "")
        etree.SubElement(ite, "ITE_11").text = prod.get("descripcion", prod.get("nombre", ""))
        etree.SubElement(ite, "ITE_20").text = moneda
        etree.SubElement(ite, "ITE_21").text = f"{valor_total_linea:.2f}"
        etree.SubElement(ite, "ITE_24").text = moneda
        etree.SubElement(ite, "ITE_27").text = str(int(cantidad))
        etree.SubElement(ite, "ITE_28").text = "94"
        iae = etree.SubElement(ite, "IAE")
        etree.SubElement(iae, "IAE_1").text = "10"
        etree.SubElement(iae, "IAE_2").text = "999"


    xml_str = etree.tostring(root, pretty_print=True, encoding="utf-8").decode("utf-8")
    # Guardar el XML en una carpeta aparte
    import os
    xml_dir = os.path.abspath('xml_facturas')
    if not os.path.exists(xml_dir):
        os.makedirs(xml_dir)
    xml_filename = f"factura_{num_factura}.xml"
    xml_path = os.path.join(xml_dir, xml_filename)
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    try:
        from tkinter import messagebox
        messagebox.showinfo("XML guardado", f"El archivo XML se guardó en:\n{xml_path}")
    except Exception:
        pass  # Si no hay entorno gráfico, no mostrar mensaje
    return xml_str

from Smart_data_syncro.facturatech_api import FacturaTechClient
from tkinter import simpledialog, messagebox

def consultar_estado_factura():
    transaccion_id = simpledialog.askstring("Consultar estado", "Ingrese el ID de transacción de la factura electrónica:")
    if not transaccion_id:
        return
    try:
        ft_client = FacturaTechClient()
        status = ft_client.get_status(transaccion_id)
        messagebox.showinfo("Estado de la factura", f"Respuesta de FacturaTech:\n{status}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo consultar el estado: {e}")
