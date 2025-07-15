# app/core/config.py
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Pusat Arsip & Aset Digital Sekolah"
    API_V1_STR: str = "/api/v1"

    # Ganti dengan URL database PostgreSQL Anda
    # Format: "postgresql://user:password@host:port/dbname"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/digital_assets_db")

    # Lokasi penyimpanan file
    UPLOAD_DIRECTORY: str = "uploads"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()