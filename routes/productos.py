from flask import Blueprint, request, jsonify
from models import db, Producto
from auth import token_required, admin_required

productos_bp = Blueprint("productos", __name__, url_prefix="/api/productos")

@productos_bp.get("")
def listar():
    """Público: lo consumen React, Flutter y los portales."""
    prods = Producto.query.filter_by(activo=True).order_by(Producto.id).all()
    return jsonify([p.to_dict() for p in prods])

@productos_bp.get("/<int:pid>")
def obtener(pid):
    return jsonify(Producto.query.get_or_404(pid).to_dict())

@productos_bp.post("")
@token_required
@admin_required
def crear():
    data = request.get_json() or {}
    try:
        p = Producto(
            nombre=data["nombre"],
            descripcion=data.get("descripcion"),
            precio=data["precio"],
            stock=data.get("stock", 0),
            imagen_url=data.get("imagen_url"),
        )
        db.session.add(p)
        db.session.commit()
        return jsonify(p.to_dict()), 201
    except KeyError as e:
        return jsonify({"error": f"Falta el campo {e}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.session.close()

@productos_bp.put("/<int:pid>")
@token_required
@admin_required
def actualizar(pid):
    data = request.get_json() or {}
    try:
        p = Producto.query.get_or_404(pid)
        for campo in ("nombre", "descripcion", "precio", "stock", "imagen_url", "activo"):
            if campo in data:
                setattr(p, campo, data[campo])
        db.session.commit()
        return jsonify(p.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.session.close()

@productos_bp.delete("/<int:pid>")
@token_required
@admin_required
def eliminar(pid):
    try:
        p = Producto.query.get_or_404(pid)
        p.activo = False
        db.session.commit()
        return jsonify({"mensaje": "Producto desactivado"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.session.close()
