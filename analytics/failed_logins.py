"""
failed_logins.py
─────────────────
Detects brute-force / failed-login patterns using Spark.

Approach:
  • Brute Force flows from CICIDS2017 use FTP-Patator and SSH-Patator labels
  • We look at high SYN flag counts (connection attempts)
  • We look at traffic on ports 21 (FTP) and 22 (SSH)

PDC concepts:
  • Distributed filtering using Spark SQL predicates
  • Time-series aggregation (flows per hour) across partitions
"""

import os
import json
from pyspark.sql import functions as F
from analytics.spark_session import get_spark

HDFS_INPUT  = "hdfs://localhost:19000/cybersecurity/processed/combined.csv"
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "analytics")

BRUTE_PORTS = [21, 22, 23, 3389]   # FTP, SSH, Telnet, RDP


def run(spark=None):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    if spark is None:
        spark = get_spark("FailedLogins")

    print("\n── Failed Login / Brute Force Analysis ───────────────")

    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(HDFS_INPUT)
    )

    # ── 1. Brute Force by label ────────────────────────────────────
    brute_df = df.filter(F.col("Attack_Category") == "Brute Force")
    total_brute = brute_df.count()
    print(f"\n  Total Brute Force flows: {total_brute:,}")

    # ── 2. Top targeted ports ──────────────────────────────────────
    port_counts = (
        brute_df.groupBy("Destination Port")
        .count()
        .withColumnRenamed("count", "BruteFlows")
        .orderBy(F.col("BruteFlows").desc())
    )
    print("\n  Top targeted ports (Brute Force):")
    port_counts.show(10)

    # ── 3. Top attacking IPs ───────────────────────────────────────
    src_counts = (
        brute_df.groupBy("Source IP")
        .count()
        .withColumnRenamed("count", "AttackFlows")
        .orderBy(F.col("AttackFlows").desc())
    )
    print("\n  Top attacking IPs:")
    src_counts.show(10)

    # ── 4. Hourly pattern ─────────────────────────────────────────
    hourly = None
    if "Hour" in df.columns:
        hourly = (
            brute_df.groupBy("Hour")
            .count()
            .withColumnRenamed("count", "BruteFlows")
            .orderBy("Hour")
        )
        print("\n  Brute Force flows by hour:")
        hourly.show(24)

    # ── 5. High-SYN flows (connection scan indicator) ─────────────
    if "SYN Flag Count" in df.columns:
        high_syn = df.filter(F.col("SYN Flag Count") > 5)
        high_syn_count = high_syn.count()
        print(f"\n  High SYN flag flows (>5 SYNs): {high_syn_count:,}")

    # ── Save results ──────────────────────────────────────────────
    result = {
        "total_brute_force_flows" : total_brute,
        "top_targeted_ports"      : [r.asDict() for r in port_counts.limit(10).collect()],
        "top_attacking_ips"       : [r.asDict() for r in src_counts.limit(10).collect()],
        "hourly_pattern"          : [r.asDict() for r in hourly.collect()] if hourly else [],
    }

    out_path = os.path.join(RESULTS_DIR, "failed_logins.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n  Results saved → {out_path}")

    return result


if __name__ == "__main__":
    run()
