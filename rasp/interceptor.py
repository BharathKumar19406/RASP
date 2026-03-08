from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
import traceback
from .feature_extractor import extract_features
from .baseline_profiler import update_baseline
from .drift_analyzer import detect_drift
from .classifier import classify_attack
from .mitigator import is_blocked, apply_mitigation
from monitoring.logger import log_event

class RASPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if "/health" in request.url.path:
            return await call_next(request)

        ip = request.client.host if request.client else "127.0.0.1"
        if is_blocked(ip):
            return Response("IP temporarily blocked", status_code=403)

        try:
            body_bytes = await request.body()
            body_sample = body_bytes.decode("utf-8", errors="ignore")[:2000]
            features = extract_features(request, body_sample)
            
            # Dynamically use ANY path
            endpoint = request.url.path
            method = request.method
            
            update_baseline(endpoint, method, features)
            drift_score = detect_drift(endpoint, method, features.body_size)
            attack = classify_attack(
                endpoint=endpoint,
                method=method,
                body=body_sample,
                headers=dict(request.headers),
                features=features,
                drift_score=drift_score
            )
            risk_level = "HIGH" if drift_score >= 30 else "MEDIUM" if drift_score >= 15 else "LOW"
            
            log_event(features, drift_score, risk_level, attack)
            
            if risk_level == "HIGH":
                apply_mitigation("block", ip)
                return Response("Request blocked: High-risk behavior detected", status_code=403)

        except Exception as e:
            print(f"⚠️ RASP ERROR: {e}")
            traceback.print_exc()

        return await call_next(request)
