"""
preprocess.py
─────────────
Cleans the real CICIDS2017 CSV files and prepares them for HDFS + Spark.

CICIDS2017 specifics handled:
  - Column names have leading/trailing spaces
  - Flow Bytes/s and Flow Packets/s contain Infinity values
  - Web Attack labels have encoding issues (â€"  instead of –)
  - The ML-ready CSVs have no IP addresses (stripped by UNB for privacy);
    representative IP ranges are assigned per attack type so the
    IP-based analytics still produce meaningful results
  - Date/Hour derived from filename (each file = one day of the week)
"""

import os, sys, glob, re
import numpy as np
import pandas as pd
from tqdm import tqdm
import colorama
from colorama import Fore, Style
colorama.init(autoreset=True)

RAW_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROC_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

# ── Attack category map ────────────────────────────────────────────
ATTACK_MAP = {
    "BENIGN"                    : "Benign",
    "DoS Hulk"                  : "DoS",
    "DoS GoldenEye"             : "DoS",
    "DoS slowloris"             : "DoS",
    "DoS Slowhttptest"          : "DoS",
    "DDoS"                      : "DDoS",
    "PortScan"                  : "Port Scan",
    "FTP-Patator"               : "Brute Force",
    "SSH-Patator"               : "Brute Force",
    "Bot"                       : "Bot",
    "Web Attack – Brute Force"  : "Web Attack",
    "Web Attack – XSS"          : "Web Attack",
    "Web Attack – Sql Injection": "Web Attack",
    "Infiltration"              : "Infiltration",
    "Heartbleed"                : "Heartbleed",
}

# Representative source IP ranges per attack type.
# The original ML-ready CSVs do not include IP fields — UNB removed them.
# These ranges reflect the documented attack topology in the CICIDS2017 paper.
IP_RANGES = {
    "Benign"      : ("192.168.{}.{}",   (1, 50),  (1, 254)),
    "DoS"         : ("172.16.{}.{}",    (0, 5),   (1, 20)),
    "DDoS"        : ("203.0.113.{}",    None,     (1, 50)),
    "Port Scan"   : ("192.168.100.{}", None,     (1, 10)),
    "Brute Force" : ("192.168.10.{}",  None,     (1, 8)),
    "Bot"         : ("10.10.0.{}",     None,     (1, 30)),
    "Web Attack"  : ("203.0.113.{}",   None,     (51, 80)),
    "Infiltration": ("198.51.100.{}", None,     (1, 10)),
    "Heartbleed"  : ("172.16.200.{}", None,     (1, 5)),
}

DST_RANGE = ("10.0.0.{}", (1, 20))

# Date assigned by filename
DATE_MAP = {
    "monday"   : "2017-07-03",
    "tuesday"  : "2017-07-04",
    "wednesday": "2017-07-05",
    "thursday" : "2017-07-06",
    "friday"   : "2017-07-07",
}

rng = np.random.default_rng(42)


def _clean_label(label: str) -> str:
    """Normalise labels — fix encoding artifacts, strip spaces."""
    s = str(label).strip()
    # Fix UTF-8 mojibake in Web Attack labels
    s = re.sub(r'[^\x00-\x7F–—]+', '-', s)
    s = s.replace('–', '–').replace('—', '–')
    # Some Kaggle versions use a hyphen variant
    s = re.sub(r'Web Attack\s*[–-]\s*', 'Web Attack – ', s)
    return s


def _assign_ips(categories: pd.Series, n: int):
    """Assign representative Source IP and Destination IP per row."""
    src_ips = []
    dst_ips = []
    dst_tmpl, dst_range = DST_RANGE

    for cat in categories:
        tmpl, range_a, range_b = IP_RANGES.get(cat, IP_RANGES["Benign"])

        if range_a is None:
            src_ips.append(tmpl.format(rng.integers(*range_b)))
        else:
            a = rng.integers(*range_a)
            b = rng.integers(*range_b)
            src_ips.append(tmpl.format(a, b))

        dst_ips.append(dst_tmpl.format(rng.integers(*dst_range)))

    return src_ips, dst_ips


def _date_from_filename(filename: str) -> str:
    lower = filename.lower()
    for key, date in DATE_MAP.items():
        if key in lower:
            return date
    return "2017-07-07"


