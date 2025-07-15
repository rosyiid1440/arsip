# app/crud/crud_folder.py
from sqlalchemy.orm import Session
from typing import Optional

from app.db import models
from app.schemas import folder as folder_schema

def get_folder(db: Session, folder_id: int):
    """Mengambil satu folder beserta isinya (sub-folder dan aset)."""
    return db.query(models.Folder).filter(models.Folder.id == folder_id).first()

def get_root_folders(db: Session):
    """Mengambil semua folder di level atas (yang tidak punya parent)."""
    return db.query(models.Folder).filter(models.Folder.parent_id == None).all()

def create_folder(db: Session, folder: folder_schema.FolderCreate) -> models.Folder:
    """Membuat folder baru."""
    db_folder = models.Folder(name=folder.name, parent_id=folder.parent_id)
    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)
    return db_folder

def delete_folder(db: Session, folder_id: int) -> models.Folder:
    """Menghapus folder (dan semua isinya karena 'cascade')."""
    db_folder = get_folder(db, folder_id=folder_id)
    if not db_folder:
        return None
    
    db.delete(db_folder)
    db.commit()
    return db_folder

def update_folder(db: Session, folder_id: int, folder_update: folder_schema.FolderUpdate) -> models.Folder:
    db_folder = get_folder(db, folder_id=folder_id)
    if db_folder:
        db_folder.name = folder_update.name
        db.commit()
        db.refresh(db_folder)
    return db_folder

    # PASTIKAN FUNGSI INI ADA DI DALAM FILE
def get_folder_path(db: Session, folder_id: int) -> list[models.Folder]:
    """Mengambil jalur breadcrumb dari folder saat ini hingga ke root."""
    path = []
    current_folder = get_folder(db, folder_id=folder_id)
    while current_folder:
        path.append(current_folder)
        current_folder = current_folder.parent
    return path[::-1] # Dibalik agar urutannya dari root ke folder saat ini