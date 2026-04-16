# app/main.py
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from rasp.interceptor import RASPMiddleware
from storage.db import SessionLocal
from storage.models import RuntimeEvent

app = FastAPI()
app.add_middleware(RASPMiddleware)

class FlagRequest(BaseModel):
    is_flagged: bool

@app.post("/api/events/{event_id}/flag")
def flag_event(event_id: str, request: FlagRequest):
    db = SessionLocal()
    try:
        event = db.query(RuntimeEvent).filter(RuntimeEvent.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        event.is_flagged = request.is_flagged
        db.commit()
        return {"status": "success", "event_id": event.id, "is_flagged": event.is_flagged}
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "OK"}

# ✅ Add this: Catch-all route to let RASP process all paths
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(path: str, request: Request):
    # Return 200 so RASP can analyze the request
    return {"message": f"Path {path} processed by RASP", "method": request.method}
