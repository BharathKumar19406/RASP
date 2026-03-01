# rasp/interceptor.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import traceback
import sys
import os

class RASPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 🔥 CRITICAL: Log entry point
        print(f"[INTERCEPTOR] Starting for {request.method} {request.url.path}")

        try:
            # Step 1: Read body safely
            body_bytes = await request.body()
            body_sample = body_bytes.decode("utf-8", errors="ignore")[:1000]
            print(f"[INTERCEPTOR] Body sample len: {len(body_sample)}")

            # Step 2: Import inside try to catch missing modules
            try:
                from rasp.feature_extractor import extract_features
                features = extract_features(request, body_sample)
                print(f"[INTERCEPTOR] Features: IP={features.ip}, BodySize={features.body_size}")
            except Exception as e:
                print(f"❌ FEATURE EXTRACT ERROR: {e}")
                traceback.print_exc()
                raise

            # Step 3: Update baseline
            try:
                from rasp.baseline_profiler import update_baseline
                update_baseline(features.endpoint, features)
                print(f"[INTERCEPTOR] Baseline updated for {features.endpoint}")
            except Exception as e:
                print(f"❌ BASELINE ERROR: {e}")
                traceback.print_exc()
                raise

            # Step 4: Detect drift
            try:
                from rasp.drift_analyzer import detect_drift
                drift_score = detect_drift(features.endpoint, features)
                print(f"[INTERCEPTOR] Drift score: {drift_score:.1f}")
            except Exception as e:
                print(f"❌ DRIFT ERROR: {e}")
                traceback.print_exc()
                raise

            # Step 5: Classify attack
            try:
                from rasp.classifier import classify_attack
                classification = classify_attack(features.endpoint, features, drift_score, body_sample)
                print(f"[INTERCEPTOR] Attack: {classification['type']} (conf: {classification['confidence']:.2f})")
            except Exception as e:
                print(f"❌ CLASSIFY ERROR: {e}")
                traceback.print_exc()
                raise

            # Step 6: Log event
            try:
                from monitoring.logger import log_event
                risk_level = "HIGH" if drift_score >= 30 else "MEDIUM" if drift_score >= 15 else "LOW"
                log_event(features, drift_score, risk_level, classification)
                print(f"[INTERCEPTOR] Logged: Risk={risk_level}")
            except Exception as e:
                print(f"❌ LOG ERROR: {e}")
                traceback.print_exc()
                raise

            # Step 7: Mitigate
            if risk_level == "HIGH":
                try:
                    from rasp.mitigator import apply_mitigation, is_blocked
                    if not is_blocked(features.ip):
                        apply_mitigation("block", features.ip)
                    print(f"[INTERCEPTOR] BLOCKING IP: {features.ip}")
                    return Response(
                        content="Request blocked: High-risk behavior detected",
                        status_code=403
                    )
                except Exception as e:
                    print(f"❌ MITIGATE ERROR: {e}")
                    traceback.print_exc()

        except Exception as e:
            # 🚨 This will always print — no more silent failures
            print(f"🔥 FULL INTERCEPTOR FAILURE: {e}")
            traceback.print_exc(file=sys.stderr)

        # If we get here, no blocking → proceed
        return await call_next(request)
