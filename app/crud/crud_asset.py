from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
import os

from app.db import models
from app.schemas import asset as asset_schema

def get_asset(db: Session, id: int):
    return db.query(models.Asset).filter(models.Asset.id == id).first()

def get_assets(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Asset).offset(skip).limit(limit).all()

def create_asset(
    db: Session, 
    asset: asset_schema.AssetCreate, 
    file_path: str, 
    file_type: str,
    thumbnail_path: Optional[str] = None, # 1. Tambahkan parameter baru
    folder_id: Optional[int] = None
    ):
    """
    Membuat record aset baru di database.
    """
    db_asset = models.Asset(
        **asset.model_dump(),
        file_path=file_path,
        file_type=file_type,
        thumbnail_path=thumbnail_path, # 2. Simpan path thumbnail ke database
        folder_id=folder_id
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def search_assets(db: Session, query: str):
    search_query = f"%{query}%"
    return db.query(models.Asset).filter(
        or_(
            models.Asset.title.ilike(search_query),
            models.Asset.description.ilike(search_query),
            models.Asset.event_name.ilike(search_query),
            models.Asset.tags.ilike(search_query)
        )
    ).all()

def delete_asset(db: Session, asset_id: int) -> models.Asset:
    """Menghapus aset dari DB dan file fisiknya dari server."""
    db_asset = get_asset(db, id=asset_id)
    if not db_asset:
        return None
    
    # Hapus file fisik (original & thumbnail) untuk hemat ruang
    if db_asset.file_path and os.path.exists(db_asset.file_path):
        os.remove(db_asset.file_path)
    if db_asset.thumbnail_path and os.path.exists(db_asset.thumbnail_path):
        os.remove(db_asset.thumbnail_path)
        
    db.delete(db_asset)
    db.commit()
    return db_asset

def update_asset(db: Session, asset_id: int, asset_update: asset_schema.AssetUpdate) -> models.Asset:
    db_asset = get_asset(db, id=asset_id)
    if db_asset:
        db_asset.title = asset_update.title
        db.commit()
        db.refresh(db_asset)
    return db_asset