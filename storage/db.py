from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings
from datetime import datetime

engine = create_engine(settings.DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RuntimeEvent(Base):
    __tablename__ = "runtime_events"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip = Column(String, index=True)
    endpoint = Column(String, index=True)
    method = Column(String)
    param_count = Column(Integer)
    body_size = Column(Integer)
    drift_score = Column(Float)
    risk_level = Column(String)
    attack_type = Column(String)  # ← NEW

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
