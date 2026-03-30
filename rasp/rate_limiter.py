"""
Rate Limiting Module for RASP
Supports multiple strategies: Token Bucket, Sliding Window, Fixed Window, Adaptive
"""

import time
import json
from typing import Dict, Tuple
from storage.redis_client import get_redis
from utils.redis_keys import RedisKeyBuilder
from config.constants import ENDPOINT_RATE_LIMITS, WHITELIST_IPS
import math

class RateLimitStrategy:
    """Base class for rate limiting strategies"""
    
    def check_rate_limit(self, ip: str, endpoint: str, max_requests: int, window_seconds: int) -> Tuple[bool, Dict]:
        """
        Check if request is allowed
        Returns: (allowed: bool, info: dict with remaining, reset_in, etc.)
        """
        raise NotImplementedError

    def reset(self, ip: str):
        """Reset rate limit for IP"""
        raise NotImplementedError


class TokenBucketRateLimiter(RateLimitStrategy):
    """
    Token Bucket Algorithm
    - Smooth traffic handling
    - Allows burst traffic up to bucket size
    - Best for: APIs with variable traffic patterns
    """
    
    def check_rate_limit(self, ip: str, endpoint: str, max_requests: int, window_seconds: int) -> Tuple[bool, Dict]:
        r = get_redis()
        key = RedisKeyBuilder.rate_limit_token_bucket(ip, endpoint)
        bucket_key = f"{key}:bucket"
        last_refill_key = f"{key}:last_refill"
        
        now = time.time()
        bucket_data = r.get(bucket_key)
        last_refill = float(r.get(last_refill_key) or now)
        
        if bucket_data:
            bucket = json.loads(bucket_data)
            tokens = bucket.get("tokens", max_requests)
        else:
            tokens = max_requests
        
        # Refill tokens based on time elapsed
        time_passed = now - last_refill
        refill_rate = max_requests / window_seconds
        new_tokens = min(max_requests, tokens + (time_passed * refill_rate))
        
        if new_tokens >= 1:
            # Allow request
            remaining = int(new_tokens - 1)
            bucket_data = {"tokens": new_tokens - 1}
            r.setex(bucket_key, window_seconds, json.dumps(bucket_data))
            r.setex(last_refill_key, window_seconds, str(now))
            
            return True, {
                "remaining": remaining,
                "reset_in": window_seconds,
                "strategy": "token_bucket"
            }
        else:
            # Reject request
            reset_in = (1 - new_tokens) / refill_rate
            return False, {
                "remaining": 0,
                "reset_in": int(reset_in) + 1,
                "strategy": "token_bucket"
            }


class SlidingWindowRateLimiter(RateLimitStrategy):
    """
    Sliding Window Algorithm
    - Tracks exact request timestamps
    - Most accurate but higher memory
    - Best for: Strict rate limiting requirements
    """
    
    def check_rate_limit(self, ip: str, endpoint: str, max_requests: int, window_seconds: int) -> Tuple[bool, Dict]:
        r = get_redis()
        key = RedisKeyBuilder.rate_limit_sliding_window(ip, endpoint)
        
        now = time.time()
        window_start = now - window_seconds
        
        # Remove old requests
        r.zremrangebyscore(key, 0, window_start)
        
        # Count requests in current window
        request_count = r.zcard(key)
        
        if request_count < max_requests:
            # Allow request - add timestamp
            r.zadd(key, {str(now): now})
            r.expire(key, window_seconds + 1)
            
            return True, {
                "remaining": max_requests - request_count - 1,
                "reset_in": window_seconds,
                "strategy": "sliding_window"
            }
        else:
            # Reject request
            oldest_request = r.zrange(key, 0, 0, withscores=True)
            if oldest_request:
                reset_in = int(oldest_request[0][1] + window_seconds - now) + 1
            else:
                reset_in = window_seconds
            
            return False, {
                "remaining": 0,
                "reset_in": reset_in,
                "strategy": "sliding_window"
            }


