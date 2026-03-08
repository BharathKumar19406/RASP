import json
from statistics import quantiles
from storage.redis_client import get_redis

def update_baseline(endpoint: str, method: str, features):
    r = get_redis()
    key = f"baseline:{endpoint}:{method}"
    data = r.get(key)
    baseline = json.loads(data) if data else {"sizes": []}
    
    baseline["sizes"].append(features.body_size)
    baseline["sizes"] = baseline["sizes"][-1000:]
    
    if len(baseline["sizes"]) >= 50:
        try:
            p95 = quantiles(baseline["sizes"], n=100)[94]
            baseline["adaptive_high"] = min(p95 * 3.0, 10000)
        except:
            pass
    
    r.set(key, json.dumps(baseline))
