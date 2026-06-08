"""
pandas_baseline.py
───────────────────
Reproduces the same analytics as Spark but using plain Pandas.
This gives us the "traditional" processing time for comparison.

PDC concept demonstrated:
  • Serial (single-core) vs parallel (multi-core Spark) processing
  • Shows WHY distributed computing is needed at scale
"""

import os
import time
import json
import pandas as pd
import numpy as np
from colorama import Fore, Style
import colorama

colorama.init(autoreset=True)

LOCAL_INPUT = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed", "combined.csv"
)
BENCH_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "benchmarks")


def run_pandas_benchmark():
    os.makedirs(BENCH_DIR, exist_ok=True)
    print(f"\n{Style.BRIGHT}Pandas Baseline Benchmark")
    print("=" * 50)

    timings = {}
    results = {}

    # ── Load ─────────────────────────────────────────────────────
    print(f"\n{Fore.CYAN}Loading dataset with Pandas...")
    t0 = time.time()
    df = pd.read_csv(LOCAL_INPUT, low_memory=False)
    timings["load"] = round(time.time() - t0, 3)
    print(f"  Loaded {len(df):,} rows in {timings['load']:.3f}s")

    # ── 1. Attack Distribution ────────────────────────────────────
    print(f"\n{Fore.CYAN}[1] Attack Distribution...")
    t0 = time.time()
    vc = df["Attack_Category"].value_counts().reset_index()
    vc.columns = ["Attack_Category", "Count"]
    attack_dist = vc.copy()
    attack_dist["Count"] = attack_dist["Count"].astype(int)
    attack_dist["Percentage"] = (attack_dist["Count"] / len(df) * 100).round(2)
    timings["attack_distribution"] = round(time.time() - t0, 3)
    results["attack_distribution"] = attack_dist.to_dict("records")
    print(f"  Done in {timings['attack_distribution']:.3f}s")

    # ── 2. Suspicious IPs ─────────────────────────────────────────
    print(f"\n{Fore.CYAN}[2] Suspicious IP Detection...")
    t0 = time.time()
    ip_total   = df.groupby("Source IP").size().reset_index(name="TotalFlows")
    ip_attacks = (
        df[df["Attack_Category"] != "Benign"]
        .groupby("Source IP")
        .size()
        .reset_index(name="AttackFlows")
    )
    ip_profile = ip_total.merge(ip_attacks, on="Source IP", how="left").fillna(0)
    ip_profile["Threat_Level"] = np.where(
        ip_profile["AttackFlows"] >= 10, "HIGH",
        np.where(ip_profile["AttackFlows"] > 0, "MEDIUM", "LOW")
    )
    timings["suspicious_ip"] = round(time.time() - t0, 3)
    results["suspicious_ip_count"] = {
        "HIGH"  : int((ip_profile["Threat_Level"] == "HIGH").sum()),
        "MEDIUM": int((ip_profile["Threat_Level"] == "MEDIUM").sum()),
        "LOW"   : int((ip_profile["Threat_Level"] == "LOW").sum()),
    }
    print(f"  Done in {timings['suspicious_ip']:.3f}s")

    # ── 3. Failed Logins / Brute Force ────────────────────────────
    print(f"\n{Fore.CYAN}[3] Failed Login Analysis...")
    t0 = time.time()
    brute_df    = df[df["Attack_Category"] == "Brute Force"]
    port_counts = brute_df["Destination Port"].value_counts().head(10)
    timings["failed_logins"] = round(time.time() - t0, 3)
    results["brute_force_count"]  = len(brute_df)
    results["top_brute_ports"]    = port_counts.to_dict()
    print(f"  Done in {timings['failed_logins']:.3f}s")

    # ── 4. Traffic Analysis ───────────────────────────────────────
    print(f"\n{Fore.CYAN}[4] Traffic Analysis...")
    t0 = time.time()
    proto_dist = df["Protocol"].value_counts()
    top_ports  = (
        df.groupby("Destination Port")
        .size()
        .sort_values(ascending=False)
        .head(15)
    )
    flow_bytes = df.groupby("Attack_Category")["Flow Bytes/s"].mean()
    timings["traffic_analysis"] = round(time.time() - t0, 3)
    results["protocol_distribution"] = proto_dist.to_dict()
    print(f"  Done in {timings['traffic_analysis']:.3f}s")

    # ── Summary ───────────────────────────────────────────────────
    total = sum(timings.values())
    print(f"\n{Style.BRIGHT}Pandas Benchmark Summary:")
    for task, t in timings.items():
        print(f"  {task:<30} {t:.3f}s")
    print(f"  {'TOTAL':<30} {total:.3f}s")

    out = {
        "framework": "pandas",
        "row_count": len(df),
        "timings_seconds": timings,
        "total_seconds": round(total, 3),
        "results": results,
    }

    out_path = os.path.join(BENCH_DIR, "pandas_benchmark.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n  Saved → {out_path}")

    return out


if __name__ == "__main__":
    run_pandas_benchmark()
