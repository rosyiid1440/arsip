from fastapi import APIRouter

from app.api.endpoints import assets, folders # Nanti bisa ditambahkan endpoint lain di sini

api_router = APIRouter()

# Menggabungkan router dari setiap file endpoint
api_router.include_router(assets.router, prefix="/assets", tags=["Aset"])
api_router.include_router(folders.router, prefix="/folders", tags=["Folder"])
# Contoh jika nanti ada endpoint otentikasi:
# api_router.include_router(auth.router, prefix="/auth", tags=["Otentikasi"])