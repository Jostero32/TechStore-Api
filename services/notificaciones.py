"""Requerimiento 8: alertas con Twilio y correos (Brevo HTTP API o SMTP)."""
import os, base64, json, smtplib, requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

BREVO_URL = "https://api.brevo.com/v3/smtp/email"

def enviar_alerta_sms(content_variables: dict):
    """Alerta por WhatsApp (Twilio Sandbox) usando un Content Template aprobado."""
    sid   = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    if not sid or not token:
        print("[Twilio] No configurado, se omite alerta")
        return
    try:
        from twilio.rest import Client
        Client(sid, token).messages.create(
            content_sid=os.getenv("TWILIO_CONTENT_SID"),
            content_variables=json.dumps(content_variables),
            from_=f"whatsapp:{os.getenv('TWILIO_FROM')}",
            to=f"whatsapp:{os.getenv('TWILIO_ADMIN_PHONE')}",
        )
        print("[Twilio] Alerta WhatsApp enviada")
    except Exception as e:
        print(f"[Twilio] Error enviando WhatsApp: {e}")

def enviar_factura_email(usuario, compra, xml_factura: str | None):
    if os.getenv("BREVO_API_KEY"):
        _enviar_brevo(usuario, compra, xml_factura)
    elif os.getenv("SMTP_HOST"):
        _enviar_smtp(usuario, compra, xml_factura)
    else:
        print("[Email] Sin configuración de correo, se omite")

# ── Brevo HTTP API (recomendado para Render — sin restricción de IP) ──────────
def _enviar_brevo(usuario, compra, xml_factura):
    cuerpo = _cuerpo(usuario, compra)
    payload = {
        "sender":      {"name": "TechStore 360", "email": os.getenv("BREVO_FROM")},
        "to":          [{"email": usuario.email, "name": usuario.nombre}],
        "subject":     f"TechStore 360 - Factura de la compra #{compra.id}",
        "textContent": cuerpo,
    }
    if xml_factura:
        payload["attachment"] = [{
            "content": base64.b64encode(xml_factura.encode("utf-8")).decode("utf-8"),
            "name":    f"factura_{compra.id}.xml",
        }]
    try:
        r = requests.post(
            BREVO_URL,
            json=payload,
            headers={"api-key": os.getenv("BREVO_API_KEY"), "Content-Type": "application/json"},
            timeout=15,
        )
        if r.status_code in (200, 201, 202):
            print(f"[Email] Factura enviada a {usuario.email} (Brevo API)")
        else:
            print(f"[Email] Error Brevo {r.status_code}: {r.text}")
    except Exception as e:
        print(f"[Email] Error Brevo: {e}")

# ── SMTP genérico (Gmail, Outlook, etc.) ─────────────────────────────────────
def _enviar_smtp(usuario, compra, xml_factura):
    msg = MIMEMultipart()
    msg["From"]    = os.getenv("SMTP_FROM")
    msg["To"]      = usuario.email
    msg["Subject"] = f"TechStore 360 - Factura de la compra #{compra.id}"
    msg.attach(MIMEText(_cuerpo(usuario, compra), "plain", "utf-8"))
    if xml_factura:
        adj = MIMEApplication(xml_factura.encode("utf-8"), _subtype="xml")
        adj.add_header("Content-Disposition", "attachment",
                       filename=f"factura_{compra.id}.xml")
        msg.attach(adj)
    server = None
    try:
        server = smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", "587")), timeout=10)
        server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        server.send_message(msg)
        print(f"[Email] Factura enviada a {usuario.email} (SMTP)")
    except Exception as e:
        print(f"[Email] Error SMTP: {e}")
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass

# ── Texto del correo ──────────────────────────────────────────────────────────
def _cuerpo(usuario, compra) -> str:
    detalle = "\n".join(
        f"  - {i['nombre']} x{i['cantidad']}  ${i['subtotal']:.2f}"
        for i in compra.items
    )
    return (
        f"Hola {usuario.nombre},\n\n"
        f"Gracias por tu compra #{compra.id}.\n\n{detalle}\n\n"
        f"Subtotal: ${float(compra.subtotal):.2f}\n"
        f"IVA 15%:  ${float(compra.iva):.2f}\n"
        f"TOTAL:    ${float(compra.total):.2f}\n\n"
        f"Estado: {compra.estado}\nClave de acceso: {compra.clave_acceso}\n\n"
        f"Se adjunta la factura electrónica en XML.\nTechStore 360"
    )
