from fastapi import Request
from dataclasses import dataclass
import hashlib
import time
import re 
import jwt
from utils.auth import get_current_user

@dataclass
class RequestFeatures:
    endpoint: str
    method: str
    ip: str
    ip_hash: str
    user_role: str
    param_count: int
    body_size: int
    request_rate: int = 1
    body_hash: str = ""
    sql_keyword_count: int = 0

def extract_features(request: Request, body_sample: str = "") -> RequestFeatures:
    endpoint = request.url.path
    method = request.method
    ip = request.client.host if request.client else "127.0.0.1"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    # User role from JWT (mocked)
    user_role = "admin" if "admin" in get_current_user().lower() else "user"
    
    param_count = len(request.query_params)
    body_size = 0
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit():
        body_size = int(content_length)
    
    # Body hash (for repetition detection)
    body_hash = ""
    if body_sample:
        body_hash = hashlib.sha256(body_sample.encode()).hexdigest()[:16]
    
    # SQL keyword count (safe mode only)
    sql_keyword_count = 0
    if body_sample and len(body_sample) > 100:
        patterns = [
            r"(?i)(union\s+select|select\s+\*\s+from|insert\s+into|drop\s+table)",
            r"(?i)(or\s+1\s*=\s*1|and\s+1\s*=\s*1|sleep\(\d+\))",
        ]
        for p in patterns:
            sql_keyword_count += len(re.findall(p, body_sample))
    
    return RequestFeatures(
        endpoint=endpoint,
        method=method,
        ip=ip,
        ip_hash=ip_hash,
        user_role=user_role,
        param_count=param_count,
        body_size=body_size,
        body_hash=body_hash,
        sql_keyword_count=sql_keyword_count
    )
