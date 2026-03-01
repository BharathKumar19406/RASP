from fastapi import FastAPI
from rasp.interceptor import RASPMiddleware
from utils.auth import get_current_user

app = FastAPI(title="RASP Protected Application")

app.add_middleware(RASPMiddleware)

@app.get("/health")
def health():
    return {"status": "OK"}

@app.post("/api/login")
def login():
    return {"message": "Logged in"}

@app.post("/api/transfer")
def transfer():
    return {"status": "transferred"}

@app.delete("/api/delete-account")
def delete_account():
    return {"status": "scheduled"}
