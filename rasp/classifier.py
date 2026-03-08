# rasp/classifier.py
def classify_attack(endpoint: str, method: str, body: str, headers: dict, features, drift_score: float) -> dict:
    evidence = []

    # 1. SQL Injection (even in small bodies)
    if features.has_sql:
        evidence.append("sql_keywords")
        return {"type": "SQL Injection", "confidence": 0.95, "evidence": evidence}

    # 2. XSS (even in small bodies)
    if features.has_xss:
        evidence.append("script_tag")
        return {"type": "XSS Attempt", "confidence": 0.90, "evidence": evidence}

    # 3. Path Traversal
    if features.has_path_traversal:
        evidence.append("directory_traversal")
        return {"type": "Path Traversal", "confidence": 0.93, "evidence": evidence}

    # 4. SSRF
    if features.has_ssr:
        evidence.append("internal_ip")
        return {"type": "SSRF Attempt", "confidence": 0.88, "evidence": evidence}

    # 5. Command Injection
    if any(cmd in body for cmd in ["; cat ", "&& id", "$(whoami)", "| ls"]):
        evidence.append("shell_metachar")
        return {"type": "Command Injection", "confidence": 0.95, "evidence": evidence}

    # 6. XXE
    if "<!DOCTYPE" in body and ("<!ENTITY" in body or "SYSTEM" in body):
        evidence.append("xml_dtd")
        return {"type": "XXE Attempt", "confidence": 0.92, "evidence": evidence}

    # 7. Parameter Spam
    if features.param_count > 20:
        evidence.append("excessive_params")
        return {"type": "Parameter Spam", "confidence": 0.80, "evidence": evidence}

    # 8. Payload Flooding (behavioral fallback)
    if drift_score > 30 and features.body_size > 1000:
        evidence.append("large_body")
        return {"type": "Payload Flooding", "confidence": 0.90, "evidence": evidence}

    # Default: Log all requests for visibility
    return {"type": "Behavioral Anomaly", "confidence": 0.65, "evidence": ["deviation_from_baseline"]}
