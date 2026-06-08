"""
01_overview.py — Overview Dashboard
─────────────────────────────────────
KPI cards + summary charts at a glance.
"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.utils.data_loader import (
    get_attack_distribution, get_suspicious_ips,
    get_failed_logins, get_traffic_analysis, results_available
)
from dashboard.utils.charts import attack_pie_chart

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")

st.title("📊 Overview Dashboard")
st.markdown("High-level security posture at a glance.")

if not results_available():
    st.warning("⚠️ No analytics results found. Run `python analytics/run_all_analytics.py` first.")
    st.stop()

# ── Load data ────────────────────────────────────────────────────────
atk  = get_attack_distribution()
ips  = get_suspicious_ips()
brut = get_failed_logins()
traf = get_traffic_analysis()

total_records  = atk.get("total_records", 0)
categories     = atk.get("attack_categories", [])

# ── KPI row ─────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

total_attacks = sum(
    r["Count"] for r in categories if r.get("Attack_Category") != "Benign"
)
total_benign  = sum(
    r["Count"] for r in categories if r.get("Attack_Category") == "Benign"
)
high_threat_count = sum(
    r.get("count", 0) for r in ips.get("threat_summary", [])
    if r.get("Threat_Level") == "HIGH"
)
brute_count = brut.get("total_brute_force_flows", 0)
dos_flows   = traf.get("dos_flows", 0) + traf.get("ddos_flows", 0)

k1.metric("📁 Total Records",   f"{total_records:,}")
k2.metric("🔴 Attack Flows",    f"{total_attacks:,}")
k3.metric("✅ Benign Flows",    f"{total_benign:,}")
k4.metric("⚠️ High-Threat IPs", f"{high_threat_count:,}")
k5.metric("💥 DoS/DDoS Flows",  f"{dos_flows:,}")

st.markdown("---")

# ── Charts ──────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Attack Category Distribution")
    fig = attack_pie_chart(categories)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Attack vs Benign Ratio")
    import plotly.graph_objects as go
    fig2 = go.Figure(go.Pie(
        labels=["Attack", "Benign"],
        values=[total_attacks, total_benign],
        marker_colors=["#EF4444", "#22C55E"],
        hole=0.5,
    ))
    fig2.update_layout(template="plotly_dark", height=420,
                       title="Malicious vs Normal Traffic")
    st.plotly_chart(fig2, use_container_width=True)

# ── Data table ──────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Attack Category Breakdown")
if categories:
    df_table = pd.DataFrame(categories)
    st.dataframe(
        df_table.style.background_gradient(subset=["Count"], cmap="Reds"),
        use_container_width=True
    )
