"""
03_suspicious_ips.py — Suspicious IP Analysis
───────────────────────────────────────────────
Table + charts of flagged malicious IPs.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.utils.data_loader import get_suspicious_ips, results_available
from dashboard.utils.charts import threat_level_gauge

st.set_page_config(page_title="Suspicious IPs", page_icon="🔍", layout="wide")

st.title("🔍 Suspicious IP Analysis")
st.markdown("Source IPs flagged by Spark as high-threat based on attack flow count.")

if not results_available():
    st.warning("⚠️ Run analytics first: `python analytics/run_all_analytics.py`")
    st.stop()

data = get_suspicious_ips()
summary   = data.get("threat_summary", [])
top_ips   = data.get("top_suspicious_ips", [])
threshold = data.get("attack_threshold", 10)

# ── Threat level KPIs ───────────────────────────────────────────────
summary_dict = {r.get("Threat_Level"): r.get("count", 0) for r in summary}
high   = summary_dict.get("HIGH", 0)
medium = summary_dict.get("MEDIUM", 0)
low    = summary_dict.get("LOW", 0)
total  = high + medium + low

c1, c2, c3, c4 = st.columns(4)
c1.metric("🔴 HIGH Threat IPs",   f"{high:,}")
c2.metric("🟡 MEDIUM Threat IPs", f"{medium:,}")
c3.metric("🟢 LOW Threat IPs",    f"{low:,}")
c4.metric("📊 Total Unique IPs",  f"{total:,}")

st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Threat Level Gauge")
    gauge = threat_level_gauge(high, medium, low)
    st.plotly_chart(gauge, use_container_width=True)

    st.subheader("Threat Distribution")
    df_sum = pd.DataFrame(summary)
    if not df_sum.empty:
        import plotly.graph_objects as go
        color_map = {"HIGH": "#EF4444", "MEDIUM": "#F59E0B", "LOW": "#22C55E"}
        df_sum["color"] = df_sum["Threat_Level"].map(color_map)
        fig_pie = go.Figure(go.Pie(
            labels=df_sum["Threat_Level"],
            values=df_sum["count"],
            marker_colors=df_sum["color"],
            hole=0.4,
        ))
        fig_pie.update_layout(template="plotly_dark", height=280)
        st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.subheader(f"Top Suspicious Source IPs (≥{threshold} attack flows)")
    if top_ips:
        df_ips = pd.DataFrame(top_ips)
        # Show the most important columns
        cols = [c for c in ["Source IP", "TotalFlows", "AttackFlows",
                             "Attack_Rate_Pct", "Threat_Level"]
                if c in df_ips.columns]
        df_display = df_ips[cols].head(30)

        # Color rows by threat
        def color_threat(val):
            if val == "HIGH":   return "background-color: #4B0000; color: #FCA5A5"
            if val == "MEDIUM": return "background-color: #422006; color: #FCD34D"
            return ""

        if "Threat_Level" in df_display.columns:
            st.dataframe(
                df_display.style.applymap(color_threat, subset=["Threat_Level"]),
                use_container_width=True, height=450
            )
        else:
            st.dataframe(df_display, use_container_width=True)

        # Bar chart of top 15 IPs
        st.subheader("Top 15 IPs by Attack Flows")
        if "AttackFlows" in df_ips.columns:
            top15 = df_ips.nlargest(15, "AttackFlows")
            fig_bar = px.bar(
                top15,
                x="Source IP",
                y="AttackFlows",
                color="Threat_Level",
                color_discrete_map={"HIGH": "#EF4444", "MEDIUM": "#F59E0B", "LOW": "#22C55E"},
                title="Top 15 Source IPs by Attack Flow Count",
                template="plotly_dark",
            )
            fig_bar.update_layout(height=350, xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No suspicious IPs found above threshold.")
