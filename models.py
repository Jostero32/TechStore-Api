from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    rol = db.Column(db.String(20), default="cliente")
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "firebase_uid": self.firebase_uid,
            "nombre": self.nombre, "email": self.email,
            "telefono": self.telefono, "rol": self.rol,
            "activo": self.activo,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }

class Producto(db.Model):
    __tablename__ = "productos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    imagen_url = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "nombre": self.nombre,
            "descripcion": self.descripcion, "precio": float(self.precio),
            "stock": self.stock, "imagen_url": self.imagen_url,
            "activo": self.activo,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }

class Compra(db.Model):
    __tablename__ = "compras"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    items = db.Column(db.JSON, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    iva = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.String(20), default="PENDIENTE")
    clave_acceso = db.Column(db.String(60))
    creado_en = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "usuario_id": self.usuario_id, "items": self.items,
            "subtotal": float(self.subtotal), "iva": float(self.iva),
            "total": float(self.total), "estado": self.estado,
            "clave_acceso": self.clave_acceso,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }
