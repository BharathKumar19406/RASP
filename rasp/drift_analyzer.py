import json
from storage.redis_client import get_redis

def detect_drift(endpoint: str, method: str, body_size: int) -> float:
    r = get_redis()
    key = f"baseline:{endpoint}:{method}"
    data = r.get(key)
    if not data:
        return 0.0
    
    baseline = json.loads(data)
    adaptive_high = baseline.get("adaptive_high", 30)
    ratio = body_size / adaptive_high if adaptive_high > 0 else 0
    return min(ratio * 10, 100.0)
