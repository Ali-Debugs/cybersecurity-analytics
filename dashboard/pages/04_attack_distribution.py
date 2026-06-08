"""
04_attack_distribution.py — Attack Distribution
─────────────────────────────────────────────────
Detailed breakdown of every attack label in CICIDS2017.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.utils.data_loader import get_attack_distribution, results_available
from dashboard.utils.charts import attack_pie_chart, attack_bar_chart

st.set_page_config(page_title="Attack Distribution", page_icon="📈", layout="wide")

st.title("📈 Attack Distribution")
st.markdown("Detailed breakdown of attack types from the CICIDS2017 dataset processed by Spark.")

if not results_available():
    st.warning("⚠️ Run analytics first: `python analytics/run_all_analytics.py`")
    st.stop()

data       = get_attack_distribution()
categories = data.get("attack_categories", [])
labels     = data.get("label_distribution", [])
total      = data.get("total_records", 0)

# ── Header KPI ──────────────────────────────────────────────────────
st.metric("Total Network Flows Analysed", f"{total:,}")
st.markdown("---")

# ── Category charts ─────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    fig_pie = attack_pie_chart(categories)
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    fig_bar = attack_bar_chart(categories)
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Category table ──────────────────────────────────────────────────
st.markdown("---")
st.subheader("Attack Category Summary Table")
if categories:
    df_cat = pd.DataFrame(categories)
    df_cat["Count"] = df_cat["Count"].apply(lambda x: f"{int(x):,}")
    st.dataframe(df_cat, use_container_width=True, hide_index=True)

# ── Granular label table ─────────────────────────────────────────────
st.markdown("---")
st.subheader("Granular Label Distribution (CICIDS2017 Raw Labels)")
if labels:
    df_lab = pd.DataFrame(labels)

    fig_labels = px.treemap(
        df_lab,
        path=["Label"],
        values="Count",
        title="Treemap of All Attack Labels",
        color="Count",
        color_continuous_scale="Reds",
        template="plotly_dark",
    )
    fig_labels.update_layout(height=500)
    st.plotly_chart(fig_labels, use_container_width=True)

    df_lab["Count"] = df_lab["Count"].apply(lambda x: f"{int(x):,}")
    st.dataframe(df_lab, use_container_width=True, hide_index=True)
