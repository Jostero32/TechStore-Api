"""Verificación centralizada del JWT emitido por Firebase Authentication."""
import os, json
from functools import wraps
from flask import request, jsonify, g
import firebase_admin
from firebase_admin import credentials, auth as fb_auth

def init_firebase():
    if firebase_admin._apps:
        return
    raw = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if raw:
        cred = credentials.Certificate(json.loads(raw))
        firebase_admin.initialize_app(cred)
    else:
        # Modo desarrollo sin credenciales (NO usar en producción)
        firebase_admin.initialize_app()

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Token JWT no proporcionado"}), 401
        token = header.split(" ", 1)[1]
        try:
            decoded = fb_auth.verify_id_token(token)
        except Exception as e:
            return jsonify({"error": "Token inválido o expirado", "detalle": str(e)}), 401
        g.firebase_uid = decoded["uid"]
        g.email = decoded.get("email")
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    """Se usa DESPUÉS de token_required. Verifica rol en la BD."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        from models import Usuario
        u = Usuario.query.filter_by(firebase_uid=g.firebase_uid).first()
        if not u or u.rol != "admin":
            return jsonify({"error": "Se requiere rol de administrador"}), 403
        return f(*args, **kwargs)
    return wrapper
