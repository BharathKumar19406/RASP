from config.settings import settings
import redis

_r = None

def get_redis():
    global _r
    if _r is None:
        _r = redis.from_url(settings.REDIS_URL)
    return _r
