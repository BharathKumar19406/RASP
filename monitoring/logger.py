import uuid
import json
from datetime import datetime
from storage.db import SessionLocal
from storage.models import RuntimeEvent

def log_event(features, drift_score, risk_level, attack: dict):
    db = SessionLocal()
    try:
        event = RuntimeEvent(
            id=str(uuid.uuid4()),
            ip_hash=features.ip_hash,
            endpoint=features.endpoint,
            method=features.method,
            param_count=features.param_count,
            body_size=features.body_size,
            drift_score=drift_score,
            risk_level=risk_level,
            attack_type=attack["type"],
            attack_confidence=attack["confidence"],
            attack_evidence=json.dumps(attack["evidence"]),
            user_role="user"
        )
        db.add(event)
        db.commit()
    except Exception as e:
        print(f"⚠️ Logger error: {e}")
    finally:
        db.close()
