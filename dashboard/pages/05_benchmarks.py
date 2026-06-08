import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.utils.data_loader import get_benchmark_summary, results_available

st.set_page_config(page_title="Benchmarks", layout="wide")

st.title("Performance Benchmarks")

BENCH_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "results", "benchmarks")
if not os.path.exists(os.path.join(BENCH_DIR, "comparison_summary.json")):
    st.warning("No benchmark results. Run `benchmarking/compare_results.py` first.")
    st.stop()

data      = get_benchmark_summary()
pandas_t  = data.get("pandas_total_s", 0)
spark_t   = data.get("spark_total_s", 0)
speedup   = data.get("overall_speedup", 0)
row_count = data.get("row_count", 0)
tasks     = data.get("task_comparison", [])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Pandas Total",   f"{pandas_t:.2f}s")
c2.metric("Spark Total",    f"{spark_t:.2f}s")
c3.metric("Speedup",        f"{speedup}×")
c4.metric("Rows Processed", f"{row_count:,}")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Execution Time per Task")
    if tasks:
        df = pd.DataFrame(tasks)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Pandas", x=df["Task"], y=df["Pandas (s)"], marker_color="#EF4444"))
        fig.add_trace(go.Bar(name="Spark",  x=df["Task"], y=df["Spark (s)"],  marker_color="#3B82F6"))
        fig.update_layout(
            barmode="group", template="plotly_dark", height=360,
            xaxis_title="", yaxis_title="Seconds",
            margin=dict(t=10),
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Speedup Factor (Spark / Pandas)")
    if tasks:
        df = pd.DataFrame(tasks)
        fig2 = px.bar(
            df, x="Task", y="Speedup (×)",
            color="Speedup (×)", color_continuous_scale="Blues",
            template="plotly_dark",
            text="Speedup (×)",
        )
        fig2.add_hline(y=1, line_dash="dash", line_color="white", annotation_text="1× baseline")
        fig2.update_traces(texttemplate="%{text:.2f}×", textposition="outside")
        fig2.update_layout(height=360, margin=dict(t=10))
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

if tasks:
    st.subheader("Task Comparison Table")
    df_t = pd.DataFrame(tasks)
    st.dataframe(df_t, use_container_width=True, hide_index=True)

