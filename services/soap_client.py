"""Cliente SOAP: la API REST invoca al servicio de facturación (requerimiento 9)."""
import os, re, requests

SOAP_URL = os.getenv("SOAP_URL", "http://localhost:8000/soap")
NS = "techstore.soap.facturacion"

def generar_factura_soap(id_compra: int):
    """Invoca GenerarFacturaXML(idCompra) y parsea la respuesta."""
    envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:fac="{NS}">
  <soapenv:Body>
    <fac:GenerarFacturaXML>
      <fac:idCompra>{id_compra}</fac:idCompra>
    </fac:GenerarFacturaXML>
  </soapenv:Body>
</soapenv:Envelope>"""
    try:
        r = requests.post(
            SOAP_URL, data=envelope.encode("utf-8"),
            headers={"Content-Type": "text/xml; charset=utf-8"},
            timeout=30,
        )
        xml = r.text
        estado = _extraer(xml, "Estado") or "PENDIENTE"
        clave = _extraer(xml, "ClaveAcceso")
        return {"estado": estado, "clave_acceso": clave, "xml": xml}
    except Exception as e:
        print(f"[SOAP] Error invocando facturación: {e}")
        return None

def _extraer(xml: str, tag: str):
    # El contenido viene escapado dentro de la respuesta SOAP
    m = re.search(rf"&lt;{tag}&gt;(.*?)&lt;/{tag}&gt;", xml)
    if m:
        return m.group(1)
    m = re.search(rf"<{tag}>(.*?)</{tag}>", xml)
    return m.group(1) if m else None
