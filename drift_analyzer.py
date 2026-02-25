# rasp/drift_analyzer.py (UPDATED)

import statistics
from rasp.baseline_profiler import get_baseline

def detect_drift(endpoint: str, features) -> float:
    baseline = get_baseline(endpoint)
    if not baseline or baseline["access_count"] < 2:
        return 0.0

    score = 0.0

    # --- Param Count Drift ---
    if baseline["param_counts"]:
        avg_params = statistics.mean(baseline["param_counts"])
        current = features.param_count
        if current > avg_params * 3:  # 3x normal → high drift
            score += 50

    # --- Body Size Drift ---
    if baseline["body_sizes"]:
        avg_size = statistics.mean(baseline["body_sizes"])
        current = features.body_size
        if current > avg_size * 5:  # 5x normal → high drift
            score += 50

    return min(score, 100.0)
