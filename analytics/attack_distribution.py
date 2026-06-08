"""
attack_distribution.py
───────────────────────
Analyses the distribution of attack types in the dataset using Spark.

PDC concepts demonstrated:
  • Distributed aggregation (groupBy → count)
  • Parallel sorting across partitions
  • HDFS as the data source
"""

import os
import json
from pyspark.sql import functions as F
from analytics.spark_session import get_spark

HDFS_INPUT  = "hdfs://localhost:19000/cybersecurity/processed/combined.csv"
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "analytics")


def run(spark=None):
    """
    Returns a dict with attack distribution results and saves to JSON.
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)
    if spark is None:
        spark = get_spark("AttackDistribution")

    print("\n── Attack Distribution Analysis ──────────────────────")

    # ── Load from HDFS ─────────────────────────────────────────────
    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(HDFS_INPUT)
    )
    total_records = df.count()
    print(f"  Total records loaded: {total_records:,}")

    # ── Attack category counts ─────────────────────────────────────
    attack_dist = (
        df.groupBy("Attack_Category")
        .count()
        .withColumnRenamed("count", "Count")
        .withColumn("Percentage",
                    F.round(F.col("Count") / total_records * 100, 2))
        .orderBy(F.col("Count").desc())
    )

    attack_dist.show(20, truncate=False)

    # ── Label-level breakdown ──────────────────────────────────────
    label_dist = (
        df.groupBy("Label")
        .count()
        .withColumnRenamed("count", "Count")
        .orderBy(F.col("Count").desc())
    )

    label_dist.show(25, truncate=False)

    # ── Collect and save ───────────────────────────────────────────
    attack_rows = [row.asDict() for row in attack_dist.collect()]
    label_rows  = [row.asDict() for row in label_dist.collect()]

    result = {
        "total_records"      : total_records,
        "attack_categories"  : attack_rows,
        "label_distribution" : label_rows,
    }

    out_path = os.path.join(RESULTS_DIR, "attack_distribution.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n  Results saved → {out_path}")

    return result


if __name__ == "__main__":
    run()
