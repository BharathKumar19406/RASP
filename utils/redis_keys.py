"""
Centralized Redis key generation to avoid hardcoded key patterns
Provides type-safe key building for all Redis operations
"""


class RedisKeyBuilder:
    """Build Redis keys consistently across the application"""

    # Rate Limiting Keys
    @staticmethod
    def rate_limit_token_bucket(ip: str, endpoint: str) -> str:
        """Token bucket rate limiting key"""
        return f"ratelimit:token_bucket:{ip}:{endpoint}"

    @staticmethod
    def rate_limit_sliding_window(ip: str, endpoint: str) -> str:
        """Sliding window rate limiting key"""
        return f"ratelimit:sliding_window:{ip}:{endpoint}"

    @staticmethod
    def rate_limit_fixed_window(ip: str, endpoint: str) -> str:
        """Fixed window rate limiting key"""
        return f"ratelimit:fixed_window:{ip}:{endpoint}"

    @staticmethod
    def rate_limit_adaptive(ip: str, endpoint: str) -> str:
        """Adaptive rate limiting key"""
        return f"ratelimit:adaptive:{ip}:{endpoint}"

    @staticmethod
    def rate_limit_counter(ip: str, endpoint: str) -> str:
        """Simple counter for enhanced rate limiting"""
        return f"ratelimit:counter:{ip}:{endpoint}"

    # Tool-Aware Rate Limiting Keys
    @staticmethod
    def brute_force_attempts(ip: str, endpoint: str) -> str:
        """Track brute force attempts per IP/endpoint"""
        return f"tool_aware:brute_force:{ip}:{endpoint}"

    @staticmethod
    def fuzzing_attempts(ip: str, endpoint: str) -> str:
        """Track fuzzing attempts per IP/endpoint"""
        return f"tool_aware:fuzzing:{ip}:{endpoint}"

    @staticmethod
    def endpoint_tracking(ip: str) -> str:
        """Track endpoints accessed by IP (scanner detection)"""
        return f"tool_aware:endpoints:{ip}"

    @staticmethod
    def blocked_ip(ip: str) -> str:
        """IP blocking key for enforcement"""
        return f"blocked:{ip}"

    # Baseline Profiling Keys
    @staticmethod
    def baseline_profile(endpoint: str, method: str) -> str:
        """Baseline profile key for features"""
        return f"baseline:{endpoint}:{method}"

    @staticmethod
    def baseline_stats(endpoint: str, method: str) -> str:
        """Statistics for baseline model"""
        return f"baseline_stats:{endpoint}:{method}"

    # Anomaly Detection Keys
    @staticmethod
    def anomaly_scores(ip: str) -> str:
        """Historical anomaly scores for an IP"""
        return f"anomaly:{ip}"

    @staticmethod
    def feature_distribution(endpoint: str) -> str:
        """Feature distribution statistics"""
        return f"features:{endpoint}"

    # Drift Analysis Keys
    @staticmethod
    def drift_state(endpoint: str) -> str:
        """Current drift state for endpoint"""
        return f"drift:{endpoint}"

    @staticmethod
    def drift_history(endpoint: str) -> str:
        """Historical drift data"""
        return f"drift_history:{endpoint}"

    # Session & User Keys
    @staticmethod
    def session(session_id: str) -> str:
        """User session key"""
        return f"session:{session_id}"

    @staticmethod
    def user_profile(user_id: str) -> str:
        """User profile and behavior"""
        return f"user:{user_id}"

    # Cache Keys
    @staticmethod
    def cache_key(namespace: str, identifier: str) -> str:
        """Generic cache key builder"""
        return f"cache:{namespace}:{identifier}"

    # Analytics Keys
    @staticmethod
    def attack_stats(endpoint: str) -> str:
        """Attack statistics per endpoint"""
        return f"stats:attacks:{endpoint}"

    @staticmethod
    def request_rate(endpoint: str) -> str:
        """Request rate metrics"""
        return f"metrics:requests:{endpoint}"
