"""
compare_results.py
───────────────────
Loads pandas_benchmark.json and spark_benchmark.json,
generates a comparison table, and saves comparison charts.
"""

import os
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from colorama import Fore, Style
import colorama

colorama.init(autoreset=True)

BENCH_DIR = os.path.join(os.path.dirname(__file__), "..", "results", "benchmarks")


def load_results():
    pandas_path = os.path.join(BENCH_DIR, "pandas_benchmark.json")
    spark_path  = os.path.join(BENCH_DIR, "spark_benchmark.json")

    with open(pandas_path) as f:
        pandas_r = json.load(f)
    with open(spark_path) as f:
        spark_r = json.load(f)

    return pandas_r, spark_r


def generate_comparison():
    print(f"\n{Style.BRIGHT}Performance Comparison: Pandas vs Spark")
    print("=" * 55)

    pandas_r, spark_r = load_results()

    tasks = ["load", "attack_distribution", "suspicious_ip",
             "failed_logins", "traffic_analysis"]

    rows = []
    for task in tasks:
        pt = pandas_r["timings_seconds"].get(task, 0)
        st = spark_r["timings_seconds"].get(task, 0)
        speedup = round(pt / st, 2) if st > 0 else 0
        rows.append({
            "Task"              : task.replace("_", " ").title(),
            "Pandas (s)"        : pt,
            "Spark (s)"         : st,
            "Speedup (×)"       : speedup,
            "Faster"            : "Spark" if st < pt else "Pandas",
        })

    df = pd.DataFrame(rows)
    print(f"\n{df.to_string(index=False)}")

    # Totals row
    pt_total = pandas_r["total_seconds"]
    st_total = spark_r["total_seconds"]
    overall_speedup = round(pt_total / st_total, 2) if st_total > 0 else 0
    print(f"\n  Total — Pandas: {pt_total:.3f}s | "
          f"Spark: {st_total:.3f}s | "
          f"Overall Speedup: {overall_speedup}×")

    # ── Bar chart ─────────────────────────────────────────────────
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Pandas",
        x=df["Task"],
        y=df["Pandas (s)"],
        marker_color="#EF4444",
    ))
    fig_bar.add_trace(go.Bar(
        name="Spark",
        x=df["Task"],
        y=df["Spark (s)"],
        marker_color="#3B82F6",
    ))
    fig_bar.update_layout(
        title="Pandas vs Spark: Execution Time per Task",
        xaxis_title="Task",
        yaxis_title="Time (seconds)",
        barmode="group",
        template="plotly_dark",
        height=450,
    )
    bar_path = os.path.join(BENCH_DIR, "comparison_bar.html")
    fig_bar.write_html(bar_path)
    print(f"\n  Bar chart saved → {bar_path}")

    # ── Speedup chart ─────────────────────────────────────────────
    fig_su = px.bar(
        df,
        x="Task",
        y="Speedup (×)",
        color="Speedup (×)",
        color_continuous_scale="Blues",
        title="Spark Speedup over Pandas (×)",
        template="plotly_dark",
        height=400,
    )
    fig_su.add_hline(y=1, line_dash="dash", line_color="white",
                     annotation_text="Baseline (1×)")
    su_path = os.path.join(BENCH_DIR, "speedup_chart.html")
    fig_su.write_html(su_path)
    print(f"  Speedup chart saved → {su_path}")

    # Save summary JSON for dashboard
    summary = {
        "pandas_total_s"   : pt_total,
        "spark_total_s"    : st_total,
        "overall_speedup"  : overall_speedup,
        "row_count"        : spark_r["row_count"],
        "task_comparison"  : rows,
    }
    summary_path = os.path.join(BENCH_DIR, "comparison_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary JSON saved → {summary_path}")

    return summary


if __name__ == "__main__":
    generate_comparison()
