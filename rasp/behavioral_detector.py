"""
Behavioral Attack Detection Module
Detects attacks based on request patterns, sequences, and tool signatures
Complements static pattern detection with dynamic behavioral analysis
"""

import time
from typing import Dict, Tuple, List
from storage.redis_client import get_redis
from storage.redis_cache import get_json, set_json, update_json
import json
import re

class BehavioralAttackDetector:
    """
    Detects attacks based on behavioral patterns rather than just content
    Tracks: tool signatures, attack sequences, timing, error rates, etc.
    """
    
    # Known attack tool signatures
    TOOL_SIGNATURES = {
        "sqlmap": {
            "user_agent": r"(?i)(^sqlmap|sqlmap[/\s])",
            "patterns": ["--batch", "union", "sleep(", "benchmark(", "waitfor"],
            "risk_level": "CRITICAL",
        },
        "acunetix": {
            "user_agent": r"(?i)acunetix",
            "patterns": [],
            "risk_level": "CRITICAL",
        },
        "metasploit": {
            "user_agent": r"(?i)(metasploit|msfconsole)",
            "patterns": [],
            "risk_level": "CRITICAL",
        },
        "nikto": {
            "user_agent": r"(?i)nikto",
            "patterns": [],
            "risk_level": "HIGH",
        },
        "nmap": {
            "user_agent": r"(?i)nmap",
            "patterns": [],
            "risk_level": "HIGH",
        },
        "burp": {
            "user_agent": r"(?i)(burp|intruder)",
            "patterns": [],
            "risk_level": "HIGH",
        },
        "zaproxy": {
            "user_agent": r"(?i)(zaproxy|owasp)",
            "patterns": [],
            "risk_level": "HIGH",
        },
    }
    
    # SQLMap specific detection (sophisticated, high-impact)
    SQLMAP_PATTERNS = [
        r"(?i)(union.*select|select.*from.*where)",  # Union-based
        r"(?i)(sleep\(|benchmark\()",                # Time-based
        r"(?i)(or\s+1\s*=\s*1|or\s+true)",           # Boolean-based
        r"(?i)(extractvalue|updatexml)",              # XML functions
        r"(?i)(load_file|into.*outfile)",             # File operations
        r"(?i)(\*/\*.*\*/|#|--|;)",                   # Comment injection
        r"(?i)(cast\(|convert\()",                    # Type casting
        r"(?i)(\*\*|^)",                              # Power operators
    ]
    
    # Brute force detection patterns
    BRUTE_FORCE_PATTERNS = {
        "login": {
            "endpoint": r"(?i)(login|auth|signin)",
            "max_attempts_per_min": 5,
            "error_threshold": 0.5,  # 50% errors = suspicious
        },
        "api_key": {
            "endpoint": r"(?i)(api|token|key)",
            "max_attempts_per_min": 20,
            "error_threshold": 0.7,  # 70% errors = suspicious
        },
        "password_reset": {
            "endpoint": r"(?i)(password|reset|forgot)",
            "max_attempts_per_min": 3,
            "error_threshold": 0.4,
        },
    }
    
    @staticmethod
    def detect_tool_signature(user_agent: str, body: str) -> Dict:
        """
        Detect if request matches known attack tool signatures
        Returns: {"detected": bool, "tool": str, "risk": str}
        """
        user_agent_lower = (user_agent or "").lower()
        
        for tool, config in BehavioralAttackDetector.TOOL_SIGNATURES.items():
            # Check user agent
            if re.search(config["user_agent"], user_agent_lower):
                return {
                    "detected": True,
                    "type": f"{tool.upper()} Detection",
                    "tool": tool,
                    "confidence": 0.95,
                    "risk_level": config["risk_level"],
                    "evidence": [f"{tool}_user_agent"],
                    "description": f"Attack tool detected: {tool.upper()} identified from User-Agent header"
                }
            
            # Check body patterns if defined
            if config["patterns"]:
                for pattern in config["patterns"]:
                    if pattern in body:
                        return {
                            "detected": True,
                            "type": f"{tool.upper()} Detection",
                            "tool": tool,
                            "confidence": 0.90,
                            "risk_level": config["risk_level"],
                            "evidence": [f"{tool}_pattern"],
                            "description": f"Attack tool detected: {tool.upper()} behavior pattern identified"
                        }
        
        return {"detected": False}
    
    @staticmethod
    def detect_sqlmap_behavior(ip: str, endpoint: str, body: str, headers: dict) -> Dict:
        """
        Detect SQLMap-specific behavior patterns
        SQLMap is high-impact and sophisticated - needs careful detection
        """
        # Count SQLMap pattern matches
        pattern_matches = 0
        for pattern in BehavioralAttackDetector.SQLMAP_PATTERNS:
            if re.search(pattern, body):
                pattern_matches += 1
        
        # Multiple pattern matches = SQLMap-like behavior
        if pattern_matches >= 2:
            return {
                "detected": True,
                "type": "SQLMap-like Behavior",
                "category": "SQLMAP_ATTACK",
                "confidence": 0.85,
                "risk_level": "CRITICAL",
                "evidence": ["multiple_sql_patterns"],
                "pattern_count": pattern_matches,
                "description": f"SQLMap-like attack detected: {pattern_matches} SQL injection patterns found (sophisticated multi-vector attack)"
            }
        
        # Check for SQLMap in request history for same IP
        r = get_redis()
        ip_history_key = f"attack_history:{ip}"
        history = get_json(ip_history_key, {})
        
        # If same IP has recent SQLMap detection, increase confidence
        if history.get("last_sqlmap_time"):
            time_diff = time.time() - history["last_sqlmap_time"]
            if time_diff < 60:  # Within last minute
                return {
                    "detected": True,
                    "type": "SQLMap Attack Sequence",
                    "category": "SQLMAP_ATTACK",
                    "confidence": 0.92,
                    "risk_level": "CRITICAL",
                    "evidence": ["repeated_sqlmap_behavior"],
                    "description": f"SQLMap attack sequence: Repeated attack from same source within {int(time_diff)} seconds"
                }
        
        return {"detected": False}
    
    @staticmethod
    def detect_brute_force(ip: str, endpoint: str, response_status: int = 401) -> Dict:
        """
        Detect brute force attacks based on request frequency and error rates
        """
        r = get_redis()
        
        # Determine category
        category = None
        max_attempts = 5
        
        for category_name, rules in BehavioralAttackDetector.BRUTE_FORCE_PATTERNS.items():
            if re.search(rules["endpoint"], endpoint):
                category = category_name
                max_attempts = rules["max_attempts_per_min"]
                break
        
        if not category:
            return {"detected": False}
        
        # Track request count and errors for this IP+endpoint
        tracking_key = f"brute_force:{ip}:{endpoint}"
        stats = get_json(tracking_key, {"count": 0, "errors": 0, "start_time": time.time()})
        
        # Reset if window expired
        if time.time() - stats["start_time"] > 60:
            stats = {"count": 0, "errors": 0, "start_time": time.time()}
        
        # Increment counters
        stats["count"] += 1
        if response_status >= 400:
            stats["errors"] += 1
        
        set_json(tracking_key, stats, expire=61)
        
        # Check for brute force
        error_rate = stats["errors"] / stats["count"] if stats["count"] > 0 else 0
        
        is_brute_force = (
            stats["count"] > max_attempts or
            error_rate > BehavioralAttackDetector.BRUTE_FORCE_PATTERNS[category].get("error_threshold", 0.5)
        )
        
        if is_brute_force:
            return {
                "detected": True,
                "type": f"Brute Force - {category.upper()}",
                "category": "BRUTE_FORCE",
                "confidence": 0.90,
                "risk_level": "HIGH",
                "evidence": ["rapid_attempts", "high_error_rate"],
                "attempt_count": stats["count"],
                "error_rate": f"{error_rate*100:.1f}%",
                "description": f"Brute force attack detected on {category}: {stats['count']} attempts with {error_rate*100:.1f}% error rate in 1 minute"
            }
        
        return {"detected": False}
    
    @staticmethod
    def detect_fuzzing_attack(ip: str, endpoint: str, features) -> Dict:
        """
        Detect fuzzing/parameter pollution attacks
        Characteristics: Malformed requests, invalid parameters, chaos patterns
        """
        r = get_redis()
        
        # Track fuzz attempts
        fuzz_key = f"fuzz_attempts:{ip}:{endpoint}"
        fuzz_stats = get_json(fuzz_key, {"count": 0, "malformed": 0, "start_time": time.time()})
        
        # Reset if window expired
        if time.time() - fuzz_stats["start_time"] > 60:
            fuzz_stats = {"count": 0, "malformed": 0, "start_time": time.time()}
        
        fuzz_stats["count"] += 1
        
        # Check for malformed request indicators
        is_malformed = (
            hasattr(features, 'param_count') and features.param_count > 30 or
            hasattr(features, 'body_size') and features.body_size > 0 and features.body_size < 10
        )
        
        if is_malformed:
            fuzz_stats["malformed"] += 1
        
        set_json(fuzz_key, fuzz_stats, expire=61)
        
        malformed_rate = fuzz_stats["malformed"] / fuzz_stats["count"] if fuzz_stats["count"] > 0 else 0
        
        # Fuzzing detected if >40% malformed in short period
        if fuzz_stats["count"] > 5 and malformed_rate > 0.4:
            return {
                "detected": True,
                "type": "Fuzzing/Parameter Pollution",
                "category": "FUZZING",
                "confidence": 0.85,
                "risk_level": "MEDIUM",
                "evidence": ["malformed_requests", "parameter_pollution"],
                "malformed_ratio": f"{malformed_rate*100:.1f}%",
                "attempt_count": fuzz_stats["count"],
                "description": f"Fuzzing attack detected: {malformed_rate*100:.1f}% malformed requests ({fuzz_stats['malformed']}/{fuzz_stats['count']}) in 1 minute"
            }
        
        return {"detected": False}
    
    @staticmethod
    def detect_scanner_behavior(ip: str, endpoint: str, user_agent: str) -> Dict:
        """
        Detect vulnerability scanner behavior
        Scanners probe multiple endpoints in rapid succession
        """
        r = get_redis()
        
        # Track endpoints accessed by this IP
        scanner_key = f"scanner_probes:{ip}"
        probes = get_json(scanner_key, {"endpoints": {}, "start_time": time.time()})
        
        # Reset if window expired
        if time.time() - probes["start_time"] > 60:
            probes = {"endpoints": {}, "start_time": time.time()}
        
        # Record this endpoint
        if endpoint not in probes["endpoints"]:
            probes["endpoints"][endpoint] = 0
        probes["endpoints"][endpoint] += 1
        
        set_json(scanner_key, probes, expire=61)
        
        # Scanner behavior: >10 different endpoints in 60 seconds
        unique_endpoints = len(probes["endpoints"])
        
        if unique_endpoints > 10:
            return {
                "detected": True,
                "type": "Vulnerability Scanner",
                "category": "SCANNER",
                "confidence": 0.88,
                "risk_level": "MEDIUM",
                "evidence": ["rapid_endpoint_enumeration"],
                "unique_endpoints": unique_endpoints,
                "description": f"Vulnerability scanner detected: {unique_endpoints} different endpoints probed in 60 seconds from single IP"
            }
        
        return {"detected": False}
    
    @staticmethod
    def detect_credential_stuffing(ip: str, username_param: str, response_status: int) -> Dict:
        """
        Detect credential stuffing attacks
        Characteristics: Multiple login attempts with different usernames/passwords
        """
        r = get_redis()
        
        # Track unique usernames from this IP
        cred_key = f"cred_stuffing:{ip}"
        attempts = get_json(cred_key, {"usernames": {}, "start_time": time.time()})
        
        # Reset if window expired
        if time.time() - attempts["start_time"] > 300:  # 5 min window
            attempts = {"usernames": {}, "start_time": time.time()}
        
        # Record username attempt
        if username_param not in attempts["usernames"]:
            attempts["usernames"][username_param] = 0
        attempts["usernames"][username_param] += 1
        
        set_json(cred_key, attempts, expire=301)
        
        unique_users = len(attempts["usernames"])
        
        # Credential stuffing: >15 unique usernames in 5 minutes
        if unique_users > 15:
            success_ratio = sum(1 for v in attempts["usernames"].values() if v == 1) / unique_users
            
            return {
                "detected": True,
                "type": "Credential Stuffing",
                "category": "CREDENTIAL_STUFFING",
                "confidence": 0.92,
                "risk_level": "CRITICAL",
                "evidence": ["multiple_username_attempts"],
                "unique_users": unique_users,
                "description": f"Credential stuffing attack detected: {unique_users} unique usernames attempted in 5 minutes"
            }
        
        return {"detected": False}
    
    @staticmethod
    def detect_rate_anomaly(ip: str, endpoint: str, current_rate: float, baseline_rate: float) -> Dict:
        """
        Detect abnormal request rates (slow DDoS, slowloris, etc)
        """
        if baseline_rate == 0:
            return {"detected": False}
        
        rate_multiplier = current_rate / baseline_rate if baseline_rate > 0 else 0
        
        # 10x increase = anomaly
        if rate_multiplier > 10:
            return {
                "detected": True,
                "type": "Rate Anomaly (Possible DDoS)",
                "category": "RATE_ANOMALY",
                "confidence": 0.85,
                "risk_level": "HIGH",
                "evidence": ["abnormal_request_rate"],
                "rate_multiplier": f"{rate_multiplier:.1f}x",
                "current_rate": f"{current_rate:.2f} req/sec",
                "baseline": f"{baseline_rate:.2f} req/sec",
                "description": f"Rate anomaly detected: {rate_multiplier:.1f}x increase from baseline ({baseline_rate:.2f} → {current_rate:.2f} req/sec)"
            }
        
        return {"detected": False}


