# monitoring/logger.py
from storage.db import SessionLocal
from storage.models import RuntimeEvent
import uuid
import json
from datetime import datetime

def log_event(features, drift_score, risk_level, classification: dict):
    db = SessionLocal()
    try:
        event = RuntimeEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            ip_hash=features.ip_hash,
            endpoint=features.endpoint,
            method=features.method,
            param_count=features.param_count,
            body_size=features.body_size,
            drift_score=drift_score,
            risk_level=risk_level,
            attack_type=classification["type"],
            attack_confidence=classification["confidence"],
            attack_evidence=json.dumps(classification["evidence"]),
            user_role=features.user_role
        )
        db.add(event)
        db.commit()
    except Exception as e:
        print(f"⚠️ Logger error: {e}")
    finally:
        db.close()
