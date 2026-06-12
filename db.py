"""Resolución de la URL de base de datos con fallback Supabase -> Aiven.

Al arrancar la app se prueba PRIMARY_DB_URL (Supabase); si no responde en
3 segundos se usa REPLICA_DB_URL (Aiven PostgreSQL). No cambia la lógica
de los endpoints: solo decide qué URI recibe Flask-SQLAlchemy.
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

logger = logging.getLogger(__name__)

PRIMARY_DB_URL = os.getenv("DATABASE_URL")          # Supabase
REPLICA_DB_URL = os.getenv("DATABASE_URL_REPLICA")  # Aiven PostgreSQL


def resolve_database_url() -> str:
    """Devuelve la primera URL que acepte una conexión real, con fallback."""
    for label, url in (("Supabase (primary)", PRIMARY_DB_URL),
                        ("Aiven (replica)", REPLICA_DB_URL)):
        if not url:
            continue
        try:
            engine = create_engine(url, connect_args={"connect_timeout": 3})
            with engine.connect():
                pass
            engine.dispose()
            logger.info(f"[DB] Conectado a {label}")
            return url
        except SQLAlchemyError as e:
            logger.warning(f"[DB] {label} no disponible ({e.__class__.__name__}). Probando siguiente...")
        except Exception as e:
            logger.warning(f"[DB] {label} error inesperado: {e}. Probando siguiente...")

    raise RuntimeError("Ninguna base de datos disponible (ni Supabase ni Aiven)")
