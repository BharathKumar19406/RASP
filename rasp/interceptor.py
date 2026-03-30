from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
import traceback
from .feature_extractor import extract_features
from .baseline_profiler import update_baseline
from .drift_analyzer import detect_drift
from .classifier import classify_attack
from .mitigator import is_blocked, apply_mitigation
from .rate_limiter import RateLimiter
from .tool_aware_rate_limiter import ToolAwareRateLimiter
from config.settings import settings
from config.constants import WHITELIST_IPS, ENDPOINT_RATE_LIMITS, get_risk_level
from monitoring.logger import log_event, log_rate_limit_violation

class RASPMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter(settings.RATE_LIMIT_STRATEGY)
        self.tool_aware_limiter = ToolAwareRateLimiter()  # Enhanced limiter for tools
    
    async def dispatch(self, request: Request, call_next):
        if "/health" in request.url.path:
            return await call_next(request)

        ip = request.client.host if request.client else "127.0.0.1"
        endpoint = request.url.path
        user_agent = request.headers.get("user-agent", "")
        
        # Read body for analysis (will be re-read later)
        body_bytes = await request.body()
        body_sample = body_bytes.decode("utf-8", errors="ignore")[:2000]
        
        # ==================== ENHANCED RATE LIMITING (Tools + Brute Force) ====================
        if settings.RATE_LIMITING_ENABLED and ip not in WHITELIST_IPS:
            # Use tool-aware limiter (detects Arjun, FFuf, brute force, fuzzing, etc)
            allowed, rate_info = self.tool_aware_limiter.check_enhanced_rate_limit(
                ip, endpoint, user_agent, body_sample
            )
            
            if not allowed:
                # Rate limit exceeded
                if settings.TRACK_RATE_LIMIT_VIOLATIONS:
                    log_rate_limit_violation(ip, endpoint, rate_info)
                
                if settings.BLOCK_ON_RATE_LIMIT:
                    apply_mitigation("block", ip)
                    
                    tool_info = rate_info.get("tool", "")
                    pattern_info = rate_info.get("pattern", "")
                    
                    if tool_info:
                        return Response(
                            f"Rate limit exceeded: Attack tool detected ({tool_info.upper()}). "
                            f"Max {rate_info['max']} requests per {rate_info['reset_in']} seconds.",
                            status_code=429
                        )
                    elif pattern_info:
                        return Response(
                            f"Rate limit exceeded: {pattern_info.upper()} attack detected. "
                            f"Max {rate_info['max']} requests per {rate_info['reset_in']} seconds.",
                            status_code=429
                        )
                    else:
                        return Response(
                            f"Rate limit exceeded: {rate_info['max']} requests per {rate_info['reset_in']} seconds. "
                            f"Reason: {rate_info['reason']}",
                            status_code=429
                        )
        
        # ==================== RASP SECURITY ANALYSIS ====================
        if is_blocked(ip):
            return Response("IP temporarily blocked", status_code=403)

        try:
            # Body already read in rate limiting section above
            features = extract_features(request, body_sample)
            
            method = request.method
            
            # Update baseline and track adaptation
            adaptation_info = update_baseline(endpoint, method, features)
            drift_score = detect_drift(endpoint, method, features.body_size)
            
            # Classify attacks (with IP for behavioral detection)
            attack = classify_attack(
                endpoint=endpoint,
                method=method,
                body=body_sample,
                headers=dict(request.headers),
                features=features,
                drift_score=drift_score,
                ip=ip,
                response_status=200  # Default; behavioral detector can update based on patterns
            )
            risk_level = get_risk_level(drift_score)
            
            # Log event with adaptation info and full details
            log_event(features, drift_score, risk_level, attack, adaptation_info, body_sample)
            
            # Block on multiple conditions:
            # 1. HIGH drift score (behavioral anomaly)
            # 2. CRITICAL/HIGH risk attack detected (tool, brute force, etc)
            block_request = False
            block_reason = ""
            
            if risk_level == "HIGH":
                block_request = True
                block_reason = "High-risk behavioral anomaly"
            elif attack.get("risk_level") in ["CRITICAL", "HIGH"]:
                block_request = True
                block_reason = f"Attack detected: {attack.get('type', 'Unknown')}"
            
            if block_request:
                apply_mitigation("block", ip)
                return Response(f"Request blocked: {block_reason}", status_code=403)

        except Exception as e:
            print(f"⚠️ RASP ERROR: {e}")
            traceback.print_exc()

        return await call_next(request)
