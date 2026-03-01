# storage/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import settings
from .models import Base, RuntimeEvent

engine = create_engine(settings.DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Auto-create tables on import
Base.metadata.create_all(bind=engine)

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
