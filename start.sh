#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# start.sh  —  One-command startup for the entire platform
# Usage: bash start.sh
# ─────────────────────────────────────────────────────────────────

set -e
PROJ_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Environment ──────────────────────────────────────────────────
export JAVA_HOME=/opt/homebrew/Cellar/openjdk@17/17.0.19/libexec/openjdk.jdk/Contents/Home
export HADOOP_HOME=/opt/homebrew/opt/hadoop/libexec
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export SPARK_HOME=/opt/homebrew/opt/apache-spark/libexec
export PATH=$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$SPARK_HOME/bin:$PATH
export PYSPARK_PYTHON=$PROJ_DIR/venv/bin/python3

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Cybersecurity Analytics Platform — Startup            ║"
echo "╚══════════════════════════════════════════════════════════╝"

# ── Step 1: Start HDFS ────────────────────────────────────────────
echo ""
echo "▶ Starting Hadoop HDFS..."
if ! jps 2>/dev/null | grep -q NameNode; then
    start-dfs.sh 2>&1 | grep -v WARN
    sleep 4
    echo "  ✅ HDFS started"
else
    echo "  ✅ HDFS already running"
fi

# Ensure directories exist
hdfs dfs -mkdir -p /cybersecurity/raw /cybersecurity/processed /cybersecurity/results 2>/dev/null || true

echo ""
jps | grep -E "NameNode|DataNode|SecondaryNameNode"

# ── Step 2: Activate venv ─────────────────────────────────────────
echo ""
echo "▶ Activating Python 3.12 virtual environment..."
source "$PROJ_DIR/venv/bin/activate"
echo "  ✅ venv active: $(python --version)"

# ── Step 3: Check dataset ─────────────────────────────────────────
echo ""
PROCESSED="$PROJ_DIR/data/processed/combined.csv"
if [ ! -f "$PROCESSED" ]; then
    echo "⚠️  No processed dataset found."
    echo "   Download dataset:   python ingestion/download_dataset.py --small-only"
    echo "   Then preprocess:    python ingestion/preprocess.py"
    echo "   Then upload:        python ingestion/hdfs_upload.py"
    echo ""
    echo "   Dashboard will show sample/demo data until real data is loaded."
fi

# ── Step 4: Launch Dashboard ──────────────────────────────────────
echo ""
echo "▶ Launching Streamlit dashboard..."
echo "  URL: http://localhost:8501"
echo ""
cd "$PROJ_DIR"
streamlit run dashboard/app.py
