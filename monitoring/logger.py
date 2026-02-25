from storage.repositories.event_repo import save_event

def log_event(features, drift_score, risk_level, attack_type="Unknown"):
    event_data = {
        "ip": features.ip,
        "endpoint": features.endpoint,
        "method": features.method,
        "param_count": features.param_count,
        "body_size": features.body_size,
        "drift_score": drift_score,
        "risk_level": risk_level,
        "attack_type": attack_type  # ← NEW
    }
    save_event(event_data)
