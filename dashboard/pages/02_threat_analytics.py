import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.utils.data_loader import get_failed_logins, get_traffic_analysis, results_available

st.set_page_config(page_title="Threat Analytics", page_icon="🎯", layout="wide")

st.title("Threat Analytics")

if not results_available():
    st.warning("No results found. Run analytics first.")
    st.stop()

brut = get_failed_logins()
traf = get_traffic_analysis()

top_port_data = brut.get("top_targeted_ports", [])
top_port = top_port_data[0].get("Destination Port", "N/A") if top_port_data else "N/A"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Brute Force Flows",  f"{brut.get('total_brute_force_flows', 0):,}")
c2.metric("DoS Flows",          f"{traf.get('dos_flows', 0):,}")
c3.metric("DDoS Flows",         f"{traf.get('ddos_flows', 0):,}")
c4.metric("Top Targeted Port",  str(top_port))

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Protocol Distribution")
    proto_data = traf.get("protocol_distribution", [])
    if proto_data:
        df_p = pd.DataFrame(proto_data)
        proto_map = {6: "TCP", 17: "UDP", 1: "ICMP"}
        df_p["Protocol"] = df_p["Protocol"].map(proto_map).fillna(df_p["Protocol"].astype(str))
        fig = px.bar(
            df_p, x="Protocol", y="FlowCount",
            color="Protocol", template="plotly_dark",
            text="FlowCount",
        )
        fig.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig.update_layout(height=320, showlegend=False, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Brute Force by Port")
    if top_port_data:
        df_bp = pd.DataFrame(top_port_data)
        fig2 = px.bar(
            df_bp, x="Destination Port", y="BruteFlows",
            color="BruteFlows", color_continuous_scale="Reds",
            template="plotly_dark", text="BruteFlows",
        )
        fig2.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig2.update_layout(height=320, margin=dict(t=10))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No brute force port data.")

st.divider()

hourly = traf.get("hourly_traffic", [])
if hourly:
    st.subheader("Hourly Traffic by Attack Type")
    df_h = pd.DataFrame(hourly)
    fig3 = px.line(
        df_h, x="Hour", y="Flows", color="Attack_Category",
        template="plotly_dark", markers=True,
    )
    fig3.update_layout(height=360, margin=dict(t=10))
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

flow_bytes = traf.get("flow_bytes_by_attack", [])
if flow_bytes:
    st.subheader("Traffic Profile by Attack Type")
    st.dataframe(pd.DataFrame(flow_bytes), use_container_width=True, hide_index=True)

hourly_brute = brut.get("hourly_pattern", [])
if hourly_brute:
    st.divider()
    st.subheader("Brute Force Activity by Hour")
    df_hb = pd.DataFrame(hourly_brute)
    fig4 = px.bar(
        df_hb, x="Hour", y="BruteFlows",
        template="plotly_dark", color_discrete_sequence=["#8B5CF6"],
    )
    fig4.update_layout(height=300, margin=dict(t=10))
    st.plotly_chart(fig4, use_container_width=True)
