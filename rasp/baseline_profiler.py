# rasp/baseline_profiler.py
import json
import redis
from config.settings import settings

r = redis.from_url(settings.REDIS_URL)

def get_baseline_key(endpoint: str, user_role: str = "user", geo_region: str = "GLOBAL") -> str:
    return f"baseline:{user_role}:{geo_region}:{endpoint}"

def update_baseline(endpoint: str, features):
    key = get_baseline_key(endpoint, features.user_role)
    print(f"[BASELINE] Saving to key: {key}")
    data = r.get(key)
    baseline = json.loads(data) if data else {
        "body_sizes": [],
        "param_counts": [],
        "access_count": 0,
        "recent_hashes": []
    }

    baseline["body_sizes"].append(features.body_size)
    baseline["param_counts"].append(features.param_count)
    baseline["access_count"] += 1
    if features.body_hash:
        baseline["recent_hashes"].append(features.body_hash)
        baseline["recent_hashes"] = baseline["recent_hashes"][-10:]

    r.set(key, json.dumps(baseline))
