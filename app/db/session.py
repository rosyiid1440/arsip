# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Membuat engine koneksi ke database sesuai URL dari config
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Membuat class SessionLocal yang akan kita gunakan untuk membuat sesi
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fungsi dependency yang akan di-inject ke setiap endpoint
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()