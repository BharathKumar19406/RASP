import re
from dataclasses import dataclass
from fastapi import Request
from utils.crypto import hash_ip

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
    ip_hash = hash_ip(ip)
    ua = request.headers.get("user-agent", "")
    
    body_size = len(body)
    param_count = len(request.query_params)
    
    # Combined analysis of path, query, and body for thorough detection
    full_request_text = f"{endpoint} ?{request.url.query} {body}"
    
    has_sql = bool(re.search(r"(?i)(union\s+select|or\s+1\s*=\s*1|' OR '|\-\-)", full_request_text))
    has_xss = bool(re.search(r"<script|javascript:|alert\(|onerror=|onload=", full_request_text, re.IGNORECASE))
    has_path_traversal = bool(re.search(r"\.\./|\.\.\\|/etc/passwd|/etc/shadow|windows/system32|boot\.ini", full_request_text, re.IGNORECASE))
    has_ssr = bool(re.search(r"127\.0\.0\.1|localhost|169\.254\.169\.254|metadata\.google\.internal", full_request_text, re.IGNORECASE))
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
