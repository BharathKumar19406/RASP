"""
Centralized constants and thresholds for RASP system
Replaces hardcoded values scattered throughout the codebase
"""

# ============================================================================
# RISK LEVEL THRESHOLDS
# ============================================================================

RISK_THRESHOLDS = {
    "HIGH": 30,      # Drift score >= 30 is HIGH risk
    "MEDIUM": 15,    # Drift score >= 15 is MEDIUM risk
    "LOW": 0,        # Drift score >= 0 is LOW risk
}


def get_risk_level(drift_score: float) -> str:
    """
    Determine risk level based on drift score
    
    Args:
        drift_score: Numerical drift score
    
    Returns:
        Risk level: "HIGH", "MEDIUM", or "LOW"
    """
    if drift_score >= RISK_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif drift_score >= RISK_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    else:
        return "LOW"


# ============================================================================
# RATE LIMITING DEFAULTS
# ============================================================================

RATE_LIMIT_DEFAULTS = {
    "enabled": True,
    "strategy": "token_bucket",  # token_bucket, sliding_window, fixed_window, adaptive
    "default_requests": 10,
    "window_seconds": 1,
    "block_on_limit": True,
    "block_duration": 300,  # 5 minutes
    "track_violations": True,
}

# Per-endpoint rate limit configurations
ENDPOINT_RATE_LIMITS = {
    "default": {"max_requests": 10, "window_seconds": 1},
    "/login": {"max_requests": 5, "window_seconds": 60},
    "/api/auth": {"max_requests": 5, "window_seconds": 60},
    "/api/users": {"max_requests": 100, "window_seconds": 1},
    "/upload": {"max_requests": 2, "window_seconds": 1},
    "/export": {"max_requests": 1, "window_seconds": 10},
}

# IPs to whitelist (bypass rate limiting)
WHITELIST_IPS = [
    "127.0.0.1",    # localhost
    "::1",          # IPv6 localhost
]


# ============================================================================
# BASELINE PROFILING THRESHOLDS
# ============================================================================

BASELINE_CONFIG = {
    "min_samples": 50,           # Minimum requests before profiling starts
    "update_frequency": 100,     # Update baseline every N requests
    "anomaly_threshold": 2.0,    # Z-score threshold for anomaly
    "ttl_seconds": 86400,        # 24 hours
}


# ============================================================================
# DRIFT ANALYSIS SETTINGS
# ============================================================================

DRIFT_CONFIG = {
    "window_size": 100,          # Requests to analyze for drift
    "drift_threshold": 0.15,     # 15% change triggers drift alert
    "min_change_significance": 5, # Minimum change in % to be significant
}


# ============================================================================
# FEATURE EXTRACTION BOUNDARIES
# ============================================================================

FEATURE_BOUNDARIES = {
    "max_params": 50,            # Maximum expected parameters
    "max_body_size": 10 * 1024,  # 10KB max body
    "max_url_length": 2048,      # Max URL length
    "max_header_count": 100,     # Max headers
}


# ============================================================================
# ATTACK DETECTION CONFIDENCE LEVELS
# ============================================================================

CONFIDENCE_LEVELS = {
    "HIGH": 0.8,     # >= 80% confidence
    "MEDIUM": 0.5,   # 50-79% confidence
    "LOW": 0.3,      # 30-49% confidence
}


# ============================================================================
# ADAPTATION & MITIGATIONP SETTINGS
# ============================================================================

ADAPTATION_CONFIG = {
    "enabled": True,
    "baseline_shift_threshold": 0.2,  # 20% shift triggers adaptation
    "cooldown_seconds": 300,          # 5 minutes between major adaptations
    "max_adaptation_level": 5,        # Maximum adaptation iterations
}

MITIGATION_CONFIG = {
    "safe_mode": True,                # Safe mode enabled by default
    "log_mitigations": True,          # Log all mitigations
    "block_dangerous": True,          # Block dangerous requests
}


# ============================================================================
# LOGGING SETTINGS
# ============================================================================

LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "rasp.log",
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
}

VIOLATION_LOG_CONFIG = {
    "enabled": True,
    "file": "rate_limit_violations.log",
    "attack_log_file": "attack_logs.log",
}


# ============================================================================
# REDIS SETTINGS
# ============================================================================

REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "default_ttl": 3600,  # 1 hour
    "connection_timeout": 5,
}


# ============================================================================
# DATABASE SETTINGS
# ============================================================================

DATABASE_CONFIG = {
    "url": "sqlite:///./rasp_events.db",
    "echo": False,  # Set to True for SQL debugging
}


# ============================================================================
# API RESPONSE CODES
# ============================================================================

HTTP_CODES = {
    "OK": 200,
    "BAD_REQUEST": 400,
    "FORBIDDEN": 403,
    "RATE_LIMIT": 429,
    "SERVER_ERROR": 500,
}


# ============================================================================
# SECURITY HEADERS
# ============================================================================

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


# ============================================================================
# COMMON PATTERNS & REGEX
# ============================================================================

DETECTION_PATTERNS = {
    # SQL Injection patterns
    "SQL_KEYWORDS": r"(?i)(union\s+select|or\s*=\s*1|drop\s+table|delete\s+from|insert\s+into)",
    
    # XSS patterns
    "XSS_TAGS": r"(?i)(<script|javascript:|on\w+\s*=|<iframe)",
    
    # Command Injection patterns
    "COMMAND_INJECTION": r"(;\s*cat\s|&&\s*id|[`$]\s*\(|\\|\s*ls)",
    
    # Path Traversal patterns
    "PATH_TRAVERSAL": r"(\.\./|\.\.\\|%2e%2e)",
    
    # XXE patterns
    "XXE": r"(?i)(<!DOCTYPE|<!ENTITY|SYSTEM)",
}
