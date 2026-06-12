from flask import Blueprint, request, jsonify, g
from models import db, Usuario
from auth import token_required, admin_required

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")

@usuarios_bp.post("/registro")
@token_required
def registrar():
    """Sincroniza el usuario de Firebase con Supabase (se llama tras el registro)."""
    data = request.get_json() or {}
    try:
        existente = Usuario.query.filter_by(firebase_uid=g.firebase_uid).first()
        if existente:
            return jsonify(existente.to_dict()), 200
        u = Usuario(
            firebase_uid=g.firebase_uid,
            nombre=data.get("nombre", "Sin nombre"),
            email=g.email or data.get("email"),
            telefono=data.get("telefono"),
            rol=data.get("rol", "cliente"),
        )
        db.session.add(u)
        db.session.commit()
        return jsonify(u.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.session.close()

@usuarios_bp.get("/me")
@token_required
def me():
    u = Usuario.query.filter_by(firebase_uid=g.firebase_uid).first()
    if not u:
        return jsonify({"error": "Usuario no sincronizado"}), 404
    return jsonify(u.to_dict())

@usuarios_bp.get("")
@token_required
@admin_required
def listar():
    return jsonify([u.to_dict() for u in Usuario.query.order_by(Usuario.id).all()])

@usuarios_bp.put("/<int:uid>")
@token_required
@admin_required
def actualizar(uid):
    data = request.get_json() or {}
    try:
        u = Usuario.query.get_or_404(uid)
        for campo in ("nombre", "telefono", "rol", "activo"):
            if campo in data:
                setattr(u, campo, data[campo])
        db.session.commit()
        return jsonify(u.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.session.close()

@usuarios_bp.delete("/<int:uid>")
@token_required
@admin_required
def eliminar(uid):
    try:
        u = Usuario.query.get_or_404(uid)
        u.activo = False  # borrado lógico
        db.session.commit()
        return jsonify({"mensaje": "Usuario desactivado"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.session.close()
