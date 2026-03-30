# rasp/classifier.py
from .behavioral_detector import classify_behavioral_attacks

def classify_attack(endpoint: str, method: str, body: str, headers: dict, features, drift_score: float, ip: str = "unknown", response_status: int = 200) -> dict:
    """
    Comprehensive attack classification combining:
    1. Pattern-based detection (static)
    2. Behavioral detection (dynamic, tool-aware)
    
    Returns attack classification with type, category, confidence, and evidence
    """
    
    # ==================== BEHAVIORAL ATTACKS (Priority 1) ====================
    # Check for sophisticated behavioral attacks first
    # These include: SQLMap, scanners, brute force, fuzzing, etc.
    behavioral_attack = classify_behavioral_attacks(
        ip=ip,
        endpoint=endpoint,
        method=method,
        body=body,
        headers=headers,
        features=features,
        response_status=response_status,
        drift_score=drift_score
    )
    
    if behavioral_attack:
        return behavioral_attack
    
    # ==================== PATTERN-BASED ATTACKS (Priority 2) ====================
    evidence = []

    # 1. SQL Injection (even in small bodies)
    if features.has_sql:
        evidence.append("sql_keywords")
        return {
            "type": "SQL Injection",
            "category": "SQL_INJECTION",
            "confidence": 0.95,
            "evidence": evidence,
            "description": f"SQL injection vectors detected in request body. Keywords like 'UNION SELECT' or 'OR 1=1' found. Endpoint: {endpoint}"
        }

    # 2. XSS (even in small bodies)
    if features.has_xss:
        evidence.append("script_tag")
        return {
            "type": "XSS Attempt",
            "category": "XSS",
            "confidence": 0.90,
            "evidence": evidence,
            "description": f"Cross-Site Scripting (XSS) payload detected. Script tags or JavaScript: protocol found in request. Endpoint: {endpoint}"
        }

    # 3. Path Traversal
    if features.has_path_traversal:
        evidence.append("directory_traversal")
        return {
            "type": "Path Traversal",
            "category": "PATH_TRAVERSAL",
            "confidence": 0.93,
            "evidence": evidence,
            "description": f"Path traversal sequence detected (../ or ..). Attempting to access files outside intended directory. Endpoint: {endpoint}"
        }

    # 4. SSRF
    if features.has_ssr:
        evidence.append("internal_ip")
        return {
            "type": "SSRF Attempt",
            "category": "SSRF",
            "confidence": 0.88,
            "evidence": evidence,
            "description": f"Server-Side Request Forgery (SSRF) detected. Internal IP addresses (127.0.0.1/localhost) referenced. Endpoint: {endpoint}"
        }

    # 5. Command Injection
    if any(cmd in body for cmd in ["; cat ", "&& id", "$(whoami)", "| ls"]):
        evidence.append("shell_metachar")
        return {
            "type": "Command Injection",
            "category": "COMMAND_INJECTION",
            "confidence": 0.95,
            "evidence": evidence,
            "description": f"Shell metacharacters and command injection patterns detected. Attempt to execute system commands: {'; cat' if '; cat ' in body else '&& id' if '&& id' in body else 'shell command'}. Endpoint: {endpoint}"
        }

    # 6. XXE
    if "<!DOCTYPE" in body and ("<!ENTITY" in body or "SYSTEM" in body):
        evidence.append("xml_dtd")
        return {
            "type": "XXE Attempt",
            "category": "XXE",
            "confidence": 0.92,
            "evidence": evidence,
            "description": f"XML External Entity (XXE) injection detected. XML DTD and ENTITY/SYSTEM declarations found. Endpoint: {endpoint}"
        }

    # 7. Parameter Spam
    if features.param_count > 20:
        evidence.append("excessive_params")
        return {
            "type": "Parameter Spam",
            "category": "PARAMETER_SPAM",
            "confidence": 0.80,
            "evidence": evidence,
            "description": f"Excessive query parameters detected ({features.param_count} params). Possible parameter pollution or fuzzing attack. Endpoint: {endpoint}"
        }

    # 8. Payload Flooding (behavioral fallback)
    if drift_score > 30 and features.body_size > 1000:
        evidence.append("large_body")
        return {
            "type": "Payload Flooding",
            "category": "PAYLOAD_FLOODING",
            "confidence": 0.90,
            "evidence": evidence,
            "description": f"Payload flooding detected. Large body size ({features.body_size} bytes) with high drift score ({drift_score:.1f}). Endpoint: {endpoint}"
        }

    # Default: Log all requests for visibility
    return {
        "type": "Behavioral Anomaly",
        "category": "BEHAVIORAL_ANOMALY",
        "confidence": 0.65,
        "evidence": ["deviation_from_baseline"],
        "description": f"Request behavior deviates from baseline profile. Drift score: {drift_score:.1f}. Method: {method}, Params: {features.param_count}, Body size: {features.body_size} bytes. Endpoint: {endpoint}"
    }
