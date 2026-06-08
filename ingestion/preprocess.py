"""
preprocess.py
─────────────
Cleans and normalises the raw CICIDS2017 CSV files so they are
ready to be loaded into HDFS and processed by Spark.

CICIDS2017 quirks handled here:
  • Column names have leading/trailing spaces
  • Some rows have 'Infinity' or 'inf' in numeric columns
  • Some rows are missing the Label column
  • Duplicate rows exist in some files
"""

import os
import sys
import glob
import pandas as pd
from tqdm import tqdm
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

# ── Paths ──────────────────────────────────────────────────────────
RAW_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROC_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

# Columns to keep (subset that matters for security analytics)
COLUMNS_KEEP = [
    "Flow ID", "Source IP", "Destination IP", "Source Port",
    "Destination Port", "Protocol", "Timestamp",
    "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
    "Total Length of Fwd Packets", "Total Length of Bwd Packets",
    "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean",
    "Fwd PSH Flags", "Bwd PSH Flags", "Fwd URG Flags", "Bwd URG Flags",
    "FIN Flag Count", "SYN Flag Count", "RST Flag Count",
    "PSH Flag Count", "ACK Flag Count", "URG Flag Count",
    "Label"
]

ATTACK_MAP = {
    "BENIGN"              : "Benign",
    "DoS Hulk"            : "DoS",
    "PortScan"            : "Port Scan",
    "DDoS"                : "DDoS",
    "DoS GoldenEye"       : "DoS",
    "FTP-Patator"         : "Brute Force",
    "SSH-Patator"         : "Brute Force",
    "DoS slowloris"       : "DoS",
    "DoS Slowhttptest"    : "DoS",
    "Bot"                 : "Bot",
    "Web Attack – Brute Force": "Web Attack",
    "Web Attack – XSS"    : "Web Attack",
    "Web Attack – Sql Injection": "Web Attack",
    "Infiltration"        : "Infiltration",
    "Heartbleed"          : "Heartbleed",
}


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from column names (common CICIDS2017 issue)."""
    df.columns = df.columns.str.strip()
    return df


def filter_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the columns we care about; ignore missing ones."""
    existing = [c for c in COLUMNS_KEEP if c in df.columns]
    return df[existing]


def fix_numeric_infinities(df: pd.DataFrame) -> pd.DataFrame:
    """Replace Inf / -Inf with NaN then drop those rows."""
    import numpy as np
    df = df.replace([float("inf"), float("-inf")], float("nan"))
    before = len(df)
    df = df.dropna(subset=["Flow Bytes/s", "Flow Packets/s"], how="any")
    dropped = before - len(df)
    if dropped:
        print(f"  {Fore.YELLOW}Dropped {dropped} rows with Infinity values")
    return df


def normalise_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Map raw CICIDS2017 labels to clean category names."""
    if "Label" not in df.columns:
        return df
    df["Label"] = df["Label"].str.strip()
    df["Attack_Category"] = df["Label"].map(ATTACK_MAP).fillna("Other")
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add columns useful for analytics."""
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df["Hour"]  = df["Timestamp"].dt.hour
        df["Date"]  = df["Timestamp"].dt.date.astype(str)
    return df


def process_file(src_path: str, dst_path: str) -> int:
    """
    Clean one CSV file and write result to dst_path.
    Returns number of rows saved.
    """
    print(f"\n{Fore.CYAN}Processing: {os.path.basename(src_path)}")

    df = pd.read_csv(src_path, low_memory=False)
    print(f"  Raw rows: {len(df):,}")

    df = clean_column_names(df)
    df = filter_columns(df)
    df = fix_numeric_infinities(df)
    df = normalise_labels(df)
    df = add_derived_columns(df)

    # Drop duplicates
    before = len(df)
    df = df.drop_duplicates()
    print(f"  Duplicates removed: {before - len(df):,}")

    # Reset index
    df = df.reset_index(drop=True)

    df.to_csv(dst_path, index=False)
    print(f"  {Fore.GREEN}Saved {len(df):,} rows → {os.path.basename(dst_path)}")
    return len(df)


def run_preprocessing():
    os.makedirs(PROC_DIR, exist_ok=True)

    csv_files = sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
    if not csv_files:
        print(f"{Fore.RED}No CSV files found in {RAW_DIR}")
        print("Please download CICIDS2017 and place CSVs in data/raw/")
        sys.exit(1)

    print(f"\n{Style.BRIGHT}Found {len(csv_files)} file(s) to process")
    total_rows = 0

    for src in tqdm(csv_files, desc="Preprocessing", unit="file"):
        filename = os.path.basename(src)
        dst = os.path.join(PROC_DIR, filename)
        total_rows += process_file(src, dst)

    # Also create a merged file for easier Spark loading
    print(f"\n{Fore.CYAN}Merging all files into combined.csv ...")
    all_dfs = []
    for f in glob.glob(os.path.join(PROC_DIR, "*.csv")):
        if "combined" not in f:
            all_dfs.append(pd.read_csv(f, low_memory=False))

    combined = pd.concat(all_dfs, ignore_index=True)
    combined_path = os.path.join(PROC_DIR, "combined.csv")
    combined.to_csv(combined_path, index=False)
    print(f"{Fore.GREEN}Combined file: {len(combined):,} total rows → combined.csv")

    print(f"\n{Style.BRIGHT}{Fore.GREEN}Preprocessing complete! Total rows: {total_rows:,}")


if __name__ == "__main__":
    run_preprocessing()
