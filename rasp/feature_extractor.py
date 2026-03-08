import hashlib
import re
from dataclasses import dataclass
from fastapi import Request

@dataclass
class RequestFeatures:
    endpoint: str
    method: str
    ip: str
    ip_hash: str
    user_agent: str
    body_size: int
    param_count: int
    has_sql: bool
    has_xss: bool
    has_path_traversal: bool
    has_ssr: bool
    has_jwt: bool

def extract_features(request: Request, body: str) -> RequestFeatures:
    endpoint = request.url.path
    method = request.method
    ip = request.client.host if request.client else "127.0.0.1"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
    ua = request.headers.get("user-agent", "")
    
    body_size = len(body)
    param_count = len(request.query_params)
    
    has_sql = bool(re.search(r"(?i)(union\s+select|or\s+1\s*=\s*1)", body))
    has_xss = bool(re.search(r"<script|javascript:", body, re.IGNORECASE))
    has_path_traversal = "../" in body or "..\\" in body
    has_ssr = "127.0.0.1" in body or "localhost" in body
    has_jwt = "Authorization" in request.headers and "Bearer " in request.headers["Authorization"]

    return RequestFeatures(
        endpoint=endpoint,
        method=method,
        ip=ip,
        ip_hash=ip_hash,
        user_agent=ua,
        body_size=body_size,
        param_count=param_count,
        has_sql=has_sql,
        has_xss=has_xss,
        has_path_traversal=has_path_traversal,
        has_ssr=has_ssr,
        has_jwt=has_jwt
    )
