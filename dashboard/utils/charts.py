"""
charts.py
──────────
Reusable Plotly chart factory functions for the dashboard.
All charts use a consistent dark cybersecurity theme.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict

# ── Colour palette ─────────────────────────────────────────────────
COLORS = {
    "Benign"       : "#22C55E",   # green
    "DoS"          : "#EF4444",   # red
    "DDoS"         : "#DC2626",   # darker red
    "Port Scan"    : "#F59E0B",   # amber
    "Brute Force"  : "#8B5CF6",   # purple
    "Web Attack"   : "#3B82F6",   # blue
    "Bot"          : "#EC4899",   # pink
    "Infiltration" : "#14B8A6",   # teal
    "Heartbleed"   : "#F97316",   # orange
    "Other"        : "#6B7280",   # grey
}

DARK_TEMPLATE = "plotly_dark"


def attack_pie_chart(categories: List[Dict]) -> go.Figure:
    """Pie chart of attack category distribution."""
    df = pd.DataFrame(categories)
    if df.empty:
        return go.Figure()

    fig = px.pie(
        df,
        names="Attack_Category",
        values="Count",
        title="Attack Category Distribution",
        color="Attack_Category",
        color_discrete_map=COLORS,
        template=DARK_TEMPLATE,
        hole=0.4,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(showlegend=True, height=420)
    return fig


def attack_bar_chart(categories: List[Dict]) -> go.Figure:
    """Horizontal bar chart of attack counts."""
    df = pd.DataFrame(categories).sort_values("Count", ascending=True)
    if df.empty:
        return go.Figure()

    colors = [COLORS.get(cat, "#6B7280") for cat in df["Attack_Category"]]

    fig = go.Figure(go.Bar(
        x=df["Count"],
        y=df["Attack_Category"],
        orientation="h",
        marker_color=colors,
        text=df["Count"].apply(lambda x: f"{x:,}"),
        textposition="outside",
    ))
    fig.update_layout(
        title="Attack Counts by Category",
        xaxis_title="Number of Flows",
        yaxis_title="Attack Type",
        template=DARK_TEMPLATE,
        height=400,
    )
    return fig


def threat_level_gauge(high: int, medium: int, low: int) -> go.Figure:
    """Gauge showing proportion of high-threat IPs."""
    total = high + medium + low
    pct   = (high / total * 100) if total > 0 else 0

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        title={"text": "% High-Threat IPs", "font": {"size": 16}},
        delta={"reference": 5, "valueformat": ".1f"},
        gauge={
            "axis"     : {"range": [0, 100]},
            "bar"      : {"color": "#EF4444"},
            "steps"    : [
                {"range": [0, 20],  "color": "#1F2937"},
                {"range": [20, 50], "color": "#374151"},
                {"range": [50, 100],"color": "#4B5563"},
            ],
            "threshold": {
                "line" : {"color": "orange", "width": 4},
                "thickness": 0.75,
                "value": 10,
            },
        },
    ))
    fig.update_layout(template=DARK_TEMPLATE, height=300)
    return fig


def hourly_traffic_line(hourly_data: List[Dict]) -> go.Figure:
    """Line chart of traffic flows per hour broken by attack category."""
    if not hourly_data:
        return go.Figure()

    df = pd.DataFrame(hourly_data)
    if df.empty or "Hour" not in df.columns:
        return go.Figure()

    fig = px.line(
        df,
        x="Hour",
        y="Flows",
        color="Attack_Category",
        title="Traffic Volume by Hour and Attack Type",
        color_discrete_map=COLORS,
        template=DARK_TEMPLATE,
        markers=True,
    )
    fig.update_layout(
        xaxis_title="Hour of Day",
        yaxis_title="Number of Flows",
        height=400,
    )
    return fig


def protocol_bar(protocol_data: List[Dict]) -> go.Figure:
    """Bar chart for protocol distribution."""
    df = pd.DataFrame(protocol_data)
    if df.empty:
        return go.Figure()

    proto_map = {6: "TCP", 17: "UDP", 1: "ICMP"}
    df["Protocol"] = df["Protocol"].map(proto_map).fillna(df["Protocol"].astype(str))

    fig = px.bar(
        df,
        x="Protocol",
        y="FlowCount",
        title="Network Protocol Distribution",
        color="Protocol",
        template=DARK_TEMPLATE,
        text="FlowCount",
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(height=350, showlegend=False)
    return fig


def benchmark_comparison_bar(task_comparison: List[Dict]) -> go.Figure:
    """Grouped bar chart: Pandas vs Spark time per task."""
    df = pd.DataFrame(task_comparison)
    if df.empty:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Pandas", x=df["Task"], y=df["Pandas (s)"],
                         marker_color="#EF4444"))
    fig.add_trace(go.Bar(name="Spark",  x=df["Task"], y=df["Spark (s)"],
                         marker_color="#3B82F6"))
    fig.update_layout(
        title="Processing Time: Pandas vs Apache Spark",
        xaxis_title="Task",
        yaxis_title="Seconds",
        barmode="group",
        template=DARK_TEMPLATE,
        height=420,
    )
    return fig


def speedup_bar(task_comparison: List[Dict]) -> go.Figure:
    """Bar chart showing Spark speedup multiplier per task."""
    df = pd.DataFrame(task_comparison)
    if df.empty:
        return go.Figure()

    fig = px.bar(
        df,
        x="Task",
        y="Speedup (×)",
        title="Spark Speedup over Pandas",
        color="Speedup (×)",
        color_continuous_scale="Blues",
        template=DARK_TEMPLATE,
        text="Speedup (×)",
    )
    fig.add_hline(y=1, line_dash="dash", line_color="white",
                  annotation_text="1× Baseline")
    fig.update_traces(texttemplate="%{text:.1f}×", textposition="outside")
    fig.update_layout(height=380)
    return fig
