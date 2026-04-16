from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class RuntimeEvent(Base):
    __tablename__ = "runtime_events"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_hash = Column(String, index=True)
    ip_addr = Column(String)
    endpoint = Column(String, index=True)
    method = Column(String)
    param_count = Column(Integer)
    body_size = Column(Integer)
    drift_score = Column(Float)
    risk_level = Column(String, index=True)
    attack_type = Column(String, index=True)
    attack_confidence = Column(Float)
    attack_evidence = Column(Text)
    attack_category = Column(String)  # SQL, XSS, Path Traversal, SSRF, Command Injection, XXE, Parameter Spam, Behavioral Anomaly
    attack_description = Column(Text)  # Detailed description of what triggered the detection
    request_sample = Column(Text)  # Sample of request body/params
    baseline_before = Column(Float)  # Baseline value before adaptation
    baseline_after = Column(Float)  # Baseline value after adaptation
    adaptation_triggered = Column(Boolean, default=False)  # Whether baseline was adapted
    user_role = Column(String)
    user_agent = Column(String)
    is_flagged = Column(Boolean, default=False)  # For SOC Analysts to flag/unflag request
