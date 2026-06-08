import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.utils.data_loader import (
    get_attack_distribution, get_suspicious_ips,
    get_failed_logins, get_traffic_analysis, results_available
)

st.set_page_config(page_title="Overview", layout="wide")

st.title("Overview")

if not results_available():
    st.warning("No results found. Run `python analytics/run_all_analytics.py` first.")
    st.stop()

atk  = get_attack_distribution()
ips  = get_suspicious_ips()
brut = get_failed_logins()
traf = get_traffic_analysis()

categories = atk.get("attack_categories", [])
total      = atk.get("total_records", 0)

total_attacks = sum(r["Count"] for r in categories if r.get("Attack_Category") != "Benign")
total_benign  = sum(r["Count"] for r in categories if r.get("Attack_Category") == "Benign")
high_ips      = sum(r.get("count", 0) for r in ips.get("threat_summary", []) if r.get("Threat_Level") == "HIGH")
dos_flows     = traf.get("dos_flows", 0) + traf.get("ddos_flows", 0)

# KPIs
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Records",   f"{total:,}")
c2.metric("Attack Flows",    f"{total_attacks:,}")
c3.metric("Benign Flows",    f"{total_benign:,}")
c4.metric("High-Threat IPs", f"{high_ips:,}")
c5.metric("DoS/DDoS Flows",  f"{dos_flows:,}")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Attack Distribution")
    if categories:
        df = pd.DataFrame(categories)
        fig = go.Figure(go.Pie(
            labels=df["Attack_Category"],
            values=df["Count"],
            hole=0.4,
            textinfo="percent+label",
        ))
        fig.update_layout(
            template="plotly_dark",
            height=380,
            showlegend=True,
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Malicious vs Normal")
    fig2 = go.Figure(go.Pie(
        labels=["Attack", "Benign"],
        values=[total_attacks, total_benign],
        marker_colors=["#EF4444", "#22C55E"],
        hole=0.5,
        textinfo="percent+label",
    ))
    fig2.update_layout(
        template="plotly_dark",
        height=380,
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader("Category Breakdown")
if categories:
    df_table = pd.DataFrame(categories)
    df_table["Count"] = df_table["Count"].apply(lambda x: f"{int(x):,}")
    st.dataframe(df_table, use_container_width=True, hide_index=True)
