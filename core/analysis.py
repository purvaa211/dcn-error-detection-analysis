"""Analytical Processing & Performance Modeling for DCN Error Experiments.

Demonstrates:
- Data modeling using dataclasses.
- Encapsulated statistical evaluation and performance analysis.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import math


@dataclass
class ExperimentConfig:
    """Configuration parameters for Monte Carlo transmission trials."""
    data_sizes: List[int] = field(default_factory=lambda: [32, 64, 128, 256, 512])
    multi_error_amounts: List[int] = field(default_factory=lambda: [1, 2, 3, 4, 5, 8])
    burst_lengths: List[int] = field(default_factory=lambda: [2, 4, 8, 16])
    trials: int = 1000
    techniques: List[str] = field(default_factory=lambda: ["VRC / Parity", "LRC", "Checksum", "CRC"])


@dataclass
class ExperimentResult:
    """Data container for an individual transmission trial outcome."""
    technique: str
    error_type: str
    data_size: int
    error_amount: int
    trial: int
    errors_injected: int
    error_detected: bool
    is_valid: bool
    processing_time: float
    overhead_bits: int
    overhead_percentage: float


class ExperimentAnalyzer:
    """Analyzes empirical benchmark trials and produces statistical performance metrics."""

    def __init__(self, name: str = "DCN Performance Analyzer"):
        self.name = name

    @staticmethod
    def calculate_confidence_interval(
        successes: int,
        total: int,
        confidence: float = 0.95
    ) -> Dict[str, float]:
        """Compute Wilson score interval for empirical detection rate."""
        if total == 0:
            return {"center": 0.0, "lower": 0.0, "upper": 0.0}

        z = 1.95996  # 95% two-sided normal quantile
        p_hat = successes / total

        denominator = 1 + (z ** 2) / total
        center = (p_hat + (z ** 2) / (2 * total)) / denominator
        spread = (z / denominator) * math.sqrt(
            (p_hat * (1 - p_hat) / total) + ((z ** 2) / (4 * (total ** 2)))
        )

        lower = max(0.0, center - spread)
        upper = min(1.0, center + spread)

        return {
            "center": round(center * 100, 2),
            "lower": round(lower * 100, 2),
            "upper": round(upper * 100, 2)
        }

    @staticmethod
    def summarize_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate batch experimental records into summary performance indices."""
        if not records:
            return {
                "total_trials": 0,
                "detected_count": 0,
                "undetected_count": 0,
                "detection_rate": 0.0,
                "avg_latency_us": 0.0,
                "avg_overhead_pct": 0.0
            }

        total = len(records)
        detected = sum(1 for r in records if r.get("error_detected") is True)
        undetected = total - detected
        det_rate = (detected / total) * 100.0 if total > 0 else 0.0

        latencies = [r.get("processing_time", 0.0) * 1e6 for r in records]
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0

        overheads = [r.get("overhead_percentage", 0.0) for r in records]
        avg_ovh = sum(overheads) / len(overheads) if overheads else 0.0

        return {
            "total_trials": total,
            "detected_count": detected,
            "undetected_count": undetected,
            "detection_rate": round(det_rate, 2),
            "avg_latency_us": round(avg_lat, 2),
            "avg_overhead_pct": round(avg_ovh, 2)
        }
