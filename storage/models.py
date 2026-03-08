from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class RuntimeEvent(Base):
    __tablename__ = "runtime_events"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_hash = Column(String, index=True)
    endpoint = Column(String, index=True)
    method = Column(String)
    param_count = Column(Integer)
    body_size = Column(Integer)
    drift_score = Column(Float)
    risk_level = Column(String, index=True)
    attack_type = Column(String)
    attack_confidence = Column(Float)
    attack_evidence = Column(Text)
    user_role = Column(String)
