import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.utils.data_loader import get_advanced_analytics, results_available

st.set_page_config(page_title="Advanced Analytics", layout="wide")

st.title("Advanced Analytics")
st.caption("Spark SQL · Window Functions · Joins · UDF · Percentiles — on 2,572,640 rows from HDFS")

ADVAN_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "results", "analytics", "advanced_analytics.json")
if not os.path.exists(ADVAN_PATH):
    st.warning("Run `python analytics/run_all_analytics.py` first.")
    st.stop()

data = get_advanced_analytics()

# ── 1. Spark SQL attack profile ────────────────────────────────────
st.subheader("Attack Profile (Spark SQL on HDFS temp view)")
sql_rows = data.get("sql_attack_profile", [])
if sql_rows:
    df_sql = pd.DataFrame(sql_rows)
    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df_sql, x="Attack_Category", y="total_flows",
            color="Attack_Category", template="plotly_dark",
            text="total_flows",
        )
        fig.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig.update_layout(height=340, showlegend=False,
                          xaxis_title="", yaxis_title="Flows",
                          margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(
            df_sql, x="Attack_Category", y="avg_bytes_per_sec",
            color="avg_bytes_per_sec", color_continuous_scale="Reds",
            template="plotly_dark", text="avg_bytes_per_sec",
        )
        fig2.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig2.update_layout(height=340, xaxis_title="", yaxis_title="Avg Bytes/s",
                           margin=dict(t=10))
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(df_sql, use_container_width=True, hide_index=True)

st.divider()

# ── 2. Window function — ranked IPs per attack type ────────────────
st.subheader("Top IPs per Attack Type (Window RANK)")
ranked_rows = data.get("top_ips_per_attack_windowed", [])
if ranked_rows:
    df_rank = pd.DataFrame(ranked_rows)

    attack_types = sorted(df_rank["Attack_Category"].unique())
    selected = st.selectbox("Attack type", attack_types)

    df_sel = df_rank[df_rank["Attack_Category"] == selected].copy()

    col1, col2 = st.columns([2, 1])
    with col1:
        fig3 = px.bar(
            df_sel, x="Source IP", y="flow_count",
            text="flow_count", template="plotly_dark",
            color="flow_count", color_continuous_scale="Blues",
        )
        fig3.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig3.update_layout(height=320, xaxis_title="", yaxis_title="Flows",
                           margin=dict(t=10), showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.dataframe(
            df_sel[["rank", "Source IP", "flow_count", "pct_of_category"]],
            use_container_width=True, hide_index=True
        )

st.divider()

# ── 3. LAG — hourly attack delta ───────────────────────────────────
st.subheader("Hourly Attack Delta (LAG Window Function)")
hourly_rows = data.get("hourly_attack_delta", [])
if hourly_rows:
    df_hourly = pd.DataFrame(hourly_rows)
    attack_types2 = sorted(df_hourly["Attack_Category"].unique())
    selected2 = st.selectbox("Attack type ", attack_types2, key="lag_select")

    df_h = df_hourly[df_hourly["Attack_Category"] == selected2].copy()

    col1, col2 = st.columns(2)
    with col1:
        fig4 = px.line(
            df_h, x="Hour", y="flows",
            template="plotly_dark", markers=True,
            title="Flow count by hour",
        )
        fig4.update_layout(height=300, margin=dict(t=30))
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        fig5 = px.bar(
            df_h, x="Hour", y="delta",
            color="delta",
            color_continuous_scale="RdBu",
            color_continuous_midpoint=0,
            template="plotly_dark",
            title="Change from previous hour",
        )
        fig5.update_layout(height=300, margin=dict(t=30))
        st.plotly_chart(fig5, use_container_width=True)

st.divider()

# ── 4. Join result — IP × port correlation ─────────────────────────
st.subheader("IP Threat Profile × Port Behaviour (Spark Join)")
joined_rows = data.get("ip_port_correlation", [])
if joined_rows:
    df_join = pd.DataFrame(joined_rows).head(20)
    cols = [c for c in ["Source IP", "total_flows", "attack_flows",
                        "attack_ratio", "unique_ports_targeted",
                        "primary_target_port"] if c in df_join.columns]

    col1, col2 = st.columns([3, 2])
    with col1:
        st.dataframe(df_join[cols], use_container_width=True, hide_index=True)

    with col2:
        if "unique_ports_targeted" in df_join.columns:
            fig6 = px.scatter(
                df_join,
                x="unique_ports_targeted",
                y="attack_ratio",
                size="total_flows",
                color="attack_ratio",
                color_continuous_scale="Reds",
                hover_name="Source IP",
                template="plotly_dark",
                labels={"unique_ports_targeted": "Unique Ports Targeted",
                        "attack_ratio": "% Attack Traffic"},
            )
            fig6.update_layout(height=340, margin=dict(t=10))
            st.plotly_chart(fig6, use_container_width=True)

st.divider()

# ── 5. UDF severity distribution ──────────────────────────────────
st.subheader("Severity Distribution (Custom UDF)")
sev_rows = data.get("severity_distribution", [])
if sev_rows:
    df_sev = pd.DataFrame(sev_rows)
    color_map = {"Critical": "#DC2626", "High": "#EF4444",
                 "Medium": "#F59E0B", "Low": "#22C55E"}

    col1, col2 = st.columns(2)
    with col1:
        fig7 = px.bar(
            df_sev, x="Attack_Category", y="count",
            color="Severity", color_discrete_map=color_map,
            template="plotly_dark", barmode="stack",
        )
        fig7.update_layout(height=360, xaxis_title="",
                           yaxis_title="Flows", margin=dict(t=10))
        st.plotly_chart(fig7, use_container_width=True)

    with col2:
        df_sev_agg = df_sev.groupby("Severity", as_index=False)["count"].sum()
        fig8 = go.Figure(go.Pie(
            labels=df_sev_agg["Severity"],
            values=df_sev_agg["count"],
            marker_colors=[color_map.get(s, "#6B7280") for s in df_sev_agg["Severity"]],
            hole=0.45,
            textinfo="percent+label",
        ))
        fig8.update_layout(template="plotly_dark", height=360, margin=dict(t=10))
        st.plotly_chart(fig8, use_container_width=True)

st.divider()

# ── 6. Percentile stats ────────────────────────────────────────────
st.subheader("Flow Byte Percentiles (PERCENTILE_APPROX on 2M rows)")
pct_rows = data.get("flow_percentiles", [])
if pct_rows:
    df_pct = pd.DataFrame(pct_rows)

    fig9 = go.Figure()
    for col, label in [("p50_bytes", "p50"), ("p90_bytes", "p90"), ("p99_bytes", "p99")]:
        fig9.add_trace(go.Bar(
            name=label, x=df_pct["Attack_Category"], y=df_pct[col], text=df_pct[col],
        ))
    fig9.update_layout(
        barmode="group", template="plotly_dark", height=360,
        xaxis_title="", yaxis_title="Bytes/s",
        margin=dict(t=10),
    )
    st.plotly_chart(fig9, use_container_width=True)

    st.dataframe(df_pct, use_container_width=True, hide_index=True)
