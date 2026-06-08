"""
data_loader.py
───────────────
Loads pre-computed analytics results (JSON files) for the dashboard.
The dashboard reads from files — it does NOT re-run Spark each time.
"""

import os
import json
import pandas as pd

RESULTS_BASE   = os.path.join(os.path.dirname(__file__), "..", "..", "results")
ANALYTICS_DIR  = os.path.join(RESULTS_BASE, "analytics")
BENCHMARKS_DIR = os.path.join(RESULTS_BASE, "benchmarks")


def _load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def get_attack_distribution() -> dict:
    return _load_json(os.path.join(ANALYTICS_DIR, "attack_distribution.json"))


def get_suspicious_ips() -> dict:
    return _load_json(os.path.join(ANALYTICS_DIR, "suspicious_ips.json"))


def get_failed_logins() -> dict:
    return _load_json(os.path.join(ANALYTICS_DIR, "failed_logins.json"))


def get_traffic_analysis() -> dict:
    return _load_json(os.path.join(ANALYTICS_DIR, "traffic_analysis.json"))


def get_benchmark_summary() -> dict:
    return _load_json(os.path.join(BENCHMARKS_DIR, "comparison_summary.json"))


def get_job_timings() -> dict:
    return _load_json(os.path.join(ANALYTICS_DIR, "job_timings.json"))


def results_available() -> bool:
    """True if at least the attack distribution result exists."""
    return os.path.exists(
        os.path.join(ANALYTICS_DIR, "attack_distribution.json")
    )
