"""
Spark session configuration for the Cybersecurity Analytics Platform.
Connects Spark to local HDFS (port 19000).
"""

from pyspark.sql import SparkSession
import os

# ── Paths ──────────────────────────────────────────────────────────
HDFS_NAMENODE   = "hdfs://localhost:19000"
HDFS_RAW        = f"{HDFS_NAMENODE}/cybersecurity/raw"
HDFS_PROCESSED  = f"{HDFS_NAMENODE}/cybersecurity/processed"
HDFS_RESULTS    = f"{HDFS_NAMENODE}/cybersecurity/results"

HADOOP_CONF_DIR = "/opt/homebrew/opt/hadoop/libexec/etc/hadoop"


def get_spark_session(app_name: str = "CybersecurityAnalytics") -> SparkSession:
    """
    Create and return a configured SparkSession.
    Hadoop config dir is injected so Spark can talk to HDFS.
    """
    os.environ["HADOOP_CONF_DIR"] = HADOOP_CONF_DIR
    os.environ["JAVA_HOME"] = (
        "/opt/homebrew/Cellar/openjdk@17/17.0.19"
        "/libexec/openjdk.jdk/Contents/Home"
    )

    spark = (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")                         # use all CPU cores
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "2g")
        .config(
            "spark.hadoop.fs.defaultFS",
            HDFS_NAMENODE
        )
        # Suppress verbose INFO logs in the console
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")
    return spark
