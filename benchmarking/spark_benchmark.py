"""
spark_benchmark.py
───────────────────
Runs the same tasks as pandas_baseline.py but using Spark.
Times are compared in compare_results.py.
"""

import os
import time
import json
from pyspark.sql import functions as F
from analytics.spark_session import get_spark
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

HDFS_INPUT = "hdfs://localhost:19000/cybersecurity/processed/combined.csv"
BENCH_DIR  = os.path.join(os.path.dirname(__file__), "..", "results", "benchmarks")


def run_spark_benchmark():
    os.makedirs(BENCH_DIR, exist_ok=True)
    print(f"\n{Style.BRIGHT}Spark Benchmark")
    print("=" * 50)

    spark   = get_spark("SparkBenchmark")
    timings = {}
    results = {}

    # ── Load ──────────────────────────────────────────────────────
    print(f"\n{Fore.CYAN}Loading dataset from HDFS...")
    t0 = time.time()
    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(HDFS_INPUT)
    )
    # Force load by counting
    row_count = df.count()
    timings["load"] = round(time.time() - t0, 3)
    print(f"  Loaded {row_count:,} rows in {timings['load']:.3f}s")

    # Cache for repeated queries
    df.cache()

    # ── 1. Attack Distribution ────────────────────────────────────
    print(f"\n{Fore.CYAN}[1] Attack Distribution...")
    t0 = time.time()
    attack_dist = (
        df.groupBy("Attack_Category")
        .count()
        .orderBy(F.col("count").desc())
        .collect()
    )
    timings["attack_distribution"] = round(time.time() - t0, 3)
    results["attack_distribution"] = [r.asDict() for r in attack_dist]
    print(f"  Done in {timings['attack_distribution']:.3f}s")

    # ── 2. Suspicious IPs ─────────────────────────────────────────
    print(f"\n{Fore.CYAN}[2] Suspicious IP Detection...")
    t0 = time.time()
    ip_attacks = (
        df.filter(F.col("Attack_Category") != "Benign")
        .groupBy("Source IP")
        .count()
        .filter(F.col("count") >= 10)
        .count()
    )
    timings["suspicious_ip"] = round(time.time() - t0, 3)
    results["high_threat_ips"] = ip_attacks
    print(f"  Done in {timings['suspicious_ip']:.3f}s")

    # ── 3. Failed Logins ──────────────────────────────────────────
    print(f"\n{Fore.CYAN}[3] Failed Login Analysis...")
    t0 = time.time()
    brute_count = df.filter(F.col("Attack_Category") == "Brute Force").count()
    timings["failed_logins"] = round(time.time() - t0, 3)
    results["brute_force_count"] = brute_count
    print(f"  Done in {timings['failed_logins']:.3f}s")

    # ── 4. Traffic Analysis ───────────────────────────────────────
    print(f"\n{Fore.CYAN}[4] Traffic Analysis...")
    t0 = time.time()
    _ = (
        df.groupBy("Protocol")
        .count()
        .collect()
    )
    _ = (
        df.groupBy("Destination Port")
        .agg(F.count("*").alias("flows"))
        .orderBy(F.col("flows").desc())
        .limit(15)
        .collect()
    )
    timings["traffic_analysis"] = round(time.time() - t0, 3)
    print(f"  Done in {timings['traffic_analysis']:.3f}s")

    # ── Summary ───────────────────────────────────────────────────
    total = sum(timings.values())
    print(f"\n{Style.BRIGHT}Spark Benchmark Summary:")
    for task, t in timings.items():
        print(f"  {task:<30} {t:.3f}s")
    print(f"  {'TOTAL':<30} {total:.3f}s")

    out = {
        "framework"       : "spark",
        "row_count"       : row_count,
        "timings_seconds" : timings,
        "total_seconds"   : round(total, 3),
        "results"         : results,
    }

    out_path = os.path.join(BENCH_DIR, "spark_benchmark.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n  Saved → {out_path}")

    spark.stop()
    return out


if __name__ == "__main__":
    run_spark_benchmark()