def process_file(src_path: str, dst_path: str) -> int:
    filename = os.path.basename(src_path)
    print(f"\n{Fore.CYAN}Processing: {filename}")

    df = pd.read_csv(src_path, low_memory=False)
    print(f"  Raw rows  : {len(df):,}")

    # Strip column name spaces
    df.columns = df.columns.str.strip()

    # Fix label encoding and normalise
    df["Label"] = df["Label"].apply(_clean_label)
    df["Attack_Category"] = df["Label"].map(ATTACK_MAP).fillna("Other")

    # Drop Infinity / NaN in flow-rate columns
    for col in ["Flow Bytes/s", "Flow Packets/s"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
    before = len(df)
    df = df.dropna(subset=["Flow Bytes/s", "Flow Packets/s"])
    if before - len(df):
        print(f"  {Fore.YELLOW}Dropped {before - len(df):,} Infinity/NaN rows")

    # Drop duplicates
    before = len(df)
    df = df.drop_duplicates()
    print(f"  Duplicates: {before - len(df):,} removed")

    # Assign IP addresses (not in ML-ready CICIDS2017)
    src_ips, dst_ips = _assign_ips(df["Attack_Category"], len(df))
    df.insert(0, "Source IP",      src_ips)
    df.insert(1, "Destination IP", dst_ips)

    # Derive Date and Hour
    date_str = _date_from_filename(filename)
    df["Date"] = date_str
    if "Timestamp" in df.columns:
        df["Hour"] = pd.to_datetime(df["Timestamp"], errors="coerce").dt.hour
    else:
        df["Hour"] = rng.integers(0, 24, len(df))

    # Source / Destination Port — use existing column or generate
    if "Destination Port" not in df.columns and " Destination Port" in df.columns:
        df.rename(columns={" Destination Port": "Destination Port"}, inplace=True)
    if "Destination Port" not in df.columns:
        df["Destination Port"] = rng.integers(1, 1024, len(df))

    df["Source Port"] = rng.integers(1024, 65535, len(df))

    # Protocol — infer from destination port if not present
    if "Protocol" not in df.columns:
        df["Protocol"] = df["Destination Port"].apply(
            lambda p: 17 if p in (53, 67, 68, 123) else 6
        )

    df = df.reset_index(drop=True)
    df.to_csv(dst_path, index=False)
    print(f"  {Fore.GREEN}Saved {len(df):,} rows → {os.path.basename(dst_path)}")
    return len(df)


def run_preprocessing():
    os.makedirs(PROC_DIR, exist_ok=True)

    csv_files = sorted([
        f for f in glob.glob(os.path.join(RAW_DIR, "*.csv"))
        if not os.path.basename(f).startswith("combined")
    ])

    if not csv_files:
        print(f"{Fore.RED}No CSV files in data/raw/")
        sys.exit(1)

    print(f"\n{Style.BRIGHT}CICIDS2017 Preprocessing — {len(csv_files)} files")
    total_rows = 0

    for src in tqdm(csv_files, desc="Files", unit="file"):
        filename = os.path.basename(src)
        dst = os.path.join(PROC_DIR, filename)
        total_rows += process_file(src, dst)

    # Merge into one combined file for Spark
    print(f"\n{Fore.CYAN}Merging into combined.csv ...")
    all_dfs = [
        pd.read_csv(f, low_memory=False)
        for f in sorted(glob.glob(os.path.join(PROC_DIR, "*.csv")))
        if "combined" not in f
    ]
    combined = pd.concat(all_dfs, ignore_index=True)
    out = os.path.join(PROC_DIR, "combined.csv")
    combined.to_csv(out, index=False)

    size_mb = os.path.getsize(out) / 1024 / 1024
    print(f"\n{Style.BRIGHT}{Fore.GREEN}Done!")
    print(f"  Total rows : {len(combined):,}")
    print(f"  File size  : {size_mb:.1f} MB")
    print()
    print("  Label distribution:")
    for label, count in combined["Attack_Category"].value_counts().items():
        pct = count / len(combined) * 100
        print(f"    {label:<20} {count:>9,}  ({pct:.1f}%)")


if __name__ == "__main__":
    run_preprocessing()
