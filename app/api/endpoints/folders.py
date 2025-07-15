# app/api/endpoints/folders.py
from fastapi import APIRouter, Depends, HTTPException, Response, Form, Request
from fastapi.responses import HTMLResponse # <-- Pastikan ini diimpor
from fastapi.templating import Jinja2Templates # <-- Impor ini
from sqlalchemy.orm import Session
from typing import List
from app.db import session
from app.crud import crud_folder
from app.schemas import folder as folder_schema

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.post("/", response_model=folder_schema.Folder)
def create_new_folder(
    folder: folder_schema.FolderCreate,
    db: Session = Depends(session.get_db)
):
    """Endpoint untuk membuat folder baru."""
    return crud_folder.create_folder(db=db, folder=folder)

@router.get("/root", response_model=List[folder_schema.Folder])
def read_root_folders(db: Session = Depends(session.get_db)):
    """Endpoint untuk melihat semua folder di level root."""
    return crud_folder.get_root_folders(db=db)

@router.get("/{folder_id}", response_model=folder_schema.Folder)
def read_folder_content(folder_id: int, db: Session = Depends(session.get_db)):
    """Endpoint untuk melihat isi dari sebuah folder."""
    db_folder = crud_folder.get_folder(db=db, folder_id=folder_id)
    if db_folder is None:
        raise HTTPException(status_code=404, detail="Folder tidak ditemukan")
    return db_folder

@router.delete("/{folder_id}")
def delete_single_folder(
    request: Request,
    folder_id: int, 
    db: Session = Depends(session.get_db)
):
    # Dapatkan folder untuk mengetahui parent_id-nya SEBELUM dihapus
    folder_to_delete = crud_folder.get_folder(db, folder_id=folder_id)
    if not folder_to_delete:
        raise HTTPException(status_code=404, detail="Folder tidak ditemukan")
    
    parent_id = folder_to_delete.parent_id

    # Hapus folder
    crud_folder.delete_folder(db, folder_id=folder_id)

    # Ambil konten dari folder induk untuk di-refresh
    if parent_id:
        parent_folder = crud_folder.get_folder(db, folder_id=parent_id)
        items = parent_folder.children + parent_folder.assets if parent_folder else []
    else: # Jika di root
        root_folders = crud_folder.get_root_folders(db)
        root_assets = db.query(models.Asset).filter(models.Asset.folder_id.is_(None)).all()
        items = root_folders + root_assets

    # Render dan kembalikan HTML dari folder induk
    # html_content = templates.get_template("_browser_items.html").render({"request": request, "items": items})
    return templates.TemplateResponse(
        "_refresh_browser_and_close_all.html",
        {"request": request, "items": items}
    )

@router.put("/{folder_id}", response_model=folder_schema.Folder)
def update_single_folder(
    request: Request, # <-- Tambahkan request
    folder_id: int, 
    db: Session = Depends(session.get_db),
    name: str = Form(...)
):
    folder_in = folder_schema.FolderUpdate(name=name)
    updated_folder = crud_folder.update_folder(db, folder_id=folder_id, folder_update=folder_in)
    
    if not updated_folder:
        raise HTTPException(status_code=404, detail="Folder tidak ditemukan")

    # Ambil konten dari folder induk untuk di-refresh
    parent_id = updated_folder.parent_id
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