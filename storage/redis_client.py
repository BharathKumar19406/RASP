from config.settings import settings
import redis
import fakeredis

_r = None
def get_redis():
    global _r
    if _r is None:
        try:
            _r = redis.from_url(settings.REDIS_URL)
            # Test connection
            _r.ping()
        except Exception as e:
            print(f"⚠️ Redis connection failed ({e}), using fake Redis for testing")
            _r = fakeredis.FakeStrictRedis()
    return _r
