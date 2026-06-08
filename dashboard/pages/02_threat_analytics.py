"""
02_threat_analytics.py — Threat Analytics
───────────────────────────────────────────
Time-series traffic patterns + brute force breakdown.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.utils.data_loader import (
    get_failed_logins, get_traffic_analysis, results_available
)
from dashboard.utils.charts import hourly_traffic_line, protocol_bar

st.set_page_config(page_title="Threat Analytics", page_icon="🎯", layout="wide")

st.title("🎯 Threat Analytics")
st.markdown("Traffic patterns, protocol distribution, and brute-force activity.")

if not results_available():
    st.warning("⚠️ Run analytics first: `python analytics/run_all_analytics.py`")
    st.stop()

brut = get_failed_logins()
traf = get_traffic_analysis()

# ── KPIs ────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("🔑 Brute Force Flows",  f"{brut.get('total_brute_force_flows', 0):,}")
c2.metric("💥 DoS Flows",          f"{traf.get('dos_flows', 0):,}")
c3.metric("🌊 DDoS Flows",         f"{traf.get('ddos_flows', 0):,}")
top_port_data = brut.get("top_targeted_ports", [])
top_port = top_port_data[0]["Destination Port"] if top_port_data else "N/A"
c4.metric("🎯 Top Targeted Port",  str(top_port))

st.markdown("---")

# ── Protocol distribution ───────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.subheader("Protocol Distribution")
    proto_data = traf.get("protocol_distribution", [])
    fig = protocol_bar(proto_data)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Brute Force by Port")
    port_data = brut.get("top_targeted_ports", [])
    if port_data:
        df_p = pd.DataFrame(port_data)
        fig2 = px.bar(
            df_p,
            x="Destination Port",
            y="BruteFlows",
            title="Brute Force Flows by Destination Port",
            color="BruteFlows",
            color_continuous_scale="Reds",
            template="plotly_dark",
        )
        fig2.update_layout(height=350)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No brute force port data available.")

# ── Hourly traffic ──────────────────────────────────────────────────
st.markdown("---")
st.subheader("Hourly Traffic Volume by Attack Type")
hourly = traf.get("hourly_traffic", [])
if hourly:
    fig3 = hourly_traffic_line(hourly)
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Hourly data not available (Timestamp column may be missing).")

# ── Traffic profile table ────────────────────────────────────────────
st.markdown("---")
st.subheader("Traffic Profile by Attack Category")
flow_bytes = traf.get("flow_bytes_by_attack", [])
if flow_bytes:
    st.dataframe(pd.DataFrame(flow_bytes), use_container_width=True)

# ── Brute force hourly ──────────────────────────────────────────────
st.markdown("---")
hourly_brute = brut.get("hourly_pattern", [])
if hourly_brute:
    st.subheader("Brute Force Activity by Hour")
    df_hb = pd.DataFrame(hourly_brute)
    fig4 = px.line(
        df_hb, x="Hour", y="BruteFlows",
        title="Brute Force Flows per Hour",
        markers=True, template="plotly_dark",
        color_discrete_sequence=["#8B5CF6"],
    )
    st.plotly_chart(fig4, use_container_width=True)
