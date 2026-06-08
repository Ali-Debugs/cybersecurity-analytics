import streamlit as st

st.set_page_config(
    page_title="Cybersecurity Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.markdown("### Cybersecurity Analytics")
    st.divider()
    st.markdown("Hadoop HDFS 3.5")
    st.markdown("Apache Spark 4.1")
    st.markdown("Python 3.12 / PySpark")
    st.markdown("Streamlit + Plotly")
    st.divider()
    st.markdown("Dataset: CICIDS2017")
    st.divider()
    st.caption("University PDC Project · 2026")

st.title("Distributed Cybersecurity Log Analytics Platform")
st.caption("CICIDS2017 · Hadoop HDFS · Apache Spark")

st.divider()

st.markdown("Use the sidebar to navigate between pages.")
st.markdown("""
- **Overview** — summary metrics
- **Threat Analytics** — traffic and brute force patterns
- **Suspicious IPs** — source addresses with high attack activity
- **Attack Distribution** — breakdown by attack type
- **Advanced Analytics** — Spark SQL, window functions, joins, UDF
- **Benchmarks** — Spark vs Pandas processing time
""")
