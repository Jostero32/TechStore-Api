from decimal import Decimal
from flask import Blueprint, request, jsonify, g, current_app
from models import db, Usuario, Producto, Compra
from auth import token_required, admin_required
from services.soap_client import generar_factura_soap
from services.notificaciones import enviar_factura_email, enviar_alerta_sms

compras_bp = Blueprint("compras", __name__, url_prefix="/api/compras")
IVA = Decimal("0.15")  # IVA Ecuador 15%

@compras_bp.post("")
@token_required
def crear():
    """Flujo del requerimiento 9 del diagrama:
    1) registra la compra en Supabase
    2) invoca el servicio SOAP para validar/generar la factura XML
    3) envía la factura por correo y alerta por Twilio
    """
    data = request.get_json() or {}
    items_req = data.get("items", [])
    if not items_req:
        return jsonify({"error": "La compra debe tener al menos un item"}), 400

    usuario = Usuario.query.filter_by(firebase_uid=g.firebase_uid).first()
    if not usuario:
        return jsonify({"error": "Usuario no sincronizado"}), 404

    try:
        items, subtotal = [], Decimal("0")
        for it in items_req:
            p = Producto.query.get(it["producto_id"])
            cantidad = int(it.get("cantidad", 1))
            if not p or not p.activo:
                return jsonify({"error": f"Producto {it['producto_id']} no existe"}), 400
            if p.stock < cantidad:
                return jsonify({"error": f"Stock insuficiente para {p.nombre}"}), 400
            p.stock -= cantidad
            sub = Decimal(p.precio) * cantidad
            subtotal += sub
            items.append({
                "producto_id": p.id, "nombre": p.nombre, "cantidad": cantidad,
                "precio_unitario": float(p.precio), "subtotal": float(sub),
            })

        iva = (subtotal * IVA).quantize(Decimal("0.01"))
        total = subtotal + iva
        compra = Compra(usuario_id=usuario.id, items=items,
                        subtotal=subtotal, iva=iva, total=total)
        db.session.add(compra)
        db.session.commit()  # 1) compra registrada en Supabase

        # 2) Invocar SOAP de facturación
        soap = generar_factura_soap(compra.id)
        if soap:
            compra.estado = soap.get("estado", "PENDIENTE")
            compra.clave_acceso = soap.get("clave_acceso")
            db.session.commit()

        # 3) Notificaciones (no bloquean la compra si fallan)
        try:
            enviar_factura_email(usuario, compra, soap.get("xml") if soap else None)
            enviar_alerta_sms({
                "1": f"#{compra.id}",
                "2": f"${total} ({current_app.config['INSTANCE_NAME']})",
            })
        except Exception as e:
            current_app.logger.warning(f"Notificación falló: {e}")

        return jsonify(compra.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.session.close()

@compras_bp.get("/mias")
@token_required
def mis_compras():
    usuario = Usuario.query.filter_by(firebase_uid=g.firebase_uid).first()
    if not usuario:
        return jsonify([])
    compras = (Compra.query.filter_by(usuario_id=usuario.id)
               .order_by(Compra.creado_en.desc()).all())
    return jsonify([c.to_dict() for c in compras])

@compras_bp.get("")
@token_required
@admin_required
def todas():
    compras = Compra.query.order_by(Compra.creado_en.desc()).all()
    return jsonify([c.to_dict() for c in compras])
