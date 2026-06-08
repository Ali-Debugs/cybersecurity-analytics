import streamlit as st

st.set_page_config(
    page_title="Cybersecurity Analytics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.markdown("### 🛡️ Cybersecurity Analytics")
    st.divider()
    st.markdown("**Stack**")
    st.markdown("- Hadoop HDFS 3.5")
    st.markdown("- Apache Spark 4.1")
    st.markdown("- PySpark / Python 3.12")
    st.markdown("- Streamlit + Plotly")
    st.divider()
    st.markdown("**Dataset**")
    st.markdown("CICIDS2017")
    st.markdown("Canadian Institute for Cybersecurity")
    st.divider()
    st.caption("University PDC Project · 2026")

st.title("Distributed Cybersecurity Log Analytics Platform")
st.caption("Hadoop HDFS + Apache Spark · CICIDS2017 Dataset")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Use the sidebar to navigate:**")
    st.markdown("- **Overview** — KPI summary")
    st.markdown("- **Threat Analytics** — Traffic patterns, brute force")
    st.markdown("- **Suspicious IPs** — Flagged source addresses")
    st.markdown("- **Attack Distribution** — Category breakdown")
    st.markdown("- **Benchmarks** — Spark vs Pandas speed")

with col2:
    st.markdown("**Architecture:**")
    st.code("""CICIDS2017 Dataset
      ↓
Preprocessing (Python)
      ↓
Hadoop HDFS  (distributed storage)
      ↓
Apache Spark (distributed analytics)
      ↓
Streamlit Dashboard""", language=None)

st.divider()
st.markdown("**PDC Concepts Demonstrated**")

c1, c2, c3, c4 = st.columns(4)
c1.markdown("**Parallel Processing**  \nSpark uses all CPU cores via `local[*]`")
c2.markdown("**Distributed Storage**  \nHDFS splits data into 128 MB blocks")
c3.markdown("**Data Partitioning**  \nSpark RDDs partitioned across workers")
c4.markdown("**Scalability**  \nSame code runs on 1 node or 1000 nodes")
