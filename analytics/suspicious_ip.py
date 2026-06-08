"""
suspicious_ip.py
─────────────────
Identifies suspicious / malicious source IPs using Spark.

Logic:
  • IPs appearing in ≥ N attack flows are flagged as "malicious"
  • IPs appearing only in benign flows are marked "clean"
  • IPs in both categories are marked "mixed"

PDC concepts:
  • Multi-key groupBy across distributed partitions
  • Window functions over distributed data
  • Efficient filter pushdown on HDFS files
"""

import os
import json
from pyspark.sql import functions as F
from pyspark.sql import Window
from analytics.spark_session import get_spark

HDFS_INPUT      = "hdfs://localhost:19000/cybersecurity/processed/combined.csv"
RESULTS_DIR     = os.path.join(os.path.dirname(__file__), "..", "results", "analytics")
ATTACK_THRESHOLD = 10   # flag an IP if it appears in ≥ 10 attack flows


def run(spark=None):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    if spark is None:
        spark = get_spark("SuspiciousIP")

    print("\n── Suspicious IP Detection ───────────────────────────")

    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(HDFS_INPUT)
    )

    # ── Flows per source IP × attack category ─────────────────────
    ip_stats = (
        df.groupBy("Source IP", "Attack_Category")
        .agg(
            F.count("*").alias("FlowCount"),
            F.countDistinct("Destination IP").alias("UniqueTargets"),
            F.countDistinct("Destination Port").alias("UniquePorts"),
        )
    )

    # ── Total flows per source IP ──────────────────────────────────
    ip_total = (
        df.groupBy("Source IP")
        .agg(F.count("*").alias("TotalFlows"))
    )

    # ── Attack-only flows per IP ───────────────────────────────────
    ip_attacks = (
        df.filter(F.col("Attack_Category") != "Benign")
        .groupBy("Source IP")
        .agg(
            F.count("*").alias("AttackFlows"),
            F.collect_set("Attack_Category").alias("AttackTypes"),
        )
    )

    # ── Join and classify ──────────────────────────────────────────
    ip_profile = (
        ip_total
        .join(ip_attacks, on="Source IP", how="left")
        .fillna({"AttackFlows": 0})
        .withColumn(
            "Threat_Level",
            F.when(F.col("AttackFlows") >= ATTACK_THRESHOLD, "HIGH")
             .when(F.col("AttackFlows") > 0,                  "MEDIUM")
             .otherwise("LOW")
        )
        .withColumn(
            "Attack_Rate_Pct",
            F.round(F.col("AttackFlows") / F.col("TotalFlows") * 100, 2)
        )
        .orderBy(F.col("AttackFlows").desc())
    )

    # ── Top 20 most suspicious IPs ────────────────────────────────
    print("\n  Top 20 Suspicious Source IPs:")
    ip_profile.filter(F.col("Threat_Level") == "HIGH").show(20, truncate=False)

    # ── Summary stats ─────────────────────────────────────────────
    summary = ip_profile.groupBy("Threat_Level").count()
    print("\n  Threat level summary:")
    summary.show()

    # ── Save ──────────────────────────────────────────────────────
    top_suspicious = [
        row.asDict()
        for row in ip_profile.filter(F.col("Threat_Level") == "HIGH")
        .limit(50)
        .collect()
    ]
    summary_rows = [row.asDict() for row in summary.collect()]

    result = {
        "attack_threshold"  : ATTACK_THRESHOLD,
        "threat_summary"    : summary_rows,
        "top_suspicious_ips": top_suspicious,
    }

    out_path = os.path.join(RESULTS_DIR, "suspicious_ips.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n  Results saved → {out_path}")

    return result


if __name__ == "__main__":
    run()
