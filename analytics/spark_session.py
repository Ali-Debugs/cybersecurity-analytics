"""
spark_session.py
────────────────
Centralised SparkSession factory.
Every analytics module imports get_spark() from here.
"""

import os
from pyspark.sql import SparkSession

os.environ["JAVA_HOME"] = (
    "/opt/homebrew/Cellar/openjdk@17/17.0.19"
    "/libexec/openjdk.jdk/Contents/Home"
)
os.environ["HADOOP_CONF_DIR"] = (
    "/opt/homebrew/opt/hadoop/libexec/etc/hadoop"
)


def get_spark(app_name: str = "CybersecurityAnalytics") -> SparkSession:
    """
    Return a SparkSession configured to use:
      • All local CPU cores  (master = local[*])
      • HDFS on localhost:19000
      • 2 GB driver + executor memory
    """
    spark = (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "2g")
        .config("spark.hadoop.fs.defaultFS", "hdfs://localhost:19000")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.sql.adaptive.enabled", "true")    # AQE for speed
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark
