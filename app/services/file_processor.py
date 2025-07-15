import os
import shutil
import uuid
from fastapi import UploadFile
from PIL import Image # <-- TAMBAHKAN BARIS INI

def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """
    Menyimpan file yang diunggah ke direktori tujuan dengan nama unik.

    Args:
        upload_file: Objek file yang diunggah dari FastAPI.
        destination: Folder tujuan untuk menyimpan file (misal: 'uploads/images').

    Returns:
        String path lengkap dari file yang disimpan.
    """
    try:
        # Membuat direktori tujuan jika belum ada
        os.makedirs(destination, exist_ok=True)

        # Mendapatkan ekstensi file (contoh: .jpg, .png)
        file_extension = os.path.splitext(upload_file.filename)[1]
        
        # Membuat nama file yang unik menggunakan UUID untuk menghindari duplikasi
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Menggabungkan path tujuan dengan nama file unik
        file_path = os.path.join(destination, unique_filename)
        
        # Menyimpan file ke path tujuan
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            
    finally:
        # Selalu tutup file yang diunggah
        upload_file.file.close()
        
    return file_path

def create_image_thumbnail(original_path: str, destination: str, size: tuple[int, int] = (200, 200)) -> str:
    """
    Membuat thumbnail dari file gambar.
    """
    try:
        os.makedirs(destination, exist_ok=True)
        filename = os.path.basename(original_path)
        thumbnail_path = os.path.join(destination, filename)

        # Baris ini sekarang akan berfungsi karena 'Image' sudah diimpor
        with Image.open(original_path) as img:
            img.thumbnail(size)
            # Simpan sebagai JPEG untuk ukuran kecil dan kompatibilitas
            # Konversi ke RGB jika formatnya memiliki alpha channel (seperti PNG)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(thumbnail_path, "JPEG") 

        return thumbnail_path
    except Exception as e:
        print(f"Gagal membuat thumbnail: {e}")
        return None