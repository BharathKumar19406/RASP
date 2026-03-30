import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DB_URL = os.getenv("DB_URL")
    REDIS_URL = os.getenv("REDIS_URL")
    LOG_SECRET_KEY = os.getenv("LOG_SECRET_KEY", "default-secret")
    SAFE_MODE = os.getenv("SAFE_MODE", "false").lower() == "true"
    
    # Rate Limiting Settings
    RATE_LIMITING_ENABLED = os.getenv("RATE_LIMITING_ENABLED", "true").lower() == "true"
    RATE_LIMIT_STRATEGY = os.getenv("RATE_LIMIT_STRATEGY", "token_bucket")  
    # Options: token_bucket, sliding_window, fixed_window, adaptive
    
    # Default rate limit: 10 requests per second per IP
    RATE_LIMIT_DEFAULT_REQUESTS = int(os.getenv("RATE_LIMIT_DEFAULT_REQUESTS", "10"))
    RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "1"))
    
    # Block IP after rate limit exceeded
    BLOCK_ON_RATE_LIMIT = os.getenv("BLOCK_ON_RATE_LIMIT", "true").lower() == "true"
    RATE_LIMIT_BLOCK_DURATION = int(os.getenv("RATE_LIMIT_BLOCK_DURATION", "300"))  # 5 minutes
    
    # Track rate limit violations
    TRACK_RATE_LIMIT_VIOLATIONS = os.getenv("TRACK_RATE_LIMIT_VIOLATIONS", "true").lower() == "true"

settings = Settings()
