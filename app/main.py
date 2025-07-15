# app/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.api.api import api_router
from app.db.session import engine
from app.db.base import Base
from app.pages.router import router as pages_router

# Membuat tabel database
Base.metadata.create_all(bind=engine)

# 1. Buat instance aplikasi FastAPI DULU
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 2. BARU lakukan konfigurasi pada 'app'
# Konfigurasi untuk file statis (CSS, JS, gambar yg diunggah)
# "uploads" akan bisa diakses dari URL /static/uploads
# Folder "." berarti direktori root proyek
app.mount("/static", StaticFiles(directory="."), name="static")

# Sertakan semua router yang ada
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(pages_router, tags=["Pages"])

@app.get("/")
def read_root():
    # Arahkan halaman root ke router halaman
    return {"message": "Redirecting to pages...", "url": "/pages/"}