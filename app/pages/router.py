# app/pages/router.py
from fastapi import APIRouter, Request, Depends, Query # <-- Impor Query
from fastapi.templating import Jinja2Templates
from fastapi import Form, UploadFile, File # <-- Impor Form, UploadFile, File
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import os # <-- Pastikan 'os' juga diimpor

from app.db import session, models
from app.crud import crud_asset, crud_folder
from app.schemas import asset as asset_schema, folder as folder_schema # <-- Pastikan ini diimpor
from app.core.config import settings # <-- Pastikan ini diimpor
from app.services import file_processor # <-- TAMBAHKAN BARIS INI

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", name="home")
def get_home_page(request: Request):
    """Menampilkan halaman utama (kerangka HTML browser)."""
    return templates.TemplateResponse("browser.html", {"request": request})

# 1. Endpoint yang lebih spesifik ('/browse/root') didefinisikan PERTAMA.
@router.get("/browse/root", name="browse_root")
def browse_root(request: Request, db: Session = Depends(session.get_db)):
    """Menyediakan isi dari level root (semua folder & aset tanpa parent)."""
    root_folders = crud_folder.get_root_folders(db)
    # Anda perlu 'from app.db import models' di atas file ini
    root_assets = db.query(models.Asset).filter(models.Asset.folder_id == None).all()
    
    return templates.TemplateResponse(
    "_refresh_browser_and_close_all.html",
        {"request": request, "items": root_folders + root_assets, "folder": None, "path":[]} # Tambah "folder"
    )

@router.get("/browse/{folder_id}", name="browse_folder")
def browse_folder(request: Request, folder_id: int, db: Session = Depends(session.get_db)):
    """Menyediakan isi dari sebuah folder sebagai potongan HTML."""
    folder = crud_folder.get_folder(db, folder_id=folder_id)
    if not folder:
        return ""
    
    # Ambil path untuk breadcrumb
    # path = crud_folder.get_folder_path(db, folder_id=folder_id)
    path = crud_folder.get_folder_path(db, folder_id=folder_id) if folder_id else []
    
    return templates.TemplateResponse(
        "_refresh_browser_and_close_all.html", 
        {"request": request, "items": folder.children + folder.assets, "folder": folder, "path": path}
    )

@router.get("/load-assets", name="load_assets")
def load_assets(
    request: Request, 
    db: Session = Depends(session.get_db),
    search: str | None = None # <-- 1. Terima parameter 'search' opsional
):
    """Menyediakan daftar aset sebagai potongan HTML untuk HTMX."""
    
    # 2. Logika untuk memilih fungsi CRUD yang sesuai
    if search:
        assets = crud_asset.search_assets(db, query=search)
    else:
        assets = crud_asset.get_assets(db, limit=50)
    
    return templates.TemplateResponse(
        "_asset_list.html", 
        {"request": request, "assets": assets}
    )

@router.get("/assets/{asset_id}/details", name="get_asset_details")
def get_asset_details(request: Request, asset_id: int, db: Session = Depends(session.get_db)):
    """
    Mengambil detail satu aset dan mengembalikannya sebagai potongan HTML.
    """
    asset = crud_asset.get_asset(db, id=asset_id)
    if not asset:
        return "" # Kembalikan string kosong jika tidak ditemukan
    
    return templates.TemplateResponse(
        "_asset_detail.html", 
        {"request": request, "asset": asset}
    )

@router.post("/close-modal", name="close_modal")
def close_modal(request: Request): # <-- TAMBAHKAN 'request: Request' DI SINI
    """
    Mengembalikan komentar HTML yang tidak akan ditampilkan oleh browser.
    """
    return HTMLResponse(content="")

@router.post("/upload-asset", name="handle_asset_upload")
def handle_asset_upload(
    request: Request,
    db: Session = Depends(session.get_db),
    title: str = Form(...),
    event_name: str = Form(None),
    photographer: str = Form(None),
    tags: str = Form(None),
    file: UploadFile = File(...),
    folder_id: str = Form("")
):
    print("--- MEMULAI PROSES UPLOAD ---")
    print(f"Nama file diterima: {file.filename}")
    print(f"Tipe konten: {file.content_type}")

    actual_folder_id = int(folder_id) if folder_id and folder_id.isdigit() else None

    # 1. Simpan file fisik
    file_path = file_processor.save_upload_file(upload_file=file, destination=os.path.join(settings.UPLOAD_DIRECTORY, "originals"))
    print(f"File asli disimpan di: {file_path}")
    file_type = file.content_type.split('/')[0]

    # 2. Buat thumbnail
    thumbnail_path = None
    if file_type == "image":
        print("Tipe file adalah gambar, mencoba membuat thumbnail...")
        thumbnail_destination = os.path.join(settings.UPLOAD_DIRECTORY, "thumbnails")
        thumbnail_path = file_processor.create_image_thumbnail(
            original_path=file_path,
            destination=thumbnail_destination
        )
        if thumbnail_path:
            print(f"Thumbnail berhasil dibuat di: {thumbnail_path}")
        else:
            print("!!! PERINGATAN: Pembuatan thumbnail gagal. Fungsi mengembalikan None.")
    else:
        print(f"Tipe file adalah '{file_type}', thumbnail tidak dibuat.")

    # 3. Simpan data ke database
    print(f"Menyimpan ke DB dengan thumbnail_path: {thumbnail_path}")
    asset_in = asset_schema.AssetCreate(title=title)
    crud_asset.create_asset(
        db=db, asset=asset_in, file_path=file_path, file_type=file_type,
        thumbnail_path=thumbnail_path, folder_id=actual_folder_id
    )

    # Logika refresh browser (mirip dengan create_folder)
    if actual_folder_id:
        parent_folder = crud_folder.get_folder(db, folder_id=actual_folder_id)
        items = parent_folder.children + parent_folder.assets if parent_folder else []
    else:
        root_folders = crud_folder.get_root_folders(db)
        root_assets = db.query(models.Asset).filter(models.Asset.folder_id.is_(None)).all()
        items = root_folders + root_assets

    return templates.TemplateResponse(
        "_refresh_browser_and_close_all.html",
        {"request": request, "items": items}
    )

