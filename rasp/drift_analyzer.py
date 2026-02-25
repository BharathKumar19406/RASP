import statistics
from rasp.models import DriftResult
from rasp.baseline_profiler import get_baseline

def classify_attack(features, baseline) -> str:
    if not baseline:
        return "Unknown"
    if baseline["body_sizes"]:
        avg_body = statistics.mean(baseline["body_sizes"])
        if features.body_size > avg_body * 3:
            return "Payload Flooding"
    if baseline["param_counts"]:
        avg_params = statistics.mean(baseline["param_counts"])
        if features.param_count > avg_params * 2:
            return "Parameter Spam"
    return "Behavioral Anomaly"

def detect_drift(endpoint: str, features) -> 'DriftResult':
    baseline = get_baseline(endpoint)
    if not baseline or baseline["access_count"] < 3:  # ← Reduced from 5
        return DriftResult(score=0.0, attack_type="Baseline Learning")
    
    score = 0.0

    # Body size: more sensitive (3x normal = max score)
    if baseline["body_sizes"]:
        avg_size = statistics.mean(baseline["body_sizes"])
        if avg_size > 0:
            ratio = features.body_size / avg_size
            if ratio > 3:
                score += min((ratio - 3) * 20 + 40, 100)  # Start at 40, scale up

    # Parameter count: 2x = high score
    if baseline["param_counts"]:
        avg_params = statistics.mean(baseline["param_counts"])
        if avg_params > 0:
            ratio = features.param_count / avg_params
            if ratio > 2:
                score += min((ratio - 2) * 25 + 30, 60)  # Max 60 from params

    attack_type = classify_attack(features, baseline)
    return DriftResult(score=min(score, 100.0), attack_type=attack_type)
