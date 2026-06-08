import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dashboard.utils.data_loader import get_attack_distribution, results_available

st.set_page_config(page_title="Attack Distribution", layout="wide")

st.title("Attack Distribution")

if not results_available():
    st.warning("No results found. Run analytics first.")
    st.stop()

data       = get_attack_distribution()
categories = data.get("attack_categories", [])
labels     = data.get("label_distribution", [])
total      = data.get("total_records", 0)

st.metric("Total Network Flows Analysed", f"{total:,}")
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("By Category")
    if categories:
        df = pd.DataFrame(categories)
        fig = go.Figure(go.Pie(
            labels=df["Attack_Category"],
            values=df["Count"],
            hole=0.4,
            textinfo="percent+label",
        ))
        fig.update_layout(template="plotly_dark", height=380, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Attack Counts")
    if categories:
        df = pd.DataFrame(categories).sort_values("Count")
        fig2 = go.Figure(go.Bar(
            x=df["Count"], y=df["Attack_Category"],
            orientation="h",
            text=df["Count"].apply(lambda x: f"{int(x):,}"),
            textposition="outside",
            marker_color="#3B82F6",
        ))
        fig2.update_layout(
            template="plotly_dark", height=380,
            xaxis_title="Flows", yaxis_title="",
            margin=dict(t=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

if categories:
    st.subheader("Category Table")
    df_cat = pd.DataFrame(categories).copy()
    df_cat["Count"] = df_cat["Count"].apply(lambda x: f"{int(x):,}")
    st.dataframe(df_cat, use_container_width=True, hide_index=True)

if labels:
    st.divider()
    st.subheader("Granular Label Breakdown")
    df_lab = pd.DataFrame(labels)
    fig3 = px.treemap(
        df_lab, path=["Label"], values="Count",
        color="Count", color_continuous_scale="Blues",
        template="plotly_dark",
    )
    fig3.update_layout(height=460, margin=dict(t=10))
    st.plotly_chart(fig3, use_container_width=True)

    df_lab_disp = df_lab.copy()
    df_lab_disp["Count"] = df_lab_disp["Count"].apply(lambda x: f"{int(x):,}")
    st.dataframe(df_lab_disp, use_container_width=True, hide_index=True)
