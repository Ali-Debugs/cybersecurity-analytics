# 🛡️ Distributed Cybersecurity Log Analytics Platform

> **University PDC Project** — Hadoop HDFS + Apache Spark + Streamlit Dashboard

## Architecture

```
CICIDS2017 Dataset
       ↓
Preprocessing (Python / Pandas)
       ↓
Hadoop HDFS 3.5  (distributed storage, pseudo-distributed on localhost:19000)
       ↓
Apache Spark 4.1  (PySpark distributed analytics)
       ├── Attack Distribution Analysis
       ├── Suspicious IP Detection
       ├── Brute Force / Failed Login Analysis
       └── Traffic Pattern Analysis
       ↓
Streamlit Dashboard  (5 pages, Plotly charts)
       ↓
Streamlit Community Cloud  (public deployment)
```

## Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Storage | Apache Hadoop HDFS | 3.5.0 |
| Processing | Apache Spark (PySpark) | 4.1.1 |
| Language | Python | 3.12 |
| Dashboard | Streamlit | 1.35 |
| Visualisation | Plotly | 5.22 |
| Runtime | Java | 17 (LTS) |

## Dataset

**CICIDS2017** — Canadian Institute for Cybersecurity Intrusion Detection Dataset 2017

- **Download:** https://www.unb.ca/cic/datasets/ids-2017.html
- **Size:** ~2.3 GB (8 CSV files across 5 days)
- **Records:** ~2.8 million network flows
- **Labels:** 14 attack types + Benign traffic

### Why CICIDS2017?
- Gold standard academic cybersecurity dataset
- Real network traffic with labelled attacks
- Covers DoS, DDoS, Brute Force, Web Attacks, Infiltration, Port Scans
- Used in 500+ academic papers

## Quick Start

### 1. Prerequisites
```bash
# Verify Java 17
java -version   # should show 17.x

# Verify Hadoop
hadoop version  # should show 3.5.x

# Verify Spark
spark-shell --version  # should show 4.1.x
```

### 2. Start HDFS
```bash
start-dfs.sh
jps   # should show NameNode, DataNode, SecondaryNameNode
```

### 3. Set up Python environment
```bash
cd ~/Projects/cybersecurity-analytics
source venv/bin/activate
# (venv already created with Python 3.12)
```

### 4. Download dataset
Place CICIDS2017 CSV files in `data/raw/`

### 5. Run preprocessing
```bash
python ingestion/preprocess.py
```

### 6. Upload to HDFS
```bash
python ingestion/hdfs_upload.py
```

### 7. Run Spark analytics
```bash
python analytics/run_all_analytics.py
```

### 8. Run benchmarks
```bash
python benchmarking/pandas_baseline.py
python benchmarking/spark_benchmark.py
python benchmarking/compare_results.py
```

### 9. Launch dashboard
```bash
streamlit run dashboard/app.py
# Opens at http://localhost:8501
```

## Project Structure

```
cybersecurity-analytics/
├── config/               # Spark & Hadoop connection settings
├── data/                 # Dataset (not in git — download separately)
├── ingestion/            # Preprocessing + HDFS upload scripts
├── analytics/            # PySpark analytics modules
├── benchmarking/         # Pandas vs Spark performance comparison
├── dashboard/            # Streamlit multi-page dashboard
├── results/              # JSON outputs from Spark jobs
└── docs/                 # Architecture diagrams, screenshots
```

## PDC Concepts Demonstrated

| Concept | Where |
|---------|-------|
| Parallel Processing | Spark `local[*]` — all CPU cores |
| Distributed Storage | HDFS blocks + replication |
| Data Partitioning | Spark RDD/DataFrame partitions |
| Fault Tolerance | HDFS replication + Spark lineage |
| Scalability | `local[*]` → cluster with zero code changes |
| Lazy Evaluation | Spark DAG builds before execution |
| In-Memory Computing | Spark `.cache()` |

## HDFS Directory Structure

```
/cybersecurity/
├── raw/          ← original uploaded CSVs
├── processed/    ← cleaned CSVs (used by Spark)
└── results/      ← Spark output files
```

## Screenshots Required

| # | Screenshot | Command |
|---|-----------|---------|
| 01 | Java verified | `java -version` |
| 02 | Hadoop verified | `hadoop version` |
| 03 | HDFS startup | `jps` |
| 04 | NameNode Web UI | http://localhost:9870 |
| 05 | DataNode running | http://localhost:9870/dfshealth.html#tab-datanode |
| 06 | Dataset in HDFS | `hdfs dfs -ls /cybersecurity/processed` |
| 07 | Spark verified | `spark-shell --version` |
| 08 | Spark reads HDFS | pyspark shell |
| 09 | Analytics output | terminal |
| 10 | Dashboard running | http://localhost:8501 |

## Author

Ali — University PDC Project, 2026
