from dataclasses import dataclass
from typing import Optional

@dataclass
class RequestFeatures:
    endpoint: str
    method: str
    ip: str
    param_count: int
    body_size: int
    timestamp: float

@dataclass
class DriftResult:
    score: float
    attack_type: str  
