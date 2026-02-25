from storage.redis_client import get_redis
from config.settings import settings  # ← NEW

def apply_mitigation(action: str, ip: str):
    if settings.SAFE_MODE:
        print(f"[SAFE MODE] Would have {action}ed IP: {ip}")
        return
    
    r = get_redis()
    if action == "block":
        r.setex(f"blocked:{ip}", 300, "1")
    elif action == "rate_limit":
        key = f"rate:{ip}"
        current = r.get(key)
        limit = 20
        if current is None:
            r.setex(key, 60, 1)
        else:
            count = int(current)
            if count >= limit:
                r.setex(f"blocked:{ip}", 300, "1")
            else:
                r.incr(key)

def is_blocked(ip: str) -> bool:
    if settings.SAFE_MODE:
        return False
    r = get_redis()
    return r.exists(f"blocked:{ip}")
