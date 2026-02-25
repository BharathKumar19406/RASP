from fastapi import FastAPI
from rasp.interceptor import RASPMiddleware
from app.routes import public, protected

app = FastAPI(title="RASP-Protected Application")

app.add_middleware(RASPMiddleware)

app.include_router(public.router)
app.include_router(protected.router)

@app.get("/health")
def health_check():
    return {"status": "OK"}
