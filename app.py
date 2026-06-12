"""TechStore 360 - API REST (se despliega 2 veces: Render 1 y Render 2)."""
import os
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from config import Config
from models import db
from auth import init_firebase
from routes.usuarios import usuarios_bp
from routes.productos import productos_bp
from routes.compras import compras_bp

CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Max-Age":       "3600",
}

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/*": {"origins": "*"}},
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    db.init_app(app)
    init_firebase()

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            resp = make_response("", 204)
            for k, v in CORS_HEADERS.items():
                resp.headers[k] = v
            return resp

    @app.after_request
    def agregar_cors(response):
        for k, v in CORS_HEADERS.items():
            response.headers[k] = v
        return response

    @app.errorhandler(Exception)
    def handle_error(e):
        resp = jsonify({"error": str(e)})
        resp.status_code = getattr(e, "code", 500)
        for k, v in CORS_HEADERS.items():
            resp.headers[k] = v
        return resp

    app.register_blueprint(usuarios_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(compras_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "instancia": app.config["INSTANCE_NAME"]})

    @app.get("/")
    def root():
        return jsonify({
            "servicio": "TechStore 360 API REST",
            "instancia": app.config["INSTANCE_NAME"],
            "endpoints": ["/api/usuarios", "/api/productos", "/api/compras", "/health"],
        })

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
