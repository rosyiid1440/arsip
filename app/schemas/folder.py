# app/schemas/folder.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from .asset import Asset  # Impor skema Asset

class FolderBase(BaseModel):
    name: str
    parent_id: Optional[int] = None

class FolderCreate(FolderBase):
    pass

# Ini adalah skema utama untuk menampilkan folder
class Folder(FolderBase):
    id: int
    
    # Akan kita isi nanti saat menampilkan data
    assets: List[Asset] = [] 
    children: List['Folder'] = [] # Menampilkan sub-folder

    model_config = ConfigDict(from_attributes=True)

class FolderUpdate(BaseModel):
    name: str