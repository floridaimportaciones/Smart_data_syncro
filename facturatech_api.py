from zeep import Client

WSDL_URL = "https://ws.facturatech.co/v2/demo/index.php?wsdl"

# Usa las credenciales de tu imagen
FACTURATECH_USER = "SIDEIN01072025"
FACTURATECH_PASS = "aa021b872a1929300e29a0369b84eb0a37fa9e650950bfac2c310b5f48f8e5a3"

class FacturaTechClient:
    def __init__(self, username=FACTURATECH_USER, password=FACTURATECH_PASS):
        self.client = Client(WSDL_URL)
        self.username = username
        self.password = password

    def upload_invoice(self, xml_base64):
        # El método correcto según el WSDL es FtechAction.uploadInvoiceFile
        response = self.client.service.__getattr__('FtechAction.uploadInvoiceFile')(
            self.username, self.password, xml_base64
        )
        return response

    def get_status(self, transaccion_id):
        # El método correcto según el WSDL es FtechAction.documentStatusFile
        response = self.client.service.__getattr__('FtechAction.documentStatusFile')(
            self.username, self.password, transaccion_id
        )
        return response

    def download_pdf(self, numero_real):
        # Separar el prefijo y folio del número real (ej: TCFA33660 -> TCFA, 33660)
        numero_real = str(numero_real or "").strip()
        prefijo = ""
        folio = ""

        # Extraer letras del inicio como prefijo
        for i, char in enumerate(numero_real):
            if char.isdigit():
                prefijo = numero_real[:i]
                folio = numero_real[i:]
                break

        # Si no se pudo separar, usar el número completo como folio
        if not prefijo:
            prefijo = ""
            folio = numero_real

    # Normalizar prefijo (solo alfanumérico) y folio
        prefijo = (prefijo or "").upper().strip()
        prefijo = "".join(ch for ch in prefijo if ch.isalnum())
        folio_str = str(folio).strip()

        # Intentar primero con folio como string
        response = self.client.service.__getattr__('FtechAction.downloadPDFFile')(
            self.username, self.password, prefijo, folio_str
        )
        # Si 404 y folio es numérico, reintentar con entero
        if getattr(response, 'code', None) == '404' and folio_str.isdigit():
            try:
                response_int = self.client.service.__getattr__('FtechAction.downloadPDFFile')(
                    self.username, self.password, prefijo, int(folio_str)
                )
                return response_int
            except Exception:
                return response
        return response

    def download_pdf_by_parts(self, prefijo, folio):
        """Descarga PDF enviando prefijo y folio explícitos, con normalización básica.
        Intenta con folio como string y, si falla con 404 y es numérico, reintenta con entero.
        """
        prefijo = (str(prefijo or "").upper().strip())
        prefijo = "".join(ch for ch in prefijo if ch.isalnum())
        folio_str = str(folio).strip()

        response = self.client.service.__getattr__('FtechAction.downloadPDFFile')(
            self.username, self.password, prefijo, folio_str
        )
        if getattr(response, 'code', None) == '404' and folio_str.isdigit():
            try:
                response_int = self.client.service.__getattr__('FtechAction.downloadPDFFile')(
                    self.username, self.password, prefijo, int(folio_str)
                )
                return response_int
            except Exception:
                return response
        return response

