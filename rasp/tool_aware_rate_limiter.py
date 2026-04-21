"""
Tool-Aware Rate Limiting Module
Specifically targets fuzzing tools, Arjun, brute force and other attack tools
with stricter, adaptive rate limits
"""

import time
import re
from typing import Dict, Tuple
from storage.redis_client import get_redis
from utils.redis_keys import RedisKeyBuilder
from config.constants import WHITELIST_IPS
from monitoring.logger import log_event

class ToolAwareRateLimiter:
    """
    Advanced rate limiter that detects attack tools and applies tool-specific limits
    """
    
    # Attack tool signatures
    ATTACK_TOOL_SIGNATURES = {
        # Fuzzing & Scanning
        "arjun": {
            "user_agent": r"(?i)(arjun|arjun-v)",
            "patterns": ["arjun"],
            "requests_per_min": 1,  # 1 request per minute
            "risk_level": "CRITICAL"
        },
        "ffuf": {
            "user_agent": r"(?i)(ffuf|fuzz)",
            "patterns": ["ffuf"],
            "requests_per_min": 2,
            "risk_level": "CRITICAL"
        },
        "dirbuster": {
            "user_agent": r"(?i)(dirbuster|dirb)",
            "patterns": ["dirbuster", "dirb"],
            "requests_per_min": 1,
            "risk_level": "CRITICAL"
        },
        "gobuster": {
            "user_agent": r"(?i)(gobuster|go-buster)",
            "patterns": ["gobuster"],
            "requests_per_min": 2,
            "risk_level": "CRITICAL"
        },
        "wfuzz": {
            "user_agent": r"(?i)(wfuzz)",
            "patterns": ["wfuzz"],
            "requests_per_min": 1,
            "risk_level": "CRITICAL"
        },
        "commix": {
            "user_agent": r"(?i)(commix)",
            "patterns": ["commix"],
            "requests_per_min": 1,
            "risk_level": "CRITICAL"
        },
        "xsstrike": {
            "user_agent": r"(?i)(xsstrike)",
            "patterns": ["xsstrike"],
            "requests_per_min": 2,
            "risk_level": "CRITICAL"
        },
        "sqlmap": {
            "user_agent": r"(?i)(sqlmap)",
            "patterns": ["sqlmap"],
            "requests_per_min": 1,
            "risk_level": "CRITICAL"
        },
        "nmap": {
            "user_agent": r"(?i)(nmap)",
            "patterns": ["nmap"],
            "requests_per_min": 1,
            "risk_level": "CRITICAL"
        },
        "nikto": {
            "user_agent": r"(?i)(nikto)",
            "patterns": ["nikto"],
            "requests_per_min": 2,
            "risk_level": "CRITICAL"
        },
        "burp": {
            "user_agent": r"(?i)(burp|intruder|portswigger)",
            "patterns": ["burp", "intruder"],
            "requests_per_min": 5,
            "risk_level": "HIGH"
        },
    }
    
    # Brute force detection patterns
    BRUTE_FORCE_INDICATORS = {
        "high_error_rate": 0.8,      # 80% errors = brute force
        "rapid_sequential": True,     # Same user/password attempts
        "target_endpoints": ["/login", "/api/auth", "/api/password"],
        "requests_per_min": 3,        # Max 3 login attempts per minute
    }
    
    # Fuzzing detection
    FUZZING_INDICATORS = {
        "malformed_payloads": ["NULL", "FUZZ", "%s", "%x", "%n", "${", "{{"],
        "rapid_different_params": True,
        "common_fuzz_paths": ["/api/*", "/admin/*", "/config/*"],
        "requests_per_min": 2,
    }
    
    def __init__(self):
        self.r = get_redis()
    
    def detect_attack_tool(self, user_agent: str, endpoint: str, body: str) -> Tuple[str, Dict]:
        """
        Detect if request is from attack tool
        Returns: (tool_name, tool_config)
        """
        user_agent_lower = (user_agent or "").lower()
        
        for tool, config in self.ATTACK_TOOL_SIGNATURES.items():
            # Check User-Agent
            if re.search(config["user_agent"], user_agent_lower):
                return tool, config
            
            # Check body patterns
            for pattern in config["patterns"]:
                if pattern in body.lower():
                    return tool, config
        
        return None, {}
    
    def is_brute_force_pattern(self, ip: str, endpoint: str, body: str, response_status: int) -> bool:
        """
        Detect brute force attack patterns
        """
        # Check if endpoint is auth-related
        auth_endpoints = self.BRUTE_FORCE_INDICATORS["target_endpoints"]
        is_auth_endpoint = any(ep in endpoint.lower() for ep in auth_endpoints)
        
        if not is_auth_endpoint:
            return False
        
        # Track failed attempts per IP
        tracking_key = RedisKeyBuilder.brute_force_attempts(ip, endpoint)
        attempts = self.r.get(tracking_key)
        
        if attempts is None:
            attempts_data = {"total": 0, "failed": 0, "last_attempt": time.time()}
        else:
            attempts_data = eval(attempts)  # Parse stored dict
        
        # Check if response indicates failure (4xx errors)
        if response_status >= 400:
            attempts_data["failed"] += 1
        
        attempts_data["total"] += 1
        attempts_data["last_attempt"] = time.time()
        
        # Store updated attempts (TTL: 60 seconds)
        self.r.setex(tracking_key, 60, str(attempts_data))
        
        # Detect brute force: >50% failed attempts in short window
        if attempts_data["total"] >= 3:
            error_rate = attempts_data["failed"] / attempts_data["total"]
            if error_rate >= 0.5:
                return True
        
        return False
    
    def is_fuzzing_attack(self, ip: str, endpoint: str, body: str) -> bool:
        """
        Detect fuzzing/parameter pollution attacks
        """
        fuzzing_keywords = self.FUZZING_INDICATORS["malformed_payloads"]
        
        # Count fuzzing patterns in request
        pattern_count = sum(1 for kw in fuzzing_keywords if kw in body)
        
        if pattern_count >= 2:
            # Track fuzzing attempts
            tracking_key = RedisKeyBuilder.fuzzing_attempts(ip, endpoint)
            attempts = self.r.incr(tracking_key)
            self.r.expire(tracking_key, 60)  # 60 second window
            
            if attempts >= 3:  # 3+ fuzzing requests in 60s = attack
                return True
        
        return False
    
    def get_adaptive_limit(self, ip: str, endpoint: str, user_agent: str, body: str, response_status: int = 200) -> Dict:
        """
        Calculate adaptive rate limit based on request characteristics
        
        Returns: {
            "max_requests": int,
            "window_seconds": int,
            "reason": str,
            "risk_level": str
        }
        """
        
        # 1. Check for known attack tools (STRICTEST)
        tool, tool_config = self.detect_attack_tool(user_agent, endpoint, body)
        if tool:
            return {
                "max_requests": tool_config["requests_per_min"],
                "window_seconds": 60,
                "reason": f"Attack tool detected: {tool}",
                "risk_level": "CRITICAL",
                "tool": tool
            }
        
        # 2. Check for brute force patterns (VERY STRICT)
        if self.is_brute_force_pattern(ip, endpoint, body, response_status):
            return {
                "max_requests": 1,  # Only 1 request per minute
                "window_seconds": 60,
                "reason": "Brute force attack pattern detected",
                "risk_level": "CRITICAL",
                "pattern": "brute_force"
            }
        
        # 3. Check for fuzzing patterns (VERY STRICT)
        if self.is_fuzzing_attack(ip, endpoint, body):
            return {
                "max_requests": 1,
                "window_seconds": 60,
                "reason": "Fuzzing attack pattern detected",
                "risk_level": "CRITICAL",
                "pattern": "fuzzing"
            }
        
        # 4. Check for rapid endpoint switching (scanner behavior)
        scanner_limit = self._check_scanner_behavior(ip)
        if scanner_limit:
            return scanner_limit
        
        # 5. Default: Normal rate limits from configuration
        from config.constants import ENDPOINT_RATE_LIMITS
        config = ENDPOINT_RATE_LIMITS.get(endpoint, ENDPOINT_RATE_LIMITS["default"])
        
        return {
            "max_requests": config["max_requests"],
            "window_seconds": config["window_seconds"],
            "reason": "Normal request",
            "risk_level": "LOW"
        }
    
    def _check_scanner_behavior(self, ip: str) -> Dict:
        """
        Detect scanner behavior: rapid endpoint switching
        """
        tracking_key = RedisKeyBuilder.endpoint_tracking(ip)
        endpoints = self.r.get(tracking_key)
        
        if endpoints:
            endpoint_data = eval(endpoints)
            unique_endpoints = len(endpoint_data.get("endpoints", {}))
            
            # If accessing >15 different endpoints in 60s = scanner
            if unique_endpoints > 15:
                return {
                    "max_requests": 1,
                    "window_seconds": 60,
                    "reason": f"Scanner behavior detected: {unique_endpoints} endpoints in 60s",
                    "risk_level": "CRITICAL",
                    "pattern": "scanner"
                }
        
        return None
    
    def check_enhanced_rate_limit(self, ip: str, endpoint: str, user_agent: str, body: str, response_status: int = 200) -> Tuple[bool, Dict]:
        """
        Main function: Check if request should be allowed with tool-aware limits
        
        Returns: (allowed: bool, info: dict with remaining, reset_in, reason)
        """
        
        # Skip whitelist
        if ip in WHITELIST_IPS:
            return True, {"remaining": 9999, "reset_in": 0, "reason": "IP whitelisted"}
        
        # Get adaptive limit based on attack detection
        limit_config = self.get_adaptive_limit(ip, endpoint, user_agent, body, response_status)
        
        # Use simple counter for enhanced limits
        counter_key = RedisKeyBuilder.rate_limit_counter(ip, endpoint)
        current_count = self.r.incr(counter_key)
        
        if current_count == 1:
            # First request in this window
            self.r.expire(counter_key, limit_config["window_seconds"])
        
        max_requests = limit_config["max_requests"]
        window_seconds = limit_config["window_seconds"]
        
        allowed = current_count <= max_requests
        
        time_to_reset = self.r.ttl(counter_key)
        reset_in = time_to_reset if time_to_reset > 0 else window_seconds
        
        return allowed, {
            "allowed": allowed,
            "current": current_count,
            "max": max_requests,
            "remaining": max(0, max_requests - current_count),
            "reset_in": reset_in,
            "reason": limit_config["reason"],
            "risk_level": limit_config["risk_level"],
            "tool": limit_config.get("tool"),
            "pattern": limit_config.get("pattern")
        }


# Convenience function for imports
def check_tool_aware_rate_limit(ip: str, endpoint: str, user_agent: str, body: str, response_status: int = 200) -> Tuple[bool, Dict]:
    """
    Check rate limit with tool-aware detection
    """
    limiter = ToolAwareRateLimiter()
    return limiter.check_enhanced_rate_limit(ip, endpoint, user_agent, body, response_status)
