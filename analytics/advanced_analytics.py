"""
advanced_analytics.py
──────────────────────
Advanced Spark analytics demonstrating real distributed processing:

  1. Spark SQL temp views      — query HDFS data with SQL syntax
  2. Window functions          — RANK, DENSE_RANK, LAG, running totals
  3. Multi-dataset join        — IP profile × port profile correlation
  4. Attack timeline pivot     — hourly attack matrix (attack type × hour)
  5. Severity scoring UDF      — custom Python function run across partitions
  6. Percentile / approx stats — PERCENTILE_APPROX on 2M rows

All of this runs on the 296 MB file stored in HDFS.
Pandas cannot hold this in memory comfortably and cannot use window
functions without extra libraries. Spark handles it natively.
"""

import os, json, time
from pyspark.sql import functions as F
from pyspark.sql import Window
from pyspark.sql.types import StringType
from analytics.spark_session import get_spark

HDFS_INPUT  = "hdfs://localhost:19000/cybersecurity/processed/combined.csv"
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "analytics")


# ── Severity UDF ───────────────────────────────────────────────────
# A user-defined function applied row-by-row across all partitions.
# This is pure Python running inside Spark workers — distributed.
def _severity_label(attack_cat, flow_bytes, syn_flags):
    if attack_cat in ("DDoS", "DoS"):
        return "Critical" if flow_bytes and flow_bytes > 20000 else "High"
    if attack_cat == "Brute Force":
        return "High" if syn_flags and syn_flags > 1 else "Medium"
    if attack_cat == "Port Scan":
        return "Medium"
    if attack_cat == "Bot":
        return "Medium"
    return "Low"

severity_udf = F.udf(_severity_label, StringType())


