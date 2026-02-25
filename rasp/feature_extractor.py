from fastapi import Request
from rasp.models import RequestFeatures
import time

def extract_features(request: Request) -> RequestFeatures:
    endpoint = request.url.path
    method = request.method
    ip = request.client.host if request.client else "127.0.0.1"
    param_count = len(request.query_params)
    
    body_size = 0
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit():
        body_size = int(content_length)
    
    return RequestFeatures(
        endpoint=endpoint,
        method=method,
        ip=ip,
        param_count=param_count,
        body_size=body_size,
        timestamp=time.time()
    )
