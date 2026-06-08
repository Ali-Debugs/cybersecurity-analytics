"""
05_benchmarks.py — Performance Benchmark Results
─────────────────────────────────────────────────
Compares Apache Spark vs Pandas processing speed.
Demonstrates PDC scalability advantage.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.utils.data_loader import get_benchmark_summary, results_available
from dashboard.utils.charts import benchmark_comparison_bar, speedup_bar

st.set_page_config(page_title="Performance Benchmarks", page_icon="⚡", layout="wide")

st.title("⚡ Performance Benchmark Results")
st.markdown("Comparing **Apache Spark (distributed)** vs **Pandas (serial)** processing on the same dataset.")

BENCH_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "results", "benchmarks")
bench_exists = os.path.exists(os.path.join(BENCH_DIR, "comparison_summary.json"))

if not bench_exists:
    st.warning("""
    ⚠️ Benchmark results not found.

    Run both benchmarks first:
    ```bash
    python benchmarking/pandas_baseline.py
    python benchmarking/spark_benchmark.py
    python benchmarking/compare_results.py
    ```
    """)
    st.stop()

data = get_benchmark_summary()

pandas_t  = data.get("pandas_total_s", 0)
spark_t   = data.get("spark_total_s", 0)
speedup   = data.get("overall_speedup", 0)
row_count = data.get("row_count", 0)
tasks     = data.get("task_comparison", [])

# ── Top KPIs ─────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("🐼 Pandas Total Time",  f"{pandas_t:.2f}s")
c2.metric("⚡ Spark Total Time",   f"{spark_t:.2f}s")
c3.metric("🚀 Overall Speedup",    f"{speedup}×")
c4.metric("📁 Rows Processed",     f"{row_count:,}")

st.markdown("---")

# ── Charts ───────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Execution Time Comparison")
    fig1 = benchmark_comparison_bar(tasks)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Spark Speedup Factor")
    fig2 = speedup_bar(tasks)
    st.plotly_chart(fig2, use_container_width=True)

# ── Summary gauge ────────────────────────────────────────────────────
st.markdown("---")
col3, col4 = st.columns([1, 2])

with col3:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=speedup,
        title={"text": "Spark Speedup (×)", "font": {"size": 18}},
        gauge={
            "axis"     : {"range": [0, max(speedup * 1.5, 5)]},
            "bar"      : {"color": "#3B82F6"},
            "steps"    : [
                {"range": [0, 1],              "color": "#4B5563"},
                {"range": [1, speedup * 0.7],  "color": "#1D4ED8"},
                {"range": [speedup * 0.7, speedup * 1.5], "color": "#1E3A5F"},
            ],
        },
        number={"suffix": "×", "font": {"size": 48, "color": "#3B82F6"}},
    ))
    fig_gauge.update_layout(template="plotly_dark", height=320)
    st.plotly_chart(fig_gauge, use_container_width=True)

with col4:
    st.subheader("Task-by-Task Breakdown")
    if tasks:
        df_tasks = pd.DataFrame(tasks)
        def color_winner(val):
            if val == "Spark":  return "background-color: #1D4ED8; color: white"
            if val == "Pandas": return "background-color: #7F1D1D; color: white"
            return ""
        styled = df_tasks.style.applymap(color_winner, subset=["Faster"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

# ── PDC explanation ──────────────────────────────────────────────────
st.markdown("---")
st.subheader("Why is Spark Faster? — PDC Concepts")
exp1, exp2, exp3 = st.columns(3)
with exp1:
    st.markdown("""
    **⚡ Parallel Execution**
    Spark splits data into partitions and processes them
    simultaneously across all CPU cores using a DAG scheduler.
    Pandas uses a single thread.
    """)
with exp2:
    st.markdown("""
    **💾 In-Memory Processing**
    Spark caches DataFrames in RAM between operations.
    No disk I/O overhead between transformation steps.
    """)
with exp3:
    st.markdown("""
    **🌐 Distributed Architecture**
    This demo uses `local[*]` mode — the same code scales
    to a 1000-node cluster with zero code changes.
    """)
