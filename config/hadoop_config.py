"""
Hadoop / HDFS connection settings used by the Python hdfs client.
"""

HDFS_HOST    = "localhost"
HDFS_PORT    = 19000          # custom port (9000 in use by Jupyter on this machine)
HDFS_WEB_URL = f"http://localhost:9870"   # NameNode Web UI

HDFS_BASE_DIR    = "/cybersecurity"
HDFS_RAW_DIR     = f"{HDFS_BASE_DIR}/raw"
HDFS_PROC_DIR    = f"{HDFS_BASE_DIR}/processed"
HDFS_RESULTS_DIR = f"{HDFS_BASE_DIR}/results"

NAMENODE_URI     = f"hdfs://{HDFS_HOST}:{HDFS_PORT}"
