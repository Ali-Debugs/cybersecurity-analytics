"""
app.py — Streamlit Dashboard Entry Point
─────────────────────────────────────────
Distributed Cybersecurity Log Analytics Platform
  • Hadoop HDFS  — distributed storage
  • Apache Spark — distributed processing
  • Streamlit    — interactive dashboard
  • Plotly       — visualizations

Run: streamlit run dashboard/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="CyberSec Analytics Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark cyber theme */
    .main { background-color: #0F172A; }
    .stMetric { background-color: #1E293B; border-radius: 8px; padding: 12px; }
    .stMetricLabel { color: #94A3B8 !important; font-size: 0.85rem; }
    .stMetricValue { color: #F1F5F9 !important; font-size: 1.8rem; font-weight: 700; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #1E293B; }

    /* Title banner */
    .hero-banner {
        background: linear-gradient(135deg, #1E3A5F 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px 32px;
        margin-bottom: 24px;
    }
    .hero-title { color: #38BDF8; font-size: 2rem; font-weight: 800; margin: 0; }
    .hero-sub   { color: #94A3B8; font-size: 1rem; margin-top: 6px; }

    /* Divider */
    hr { border-color: #334155; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar navigation ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ CyberSec Analytics")
    st.markdown("---")
    st.markdown("**Stack**")
    st.markdown("- 🐘 Hadoop HDFS 3.5")
    st.markdown("- ⚡ Apache Spark 4.1")
    st.markdown("- 🐍 PySpark + Python")
    st.markdown("- 📊 Streamlit + Plotly")
    st.markdown("---")
    st.markdown("**Dataset**")
    st.markdown("CICIDS2017")
    st.markdown("Canadian Institute for Cybersecurity")
    st.markdown("---")
    st.caption("University PDC Project · 2026")

# ── Hero banner ──────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
  <p class="hero-title">🛡️ Distributed Cybersecurity Log Analytics Platform</p>
  <p class="hero-sub">
    Real-time threat detection powered by Hadoop HDFS + Apache Spark
  </p>
</div>
""", unsafe_allow_html=True)

# ── Quick-start info ────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.info("""
    **Navigate using the sidebar pages:**
    - 📊 **Overview** — KPI dashboard
    - 🎯 **Threat Analytics** — Attack patterns
    - 🔍 **Suspicious IPs** — Malicious hosts
    - 📈 **Attack Distribution** — Category breakdown
    - ⚡ **Performance Benchmarks** — Spark vs Pandas
    """)

with col2:
    st.success("""
    **Architecture:**
    ```
    CICIDS2017 Dataset
         ↓
    Preprocessing (Python)
         ↓
    HDFS Storage (Hadoop)
         ↓
    Spark Analytics (PySpark)
         ↓
    Dashboard (Streamlit)
    ```
    """)

# ── PDC concepts callout ────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🧠 PDC Concepts Demonstrated")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("**⚡ Parallel Processing**  \nSpark `local[*]` uses all CPU cores simultaneously")
with c2:
    st.markdown("**🌐 Distributed Storage**  \nHDFS splits data into 128 MB blocks across DataNodes")
with c3:
    st.markdown("**🔀 Data Partitioning**  \nSpark RDDs partitioned for parallel execution")
with c4:
    st.markdown("**📈 Scalability**  \nSame code works on 1 node or 1000-node cluster")
