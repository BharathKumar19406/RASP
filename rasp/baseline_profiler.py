import json
import statistics
from storage.redis_client import get_redis

def get_baseline_key(endpoint: str) -> str:
    return f"baseline:{endpoint}"

def update_baseline(endpoint: str, features):
    r = get_redis()
    key = get_baseline_key(endpoint)
    
    baseline = {}
    if r.exists(key):
        baseline = json.loads(r.get(key))
    else:
        baseline = {"param_counts": [], "body_sizes": [], "access_count": 0}
    
    baseline["param_counts"].append(features.param_count)
    baseline["body_sizes"].append(features.body_size)
    baseline["access_count"] += 1
    
    # Keep only last 100 samples
    baseline["param_counts"] = baseline["param_counts"][-100:]
    baseline["body_sizes"] = baseline["body_sizes"][-100:]
    
    r.set(key, json.dumps(baseline))

def get_baseline(endpoint: str):
    r = get_redis()
    key = get_baseline_key(endpoint)
    if r.exists(key):
        return json.loads(r.get(key))
    return None
