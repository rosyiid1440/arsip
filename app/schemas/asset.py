# app/schemas/asset.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Skema dasar untuk data yang masuk
class AssetBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_name: Optional[str] = None
    capture_date: Optional[datetime] = None
    photographer: Optional[str] = None
    tags: Optional[str] = None

# Skema untuk membuat aset baru (dari request)
class AssetCreate(AssetBase):
    pass

# Skema untuk menampilkan aset (untuk response)
class Asset(AssetBase):
    id: int
    file_path: str
    thumbnail_path: Optional[str] = None # <-- TAMBAHKAN BARIS INI
    file_type: str
    uploaded_at: datetime

    class Config:
        orm_mode = True # Dulu 'orm_mode', sekarang 'from_attributes=True' di Pydantic v2
        from_attributes = True

class AssetUpdate(BaseModel):
    title: str