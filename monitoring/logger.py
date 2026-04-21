import uuid
import json
from datetime import datetime
from storage.db import SessionLocal
from storage.models import RuntimeEvent
from utils.crypto import hash_ip

def log_event(features, drift_score, risk_level, attack: dict, adaptation_info: dict = None, body_sample: str = ""):
    """Log security event with detailed information"""
    db = SessionLocal()
    try:
        adaptation_triggered = False
        baseline_before = None
        baseline_after = None
        
        if adaptation_info:
            baseline_before = adaptation_info.get("baseline_before")
            baseline_after = adaptation_info.get("baseline_after")
            adaptation_triggered = adaptation_info.get("adapted", False)
        
        # Use the highest risk between behavioral analysis and static pattern detection
        static_risk = attack.get("risk_level", "LOW")
        risk_priority = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
        
        # Determine highest risk
        current_risk_val = risk_priority.get(risk_level, 0)
        static_risk_val = risk_priority.get(static_risk, 0)
        
        final_risk = risk_level
        if static_risk_val > current_risk_val:
            final_risk = static_risk
            if final_risk == "CRITICAL": final_risk = "HIGH"
            
        event = RuntimeEvent(
            id=str(uuid.uuid4()),
            ip_hash=features.ip_hash,
            ip_addr=features.ip,
            endpoint=features.endpoint,
            method=features.method,
            param_count=features.param_count,
            body_size=features.body_size,
            drift_score=drift_score,
            risk_level=final_risk,
            attack_type=attack["type"],
            attack_category=attack.get("category", "UNKNOWN"),
            attack_confidence=attack["confidence"],
            attack_evidence=json.dumps(attack["evidence"]),
            attack_description=attack.get("description", ""),
            request_sample=body_sample[:500] if body_sample else "",
            baseline_before=baseline_before,
            baseline_after=baseline_after,
            adaptation_triggered=adaptation_triggered,
            user_role="user",
            user_agent=features.user_agent
        )
        db.add(event)
        db.commit()
    except Exception as e:
        print(f"⚠️ Logger error: {e}")
    finally:
        db.close()


def log_rate_limit_violation(ip: str, endpoint: str, rate_info: dict):
    """Log rate limit violations"""
    ip_hash = hash_ip(ip)
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║              🚨 RATE LIMIT VIOLATION DETECTED              ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  IP Hash:         {ip_hash}
║  Endpoint:        {endpoint}
║  Strategy:        {rate_info.get('strategy', 'unknown')}
║  Remaining:       {rate_info.get('remaining', 0)}
║  Reset In:        {rate_info.get('reset_in', 'N/A')} seconds
║  Timestamp:       {datetime.now().isoformat()}
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Log to file for audit trail
    try:
        with open("/workspaces/RASP/rate_limit_violations.log", "a") as f:
            f.write(f"""
[{datetime.now().isoformat()}] RATE_LIMIT_VIOLATION
  IP: {ip}
  IP_HASH: {ip_hash}
  Endpoint: {endpoint}
  Strategy: {rate_info.get('strategy', 'unknown')}
  Remaining: {rate_info.get('remaining', 0)}
  Reset_In: {rate_info.get('reset_in', 'N/A')}
  Anomaly_Level: {rate_info.get('anomaly_level', 0)}
---\n""")
    except Exception as e:
        print(f"⚠️ Error logging rate limit violation: {e}")
