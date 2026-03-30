import json
from statistics import quantiles
from storage.redis_client import get_redis

def update_baseline(endpoint: str, method: str, features):
    """Update baseline profile and return adaptation info"""
    r = get_redis()
    key = f"baseline:{endpoint}:{method}"
    data = r.get(key)
    baseline = json.loads(data) if data else {"sizes": []}
    
    baseline["sizes"].append(features.body_size)
    baseline["sizes"] = baseline["sizes"][-1000:]
    
    baseline_before = baseline.get("adaptive_high", 30)
    adapted = False
    
    if len(baseline["sizes"]) >= 50:
        try:
            p95 = quantiles(baseline["sizes"], n=100)[94]
            new_adaptive_high = min(p95 * 3.0, 10000)
            if new_adaptive_high != baseline_before:
                baseline["adaptive_high"] = new_adaptive_high
                adapted = True
            else:
                baseline["adaptive_high"] = new_adaptive_high
        except:
            pass
    
    r.set(key, json.dumps(baseline))
    
    return {
        "baseline_before": baseline_before,
        "baseline_after": baseline.get("adaptive_high", baseline_before),
        "adapted": adapted
    }


def get_baseline_info(endpoint: str, method: str) -> dict:
    """Get current baseline information for an endpoint"""
    r = get_redis()
    key = f"baseline:{endpoint}:{method}"
    data = r.get(key)
    
    if not data:
        return {"exists": False}
    
    baseline = json.loads(data)
    return {
        "exists": True,
        "adaptive_high": baseline.get("adaptive_high", 30),
        "samples_count": len(baseline.get("sizes", []))
    }
