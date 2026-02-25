from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from rasp.feature_extractor import extract_features
from rasp.baseline_profiler import update_baseline
from rasp.drift_analyzer import detect_drift
from rasp.risk_engine import evaluate_risk
from rasp.mitigator import apply_mitigation, is_blocked
from monitoring.logger import log_event

class RASPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if "/health" in request.url.path or "/admin" in request.url.path:
            return await call_next(request)
        
        ip = request.client.host if request.client else "127.0.0.1"
        if is_blocked(ip):
            return Response(content="IP temporarily blocked", status_code=403)

        features = extract_features(request)
        update_baseline(features.endpoint, features)
        drift_result = detect_drift(features.endpoint, features)  # ← Returns DriftResult
        risk_level = evaluate_risk(drift_result.score, features.endpoint, ip)
        log_event(features, drift_result.score, risk_level, drift_result.attack_type)  # ← Pass attack_type

        if risk_level == "HIGH":
            apply_mitigation("block", ip)
            return Response(content="Request blocked: High-risk behavior detected", status_code=403)
        elif risk_level == "MEDIUM":
            apply_mitigation("rate_limit", ip)

        response = await call_next(request)
        return response
