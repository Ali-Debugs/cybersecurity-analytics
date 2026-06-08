"""
traffic_analysis.py
────────────────────
Analyses network traffic patterns:
  • Protocol distribution (TCP/UDP/ICMP)
  • Most targeted destination ports
  • Traffic volume over time (daily/hourly)
  • Flow duration analysis (long vs short connections)
  • DoS / DDoS traffic spikes

PDC concepts:
  • Spark SQL window functions
  • Multi-column aggregations distributed across partitions
  • Lazy evaluation — transformations only execute when .collect() is called
"""

import os
import json
from pyspark.sql import functions as F
from pyspark.sql import Window
from analytics.spark_session import get_spark

HDFS_INPUT  = "hdfs://localhost:19000/cybersecurity/processed/combined.csv"
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "analytics")

PROTOCOL_MAP = {6: "TCP", 17: "UDP", 1: "ICMP", 0: "HOPOPT"}


def run(spark=None):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    if spark is None:
        spark = get_spark("TrafficAnalysis")

    print("\n── Network Traffic Analysis ──────────────────────────")

    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(HDFS_INPUT)
    )

    # ── 1. Protocol distribution ───────────────────────────────────
    proto_dist = (
        df.groupBy("Protocol")
        .count()
        .withColumnRenamed("count", "FlowCount")
        .orderBy(F.col("FlowCount").desc())
    )
    print("\n  Protocol distribution:")
    proto_dist.show()

    # ── 2. Top destination ports ───────────────────────────────────
    top_ports = (
        df.groupBy("Destination Port")
        .agg(
            F.count("*").alias("TotalFlows"),
            F.sum(F.when(F.col("Attack_Category") != "Benign", 1)
                  .otherwise(0)).alias("AttackFlows")
        )
        .withColumn(
            "Attack_Ratio",
            F.round(F.col("AttackFlows") / F.col("TotalFlows") * 100, 1)
        )
        .orderBy(F.col("TotalFlows").desc())
    )
    print("\n  Top 15 destination ports:")
    top_ports.show(15)

    # ── 3. Hourly traffic volume ───────────────────────────────────
    hourly_traffic = None
    if "Hour" in df.columns:
        hourly_traffic = (
            df.groupBy("Hour", "Attack_Category")
            .count()
            .withColumnRenamed("count", "Flows")
            .orderBy("Hour", "Attack_Category")
        )
        print("\n  Hourly traffic (sample):")
        hourly_traffic.show(10)

    # ── 4. DoS / DDoS flow detection ──────────────────────────────
    dos_df    = df.filter(F.col("Attack_Category") == "DoS")
    ddos_df   = df.filter(F.col("Attack_Category") == "DDoS")
    dos_count = dos_df.count()
    ddos_count = ddos_df.count()
    print(f"\n  DoS flows:  {dos_count:,}")
    print(f"  DDoS flows: {ddos_count:,}")

    # ── 5. Average flow bytes by attack type ──────────────────────
    flow_bytes = (
        df.groupBy("Attack_Category")
        .agg(
            F.round(F.avg("Flow Bytes/s"), 2).alias("Avg_Bytes_per_s"),
            F.round(F.avg("Flow Packets/s"), 2).alias("Avg_Packets_per_s"),
            F.round(F.avg("Flow Duration"), 2).alias("Avg_Duration_us"),
        )
        .orderBy(F.col("Avg_Bytes_per_s").desc())
    )
    print("\n  Traffic profile by attack category:")
    flow_bytes.show(truncate=False)

    # ── Save ──────────────────────────────────────────────────────
    result = {
        "protocol_distribution" : [r.asDict() for r in proto_dist.collect()],
        "top_ports"             : [r.asDict() for r in top_ports.limit(15).collect()],
        "dos_flows"             : dos_count,
        "ddos_flows"            : ddos_count,
        "flow_bytes_by_attack"  : [r.asDict() for r in flow_bytes.collect()],
        "hourly_traffic"        : (
            [r.asDict() for r in hourly_traffic.collect()]
            if hourly_traffic else []
        ),
    }

    out_path = os.path.join(RESULTS_DIR, "traffic_analysis.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n  Results saved → {out_path}")

    return result


if __name__ == "__main__":
    run()
