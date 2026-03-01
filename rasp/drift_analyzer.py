# rasp/drift_analyzer.py
import json
import statistics
from config.settings import settings
from storage.redis_client import get_redis

def detect_drift(endpoint: str, features) -> float:
    r = get_redis()
    
    # ✅ EXACT same key as baseline_profiler.py
    key = f"baseline:{features.user_role}:GLOBAL:{endpoint}"
    print(f"[DRIFT] Looking for key: {key}")
    data = r.get(key)
    if not data:
        # Fallback to legacy (for safety)
        key_legacy = f"baseline:{endpoint}"
        data = r.get(key_legacy)
        if not data:
            return 0.0

    try:
        baseline = json.loads(data)
    except Exception:
        return 0.0

    body_sizes = baseline.get("body_sizes", [])
    if not body_sizes:
        return 0.0

    avg_body = statistics.mean(body_sizes)
    if avg_body <= 0:
        return 0.0

    ratio = features.body_size / avg_body
    # ✅ Simple, reliable scoring: ratio * 10 (capped at 100)
    score = min(ratio * 10, 100.0)

    # 🔍 Debug: Print to terminal (remove in prod)
    print(f"[DRIFT] Endpoint={endpoint} | Body={features.body_size} | Avg={avg_body:.1f} | Ratio={ratio:>.1f} | Score={score:.1f}")

    return score