class FixedWindowRateLimiter(RateLimitStrategy):
    """
    Fixed Window Algorithm
    - Simple, low memory
    - May allow burst at window boundaries
    - Best for: Simple, high-throughput APIs
    """
    
    def check_rate_limit(self, ip: str, endpoint: str, max_requests: int, window_seconds: int) -> Tuple[bool, Dict]:
        r = get_redis()
        key = RedisKeyBuilder.rate_limit_fixed_window(ip, endpoint)
        
        current_count = r.incr(key)
        
        if current_count == 1:
            # First request in this window
            r.expire(key, window_seconds)
        
        time_to_reset = r.ttl(key)
        
        if current_count <= max_requests:
            return True, {
                "remaining": max_requests - current_count,
                "reset_in": time_to_reset if time_to_reset > 0 else window_seconds,
                "strategy": "fixed_window"
            }
        else:
            return False, {
                "remaining": 0,
                "reset_in": time_to_reset if time_to_reset > 0 else window_seconds,
                "strategy": "fixed_window"
            }


class AdaptiveRateLimiter(RateLimitStrategy):
    """
    Adaptive Rate Limiting
    - Adjusts limits based on traffic patterns
    - Increases during normal traffic, tightens during anomalies
    - Best for: Advanced threat response
    """
    
    def check_rate_limit(self, ip: str, endpoint: str, max_requests: int, window_seconds: int) -> Tuple[bool, Dict]:
        r = get_redis()
        key = RedisKeyBuilder.rate_limit_adaptive(ip, endpoint)
        stats_key = f"ratelimit:stats:{ip}:{endpoint}"
        
        now = time.time()
        
        # Get traffic stats
        stats_data = r.get(stats_key)
        if stats_data:
            stats = json.loads(stats_data)
        else:
            stats = {"avg_rate": 0, "spike_count": 0, "last_check": now}
        
        # Increment request count in fixed window
        window_key = f"{key}:{int(now / window_seconds)}"
        current_count = r.incr(window_key)
        r.expire(window_key, window_seconds + 1)
        
        # Calculate current rate
        current_rate = current_count
        
        # Detect anomalies (spike = 3x average)
        if stats["avg_rate"] > 0 and current_rate > stats["avg_rate"] * 3:
            stats["spike_count"] += 1
            # Reduce limit during spike
            adjusted_limit = max(5, int(max_requests * 0.5))
        else:
            stats["spike_count"] = max(0, stats["spike_count"] - 1)
            # Gradually increase limit back to normal
            adjusted_limit = max_requests
        
        # Update average rate (exponential moving average)
        alpha = 0.3
        stats["avg_rate"] = alpha * current_rate + (1 - alpha) * stats["avg_rate"]
        stats["last_check"] = now
        r.setex(stats_key, window_seconds * 10, json.dumps(stats))
        
        if current_count <= adjusted_limit:
            return True, {
                "remaining": adjusted_limit - current_count,
                "reset_in": window_seconds,
                "strategy": "adaptive",
                "adjusted_limit": adjusted_limit,
                "anomaly_level": stats["spike_count"]
            }
        else:
            return False, {
                "remaining": 0,
                "reset_in": window_seconds,
                "strategy": "adaptive",
                "adjusted_limit": adjusted_limit,
                "anomaly_level": stats["spike_count"]
            }


class RateLimiter:
    """Main rate limiter with strategy selection"""
    
    def __init__(self, strategy: str = "token_bucket"):
        """Initialize rate limiter with strategy"""
        self.strategy_name = strategy
        
        if strategy == "token_bucket":
            self.limiter = TokenBucketRateLimiter()
        elif strategy == "sliding_window":
            self.limiter = SlidingWindowRateLimiter()
        elif strategy == "fixed_window":
            self.limiter = FixedWindowRateLimiter()
        elif strategy == "adaptive":
            self.limiter = AdaptiveRateLimiter()
        else:
            # Default to token bucket
            self.limiter = TokenBucketRateLimiter()
    
    def check_rate_limit(self, ip: str, endpoint: str, max_requests: int, window_seconds: int) -> Tuple[bool, Dict]:
        """Check if request is allowed"""
        return self.limiter.check_rate_limit(ip, endpoint, max_requests, window_seconds)
    
    def reset(self, ip: str):
        """Reset rate limit for IP"""
        return self.limiter.reset(ip)
