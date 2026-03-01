# rasp/classifier.py
import re

SQL_PATTERNS = [
    r"(?i)(union\s+select|select\s+\*\s+from|insert\s+into|drop\s+table|delete\s+from)",
]

def detect_sql_indicators(body: str) -> bool:
    if len(body) < 50:
        return False
    return any(re.search(p, body) for p in SQL_PATTERNS)

def classify_attack(endpoint: str, features, drift_score: float, body_sample: str = "") -> dict:
    evidence = []

    # 1. Payload Flooding: Large body + high drift
    if drift_score > 30 and features.body_size > 1000:
        evidence.append("large_body")
        return {
            "type": "Payload Flooding",
            "confidence": 0.90,
            "evidence": evidence
        }

    # 2. Script Flooding: Repeated hash (requires body_hash)
    if (drift_score > 30 and features.body_hash and 
        hasattr(features, 'recent_hashes') and 
        features.recent_hashes and 
        features.body_hash in features.recent_hashes[-3:]):
        evidence.append("repeated_hash")
        return {
            "type": "Script Flooding",
            "confidence": 0.92,
            "evidence": evidence
        }

    # 3. SQL Injection Flooding: SQL keywords + large body
    if drift_score > 25 and features.body_size > 500 and detect_sql_indicators(body_sample):
        evidence.append("sql_keywords")
        return {
            "type": "SQL Injection Flooding",
            "confidence": 0.95,
            "evidence": evidence
        }

    # 4. Parameter Spam
    if features.param_count > 15:
        return {
            "type": "Parameter Spam",
            "confidence": 0.80,
            "evidence": ["excessive_params"]
        }

    # Default
    return {
        "type": "Behavioral Anomaly",
        "confidence": 0.65,
        "evidence": ["deviation_from_baseline"]
    }
