# app/api/endpoints/assets.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Response, Form, Request
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse # <-- Pastikan ini diimpor
from fastapi.templating import Jinja2Templates # <-- Impor ini
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os

from app.db import session
from app.schemas import asset as asset_schema
from app.crud import crud_asset, crud_folder
from app.core.config import settings
from app.services import file_processor

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.post("/", response_model=asset_schema.Asset)
def create_asset(
    *,
    db: Session = Depends(session.get_db),
    title: str,
    description: Optional[str] = None,
    event_name: Optional[str] = None,
    photographer: Optional[str] = None,
    tags: Optional[str] = None,
    file: UploadFile = File(...)
):
    """
    Mengunggah file aset baru beserta metadatanya.
    """
    # 1. Simpan file ke disk
    file_path = file_processor.save_upload_file(upload_file=file, destination=settings.UPLOAD_DIRECTORY)
    file_type = file.content_type.split('/')[0] # 'image', 'video', etc

    # 2. Buat thumbnail jika file adalah gambar atau video
    if file_type in ["image", "video"]:
        thumbnail_destination = os.path.join(settings.UPLOAD_DIRECTORY, "thumbnails")
        thumbnail_path = file_processor.create_image_thumbnail(
            original_path=file_path, 
            destination=thumbnail_destination
        )
        pass

    # 3. Buat objek data untuk disimpan ke database
    asset_in = asset_schema.AssetCreate(
        title=title,
        description=description,
        event_name=event_name,
        photographer=photographer,
        tags=tags,
    )
    
    # 4. Simpan record ke database
    new_asset = crud_asset.create_asset(
        db=db, 
        asset=asset_in, 
        file_path=file_path, 
        thumbnail_path=thumbnail_path, # <-- Kirim path thumbnail
        file_type=file_type
    )
    
    return new_asset


@router.get("/", response_model=List[asset_schema.Asset])
def read_assets(
    db: Session = Depends(session.get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
):
    """
    Mendapatkan daftar semua aset dengan opsi pencarian.
    """
    if search:
        assets = crud_asset.search_assets(db, query=search)
    else:
        assets = crud_asset.get_assets(db, skip=skip, limit=limit)
    return assets

@router.get("/{asset_id}", response_model=asset_schema.Asset)
def read_asset(
    *,
    db: Session = Depends(session.get_db),
    asset_id: int,
):
    """
    Mendapatkan detail satu aset berdasarkan ID.
    """
    db_asset = crud_asset.get_asset(db, id=asset_id)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Aset tidak ditemukan")
    return db_asset

@router.delete("/{asset_id}")
def delete_single_asset(
    request: Request, 
    asset_id: int, 
    db: Session = Depends(session.get_db)
):
    # ... (logika untuk mendapatkan parent_id dan menghapus aset tidak berubah) ...
    asset_to_delete = crud_asset.get_asset(db, id=asset_id)
    if not asset_to_delete:
        raise HTTPException(status_code=404, detail="Aset tidak ditemukan")
    parent_id = asset_to_delete.folder_id
    crud_asset.delete_asset(db, asset_id=asset_id)

    # Ambil konten dari folder induk untuk di-refresh
    if parent_id:
        parent_folder = crud_folder.get_folder(db, folder_id=parent_id)
        items = parent_folder.children + parent_folder.assets if parent_folder else []
    else:
        root_folders = crud_folder.get_root_folders(db)
        root_assets = db.query(models.Asset).filter(models.Asset.folder_id.is_(None)).all()
        items = root_folders + root_assets

    # Ganti return statement untuk menggunakan template paket yang baru
    return templates.TemplateResponse(
        "_refresh_browser_and_close_all.html",
        {"request": request, "items": items}
    )

@router.put("/{asset_id}", response_model=asset_schema.Asset)
def update_single_asset(
    request: Request, # <-- Tambahkan request
    asset_id: int,
    db: Session = Depends(session.get_db),
    title: str = Form(...)
):
    asset_in = asset_schema.AssetUpdate(title=title)
    updated_asset = crud_asset.update_asset(db, asset_id=asset_id, asset_update=asset_in)

    if not updated_asset:
        raise HTTPException(status_code=404, detail="Aset tidak ditemukan")

    # Ambil konten dari folder induk untuk di-refresh
    parent_id = updated_asset.folder_id
    if parent_id:
        parent_folder = crud_folder.get_folder(db, folder_id=parent_id)
        items = parent_folder.children + parent_folder.assets if parent_folder else []
    else:
        root_folders = crud_folder.get_root_folders(db)
        root_assets = db.query(models.Asset).filter(models.Asset.folder_id.is_(None)).all()
        items = root_folders + root_assets

    # Render dan kembalikan HTML dari folder induk + perintah tutup UI
    return templates.TemplateResponse(
        "_refresh_browser_and_close_all.html",
        {"request": request, "items": items}
    )