from config.settings import settings
from storage.redis_client import get_redis

def is_blocked(ip: str) -> bool:
    if settings.SAFE_MODE:
        return False
    r = get_redis()
    return r.exists(f"blocked:{ip}")

def apply_mitigation(action: str, ip: str):
    if settings.SAFE_MODE:
        print(f"[SAFE MODE] Would have {action} IP: {ip}")
        return
    r = get_redis()
    if action == "block":
        r.setex(f"blocked:{ip}", 300, "1")