def run(spark=None):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    if spark is None:
        spark = get_spark("AdvancedAnalytics")

    print("\n── Advanced Spark Analytics ──────────────────────────")

    # ── Load from HDFS ─────────────────────────────────────────────
    t0 = time.time()
    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(HDFS_INPUT)
        .cache()                      # cache for repeated queries
    )
    total = df.count()
    print(f"  Loaded {total:,} rows from HDFS in {time.time()-t0:.2f}s")

    # Register as Spark SQL temp view — now queryable with spark.sql()
    df.createOrReplaceTempView("network_flows")
    print("  Temp view 'network_flows' registered")

    results = {}

    # ══════════════════════════════════════════════════════════════
    # 1. SPARK SQL — plain SQL on top of HDFS data
    # ══════════════════════════════════════════════════════════════
    print("\n  [1] Spark SQL query...")
    t0 = time.time()

    sql_result = spark.sql("""
        SELECT
            Attack_Category,
            COUNT(*)                                  AS total_flows,
            COUNT(DISTINCT `Source IP`)               AS unique_src_ips,
            COUNT(DISTINCT `Destination Port`)        AS unique_dst_ports,
            ROUND(AVG(`Flow Bytes/s`), 2)             AS avg_bytes_per_sec,
            ROUND(AVG(`Flow Duration`), 2)            AS avg_duration_us,
            ROUND(AVG(`SYN Flag Count`), 3)           AS avg_syn_flags,
            ROUND(MAX(`Flow Bytes/s`), 2)             AS max_bytes_per_sec
        FROM network_flows
        GROUP BY Attack_Category
        ORDER BY total_flows DESC
    """)

    sql_rows = [r.asDict() for r in sql_result.collect()]
    results["sql_attack_profile"] = sql_rows
    print(f"  Done in {time.time()-t0:.2f}s")
    sql_result.show(truncate=False)

    # ══════════════════════════════════════════════════════════════
    # 2. WINDOW FUNCTIONS — rank IPs within each attack category
    # ══════════════════════════════════════════════════════════════
    print("\n  [2] Window functions — ranking IPs per attack type...")
    t0 = time.time()

    # Step 1: count flows per (source IP, attack category)
    ip_attack_counts = (
        df.filter(F.col("Attack_Category") != "Benign")
        .groupBy("Source IP", "Attack_Category")
        .agg(F.count("*").alias("flow_count"))
    )

    # Step 2: RANK() inside each attack category partition
    window_spec = Window.partitionBy("Attack_Category").orderBy(F.col("flow_count").desc())

    ranked = (
        ip_attack_counts
        .withColumn("rank",       F.rank().over(window_spec))
        .withColumn("dense_rank", F.dense_rank().over(window_spec))
        .withColumn("pct_of_category",
                    F.round(
                        F.col("flow_count") /
                        F.sum("flow_count").over(Window.partitionBy("Attack_Category")) * 100,
                        2
                    ))
        .filter(F.col("rank") <= 5)   # top 5 per category
        .orderBy("Attack_Category", "rank")
    )

    ranked_rows = [r.asDict() for r in ranked.collect()]
    results["top_ips_per_attack_windowed"] = ranked_rows
    print(f"  Done in {time.time()-t0:.2f}s")
    ranked.show(20, truncate=False)

    # ══════════════════════════════════════════════════════════════
    # 3. LAG FUNCTION — detect hourly attack escalation
    # ══════════════════════════════════════════════════════════════
    print("\n  [3] LAG window — hourly attack escalation...")
    t0 = time.time()

    hourly_attacks = (
        df.filter(F.col("Attack_Category") != "Benign")
        .groupBy("Hour", "Attack_Category")
        .agg(F.count("*").alias("flows"))
        .orderBy("Attack_Category", "Hour")
    )

    lag_window = Window.partitionBy("Attack_Category").orderBy("Hour")

    hourly_delta = (
        hourly_attacks
        .withColumn("prev_hour_flows", F.lag("flows", 1).over(lag_window))
        .withColumn("delta",
                    F.col("flows") - F.coalesce(F.col("prev_hour_flows"), F.col("flows")))
        .withColumn("pct_change",
                    F.round(
                        F.when(F.col("prev_hour_flows") > 0,
                               (F.col("flows") - F.col("prev_hour_flows"))
                               / F.col("prev_hour_flows") * 100
                        ).otherwise(0),
                        1
                    ))
    )

    hourly_rows = [r.asDict() for r in hourly_delta.collect()]
    results["hourly_attack_delta"] = hourly_rows
    print(f"  Done in {time.time()-t0:.2f}s")
    hourly_delta.filter(F.col("Attack_Category") == "DDoS").show()

    # ══════════════════════════════════════════════════════════════
    # 4. JOIN — correlate IP threat profile with port behaviour
    # ══════════════════════════════════════════════════════════════
    print("\n  [4] Join — IP threat profile x port profile...")
    t0 = time.time()

    # Left table: IP attack summary
    ip_profile = (
        df.groupBy("Source IP")
        .agg(
            F.count("*").alias("total_flows"),
            F.sum(F.when(F.col("Attack_Category") != "Benign", 1).otherwise(0)).alias("attack_flows"),
            F.countDistinct("Destination Port").alias("unique_ports_targeted"),
        )
        .withColumn("attack_ratio",
                    F.round(F.col("attack_flows") / F.col("total_flows") * 100, 1))
    )

    # Right table: most-used port per IP
    port_window = Window.partitionBy("Source IP").orderBy(F.col("port_count").desc())
    top_port_per_ip = (
        df.groupBy("Source IP", "Destination Port")
        .agg(F.count("*").alias("port_count"))
        .withColumn("port_rank", F.rank().over(port_window))
        .filter(F.col("port_rank") == 1)
        .select("Source IP",
                F.col("Destination Port").alias("primary_target_port"),
                "port_count")
    )

    # Join
    joined = (
        ip_profile
        .join(top_port_per_ip, on="Source IP", how="left")
        .filter(F.col("attack_ratio") > 50)   # IPs that are majority-attacker
        .orderBy(F.col("attack_flows").desc())
        .limit(100)
    )

    joined_rows = [r.asDict() for r in joined.collect()]
    results["ip_port_correlation"] = joined_rows
    print(f"  Done in {time.time()-t0:.2f}s")
    joined.show(10, truncate=False)

    # ══════════════════════════════════════════════════════════════
    # 5. SEVERITY UDF — distributed Python function across partitions
    # ══════════════════════════════════════════════════════════════
    print("\n  [5] Severity UDF across all partitions...")
    t0 = time.time()

    severity_df = (
        df.withColumn(
            "Severity",
            severity_udf(
                F.col("Attack_Category"),
                F.col("Flow Bytes/s"),
                F.col("SYN Flag Count"),
            )
        )
        .groupBy("Attack_Category", "Severity")
        .count()
        .orderBy("Attack_Category", F.col("count").desc())
    )

    severity_rows = [r.asDict() for r in severity_df.collect()]
    results["severity_distribution"] = severity_rows
    print(f"  Done in {time.time()-t0:.2f}s")
    severity_df.show(20)

    # ══════════════════════════════════════════════════════════════
    # 6. PERCENTILE APPROX — statistical depth on 2M rows
    # ══════════════════════════════════════════════════════════════
    print("\n  [6] Percentile approximation (p50, p90, p99)...")
    t0 = time.time()

    percentiles = spark.sql("""
        SELECT
            Attack_Category,
            ROUND(PERCENTILE_APPROX(`Flow Bytes/s`, 0.50), 2)  AS p50_bytes,
            ROUND(PERCENTILE_APPROX(`Flow Bytes/s`, 0.90), 2)  AS p90_bytes,
            ROUND(PERCENTILE_APPROX(`Flow Bytes/s`, 0.99), 2)  AS p99_bytes,
            ROUND(PERCENTILE_APPROX(`Flow Duration`, 0.50), 0) AS p50_duration_us,
            ROUND(PERCENTILE_APPROX(`Flow Duration`, 0.90), 0) AS p90_duration_us
        FROM network_flows
        GROUP BY Attack_Category
        ORDER BY p99_bytes DESC
    """)

    pct_rows = [r.asDict() for r in percentiles.collect()]
    results["flow_percentiles"] = pct_rows
    print(f"  Done in {time.time()-t0:.2f}s")
    percentiles.show(truncate=False)

    # ── Save all results ───────────────────────────────────────────
    out_path = os.path.join(RESULTS_DIR, "advanced_analytics.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  All results saved → {out_path}")

    return results


if __name__ == "__main__":
    run()
