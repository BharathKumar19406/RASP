from config.settings import sensitive_endpoints, thresholds

def evaluate_risk(drift_score: float, endpoint: str, ip: str) -> str:
    if drift_score >= thresholds["drift"]["high"]:
        risk = "HIGH"
    elif drift_score >= thresholds["drift"]["medium"]:
        risk = "MEDIUM"
    else:
        risk = "LOW"
    
    # Boost risk for sensitive endpoints
    if endpoint in sensitive_endpoints.get("high_risk", []):
        if risk == "MEDIUM":
            risk = "HIGH"
    
    return risk
