import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.utils.data_loader import get_suspicious_ips, results_available

st.set_page_config(page_title="Suspicious IPs", page_icon="🔍", layout="wide")

st.title("Suspicious IP Analysis")
st.caption("Source IPs flagged by Spark based on attack flow count.")

if not results_available():
    st.warning("No results found. Run analytics first.")
    st.stop()

data      = get_suspicious_ips()
summary   = data.get("threat_summary", [])
top_ips   = data.get("top_suspicious_ips", [])
threshold = data.get("attack_threshold", 10)

summary_dict = {r.get("Threat_Level"): r.get("count", 0) for r in summary}
high   = summary_dict.get("HIGH", 0)
medium = summary_dict.get("MEDIUM", 0)
low    = summary_dict.get("LOW", 0)
total  = high + medium + low

c1, c2, c3, c4 = st.columns(4)
c1.metric("HIGH Threat IPs",   f"{high:,}")
c2.metric("MEDIUM Threat IPs", f"{medium:,}")
c3.metric("LOW Threat IPs",    f"{low:,}")
c4.metric("Total Unique IPs",  f"{total:,}")

st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Threat Distribution")
    if summary:
        df_sum = pd.DataFrame(summary)
        color_map = {"HIGH": "#EF4444", "MEDIUM": "#F59E0B", "LOW": "#22C55E"}
        colors = [color_map.get(lvl, "#6B7280") for lvl in df_sum["Threat_Level"]]
        fig = go.Figure(go.Pie(
            labels=df_sum["Threat_Level"],
            values=df_sum["count"],
            marker_colors=colors,
            hole=0.45,
            textinfo="percent+label",
        ))
        fig.update_layout(template="plotly_dark", height=300, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader(f"Top Suspicious IPs (≥ {threshold} attack flows)")
    if top_ips:
        df_ips = pd.DataFrame(top_ips)
        cols = [c for c in ["Source IP", "TotalFlows", "AttackFlows", "Attack_Rate_Pct", "Threat_Level"] if c in df_ips.columns]
        st.dataframe(df_ips[cols].head(30), use_container_width=True, hide_index=True, height=300)

st.divider()

if top_ips:
    df_ips = pd.DataFrame(top_ips)
    if "AttackFlows" in df_ips.columns:
        st.subheader("Top 15 IPs by Attack Flows")
        top15 = df_ips.nlargest(15, "AttackFlows")
        color_map = {"HIGH": "#EF4444", "MEDIUM": "#F59E0B", "LOW": "#22C55E"}
        fig2 = px.bar(
            top15, x="Source IP", y="AttackFlows",
            color="Threat_Level",
            color_discrete_map=color_map,
            template="plotly_dark",
        )
        fig2.update_layout(height=360, xaxis_tickangle=-35, margin=dict(t=10))
        st.plotly_chart(fig2, use_container_width=True)
