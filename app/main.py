# app/main.py
from fastapi import FastAPI, Request
from rasp.interceptor import RASPMiddleware

app = FastAPI()
app.add_middleware(RASPMiddleware)

@app.get("/health")
def health():
    return {"status": "OK"}

# ✅ Add this: Catch-all route to let RASP process all paths
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(path: str, request: Request):
    # Return 200 so RASP can analyze the request
    return {"message": f"Path {path} processed by RASP", "method": request.method}
