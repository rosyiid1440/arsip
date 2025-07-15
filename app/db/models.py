# app/db/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime

from app.db.base_class import Base

class Folder(Base):
    __tablename__ = 'folders'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    
    # Kunci untuk struktur folder bertingkat (self-referencing)
    parent_id = Column(Integer, ForeignKey('folders.id'), nullable=True)

    # Mendefinisikan hubungan parent-child
    parent = relationship('Folder', remote_side=[id], back_populates='children')
    children = relationship('Folder', back_populates='parent', cascade="all, delete-orphan")
    
    # Hubungan ke aset yang ada di dalam folder ini
    assets = relationship('Asset', back_populates='folder', cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Asset(Base):
    __tablename__ = 'assets'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    file_path = Column(String, unique=True, nullable=False)
    thumbnail_path = Column(String, nullable=True)
    file_type = Column(String)
    event_name = Column(String, index=True)
    capture_date = Column(DateTime)
    photographer = Column(String)
    tags = Column(String)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Menghubungkan setiap aset ke sebuah folder
    folder_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    folder = relationship('Folder', back_populates='assets')