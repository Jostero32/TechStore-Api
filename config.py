import os
from dotenv import load_dotenv
from db import resolve_database_url

load_dotenv()

class Config:
    # Fallback automático: intenta Supabase (DATABASE_URL) y, si no responde
    # en 3s, usa Aiven (DATABASE_URL_REPLICA). Ver db.py.
    SQLALCHEMY_DATABASE_URI = resolve_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    INSTANCE_NAME = os.getenv("INSTANCE_NAME", "RENDER-LOCAL")
    SOAP_URL = os.getenv("SOAP_URL", "http://localhost:8000/soap")
