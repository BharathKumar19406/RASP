from storage.db import SessionLocal, RuntimeEvent

def save_event(event_data):
    db = SessionLocal()
    try:
        event = RuntimeEvent(**event_data)
        db.add(event)
        db.commit()
    finally:
        db.close()

def get_recent_events(limit=50):
    db = SessionLocal()
    try:
        return db.query(RuntimeEvent).order_by(RuntimeEvent.timestamp.desc()).limit(limit).all()
    finally:
        db.close()