def classify_behavioral_attacks(
    ip: str,
    endpoint: str,
    method: str,
    body: str,
    headers: dict,
    features,
    response_status: int = 200,
    drift_score: float = 0.0
) -> Dict:
    """
    Comprehensive behavioral attack detection
    Complements static pattern detection with dynamic analysis
    
    Returns attack info if detected, None otherwise
    """
    
    detector = BehavioralAttackDetector()
    user_agent = headers.get("user-agent", "")
    
    # 1. Check for tool signatures (SQLMap, Nikto, etc)
    tool_detection = detector.detect_tool_signature(user_agent, body)
    if tool_detection.get("detected"):
        return tool_detection
    
    # 2. SQLMap-specific sophisticated detection
    sqlmap_detection = detector.detect_sqlmap_behavior(ip, endpoint, body, headers)
    if sqlmap_detection.get("detected"):
        return sqlmap_detection
    
    # 3. Brute force detection (login attempts, API key guessing)
    brute_force = detector.detect_brute_force(ip, endpoint, response_status)
    if brute_force.get("detected"):
        return brute_force
    
    # 4. Fuzzing/Parameter pollution
    fuzzing = detector.detect_fuzzing_attack(ip, endpoint, features)
    if fuzzing.get("detected"):
        return fuzzing
    
    # 5. Vulnerability scanner probing
    scanner = detector.detect_scanner_behavior(ip, endpoint, user_agent)
    if scanner.get("detected"):
        return scanner
    
    # 6. Credential stuffing (if login endpoint)
    if "login" in endpoint.lower() or "auth" in endpoint.lower():
        cred_stuff = detector.detect_credential_stuffing(ip, "", response_status)
        if cred_stuff.get("detected"):
            return cred_stuff
    
    return None