@router.get("/ui/new-folder-form", name="get_new_folder_form")
def get_new_folder_form(request: Request, parent_id: str | None = None): # 1. Ubah tipe menjadi str
    """Menyediakan form HTML untuk membuat folder baru."""
    
    # 2. Tambahkan logika untuk konversi manual
    # Jika parent_id adalah string angka, ubah jadi integer. Jika tidak, jadi None.
    current_parent_id = int(parent_id) if parent_id and parent_id.isdigit() else None
    
    return templates.TemplateResponse(
        "_new_folder_form.html",
        # 3. Kirim ID yang sudah bersih ke template
        {"request": request, "parent_id": current_parent_id}
    )

@router.post("/create-folder", name="create_folder")
def handle_create_folder(
    request: Request,
    db: Session = Depends(session.get_db),
    name: str = Form(...),
    parent_id: str = Form("") # 1. Ubah tipe menjadi str, default string kosong
):
    # 2. Tambahkan logika konversi manual yang aman
    actual_parent_id = int(parent_id) if parent_id and parent_id.isdigit() else None

    # 3. Gunakan ID yang sudah bersih untuk membuat folder
    folder_data = folder_schema.FolderCreate(name=name, parent_id=actual_parent_id)
    crud_folder.create_folder(db, folder=folder_data)

    # Ambil kembali konten dari folder induk untuk me-refresh tampilan
    if actual_parent_id:
        parent_folder = crud_folder.get_folder(db, folder_id=actual_parent_id)
        items = parent_folder.children + parent_folder.assets
    else: # Jika di root
        root_folders = crud_folder.get_root_folders(db)
        root_assets = db.query(models.Asset).filter(models.Asset.folder_id.is_(None)).all()
        items = root_folders + root_assets

    path = crud_folder.get_folder_path(db, folder_id=actual_parent_id) if actual_parent_id else []

    # Kirim 'items' DAN 'path' ke template
    return templates.TemplateResponse(
        "_refresh_browser_and_close_all.html",
        {"request": request, "items": items, "path": path} # <-- Pastikan "path" ada di sini
    )

@router.get("/ui/new-upload-form", name="get_new_upload_form")
def get_new_upload_form(request: Request, folder_id: str | None = None):
    """
    Menyediakan form HTML untuk mengunggah file baru.
    """
    # Logika untuk mengubah folder_id dari string ke integer (sudah benar)
    current_folder_id = int(folder_id) if folder_id and folder_id.isdigit() else None
    
    # PERBAIKAN DI SINI:
    # Kirim 'folder_id' ke template, bukan 'items'.
    return templates.TemplateResponse(
        "_new_upload_form.html",
        {"request": request, "folder_id": current_folder_id}
    )

@router.get("/ui/context-menu", name="get_context_menu")
def get_context_menu(
    request: Request, 
    item_id: int, 
    item_type: str, 
    x: int, # <-- Tambahkan ini
    y: int  # <-- Tambahkan ini
):
    """Menyediakan HTML untuk context menu."""
    return templates.TemplateResponse(
        "_context_menu.html",
        {
            "request": request, 
            "item_id": item_id, 
            "item_type": item_type,
            "x": x, # <-- Tambahkan ini
            "y": y  # <-- Tambahkan ini
        }
    )

@router.get("/ui/rename-form", name="get_rename_form")
def get_rename_form(request: Request, item_id: int, item_type: str, db: Session = Depends(session.get_db)):
    """Menyediakan form HTML untuk me-rename item."""
    current_name = ""
    if item_type == "folder":
        item = crud_folder.get_folder(db, folder_id=item_id)
        if item: current_name = item.name
    elif item_type == "asset":
        item = crud_asset.get_asset(db, id=item_id)
        if item: current_name = item.title

    return templates.TemplateResponse(
        "_rename_form.html",
        {"request": request, "item_id": item_id, "item_type": item_type, "current_name": current_name}
    )