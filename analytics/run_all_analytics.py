"""
run_all_analytics.py
─────────────────────
Master runner — executes all Spark analytics jobs in sequence
using a single shared SparkSession (avoids repeated JVM startup).

Usage:
    python analytics/run_all_analytics.py
"""

import time
import json
import os
from analytics.spark_session import get_spark
import analytics.attack_distribution as ad
import analytics.suspicious_ip       as si
import analytics.failed_logins       as fl
import analytics.traffic_analysis    as ta

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "analytics")


def main():
    print("\n" + "=" * 60)
    print("  CYBERSECURITY ANALYTICS PLATFORM — SPARK JOBS")
    print("=" * 60)

    start_total = time.time()
    spark = get_spark("CybersecurityAnalytics-AllJobs")

    timings = {}
    results = {}

    jobs = [
        ("Attack Distribution",  ad.run),
        ("Suspicious IP",        si.run),
        ("Failed Logins",        fl.run),
        ("Traffic Analysis",     ta.run),
    ]

    for name, fn in jobs:
        print(f"\n{'─'*55}")
        print(f"  Running: {name}")
        print(f"{'─'*55}")
        t0 = time.time()
        try:
            results[name] = fn(spark=spark)
            elapsed = time.time() - t0
            timings[name] = round(elapsed, 2)
            print(f"  ✓ {name} completed in {elapsed:.2f}s")
        except Exception as e:
            timings[name] = -1
            print(f"  ✗ {name} FAILED: {e}")
            import traceback; traceback.print_exc()

    total_elapsed = time.time() - start_total

    # Save timing summary
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timing_out = os.path.join(RESULTS_DIR, "job_timings.json")
    with open(timing_out, "w") as f:
        json.dump({"timings_seconds": timings,
                   "total_seconds": round(total_elapsed, 2)}, f, indent=2)

    print("\n" + "=" * 60)
    print("  ALL JOBS COMPLETE")
    print("=" * 60)
    for job, t in timings.items():
        status = f"{t:.2f}s" if t > 0 else "FAILED"
        print(f"  {job:<30} {status}")
    print(f"\n  Total time: {total_elapsed:.2f}s")
    print(f"  Timings saved → {timing_out}")

    spark.stop()


if __name__ == "__main__":
    main()
