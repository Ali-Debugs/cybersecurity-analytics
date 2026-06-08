"""
generate_sample_data.py
────────────────────────
Generates a realistic synthetic CICIDS2017-format dataset.

Use this when:
  1. You cannot yet access the real dataset (UNB requires registration)
  2. You want a small dataset for fast testing / viva demonstration

The generated data matches CICIDS2017's column structure, attack
type proportions, and value ranges so all analytics modules work.

Real dataset download (Kaggle — no registration wall):
  https://www.kaggle.com/datasets/cicdataset/cicids2017

Usage:
    python ingestion/generate_sample_data.py
    python ingestion/generate_sample_data.py --rows 500000
"""

import os
import argparse
import numpy as np
import pandas as pd
from tqdm import tqdm
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

RAW_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROC_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

# ── Attack type configuration ──────────────────────────────────────
ATTACK_CONFIGS = {
    "BENIGN": {
        "weight"         : 0.55,
        "src_ips"        : ["192.168.1.{}".format(i) for i in range(1, 50)],
        "dst_ips"        : ["10.0.0.{}".format(i) for i in range(1, 30)],
        "ports"          : [80, 443, 8080, 3306, 5432, 22, 21, 25, 53],
        "protocols"      : [6, 17, 6, 6, 17],
        "bytes_range"    : (100, 5000),
        "packets_range"  : (2, 50),
        "duration_range" : (100, 50000),
        "syn_flags"      : (0, 2),
    },
    "DoS Hulk": {
        "weight"         : 0.12,
        "src_ips"        : ["172.16.0.{}".format(i) for i in range(1, 10)],
        "dst_ips"        : ["10.0.0.{}".format(i) for i in range(1, 5)],
        "ports"          : [80, 443],
        "protocols"      : [6],
        "bytes_range"    : (5000, 50000),
        "packets_range"  : (50, 500),
        "duration_range" : (10, 1000),
        "syn_flags"      : (0, 1),
    },
    "PortScan": {
        "weight"         : 0.10,
        "src_ips"        : ["192.168.100.{}".format(i) for i in range(1, 6)],
        "dst_ips"        : ["10.0.0.{}".format(i) for i in range(1, 50)],
        "ports"          : list(range(1, 1024, 10)),
        "protocols"      : [6],
        "bytes_range"    : (40, 200),
        "packets_range"  : (1, 3),
        "duration_range" : (1, 100),
        "syn_flags"      : (1, 3),
    },
    "DDoS": {
        "weight"         : 0.08,
        "src_ips"        : ["203.0.113.{}".format(i) for i in range(1, 30)],
        "dst_ips"        : ["10.0.0.1"],
        "ports"          : [80, 443],
        "protocols"      : [6, 17],
        "bytes_range"    : (10000, 100000),
        "packets_range"  : (100, 1000),
        "duration_range" : (1, 500),
        "syn_flags"      : (2, 8),
    },
    "FTP-Patator": {
        "weight"         : 0.04,
        "src_ips"        : ["192.168.10.{}".format(i) for i in range(1, 5)],
        "dst_ips"        : ["10.0.0.5"],
        "ports"          : [21],
        "protocols"      : [6],
        "bytes_range"    : (200, 1000),
        "packets_range"  : (5, 20),
        "duration_range" : (1000, 30000),
        "syn_flags"      : (1, 2),
    },
    "SSH-Patator": {
        "weight"         : 0.04,
        "src_ips"        : ["192.168.10.{}".format(i) for i in range(1, 5)],
        "dst_ips"        : ["10.0.0.5"],
        "ports"          : [22],
        "protocols"      : [6],
        "bytes_range"    : (300, 1500),
        "packets_range"  : (5, 25),
        "duration_range" : (2000, 40000),
        "syn_flags"      : (1, 2),
    },
    "DoS GoldenEye": {
        "weight"         : 0.04,
        "src_ips"        : ["198.51.100.{}".format(i) for i in range(1, 8)],
        "dst_ips"        : ["10.0.0.1", "10.0.0.2"],
        "ports"          : [80, 443],
        "protocols"      : [6],
        "bytes_range"    : (3000, 30000),
        "packets_range"  : (30, 300),
        "duration_range" : (100, 5000),
        "syn_flags"      : (0, 2),
    },
    "Bot": {
        "weight"         : 0.03,
        "src_ips"        : ["10.10.0.{}".format(i) for i in range(1, 20)],
        "dst_ips"        : ["8.8.8.8", "1.1.1.1", "208.67.222.222"],
        "ports"          : [80, 443, 6667, 8080],
        "protocols"      : [6, 17],
        "bytes_range"    : (500, 5000),
        "packets_range"  : (10, 100),
        "duration_range" : (500, 20000),
        "syn_flags"      : (0, 1),
    },
}

ATTACK_CATEGORY_MAP = {
    "BENIGN"        : "Benign",
    "DoS Hulk"      : "DoS",
    "DoS GoldenEye" : "DoS",
    "PortScan"      : "Port Scan",
    "DDoS"          : "DDoS",
    "FTP-Patator"   : "Brute Force",
    "SSH-Patator"   : "Brute Force",
    "Bot"           : "Bot",
}

rng = np.random.default_rng(42)


def generate_rows(label: str, config: dict, n: int) -> pd.DataFrame:
    src_ips  = rng.choice(config["src_ips"],  n)
    dst_ips  = rng.choice(config["dst_ips"],  n)
    ports    = rng.choice(config["ports"],    n)
    protos   = rng.choice(config["protocols"],n)
    hours    = rng.integers(0, 24, n)

    bytes_ps = rng.uniform(*config["bytes_range"],   n).round(2)
    pkts_ps  = rng.uniform(*config["packets_range"], n).round(2)
    duration = rng.integers(*config["duration_range"], n)
    syn_f    = rng.integers(*config["syn_flags"],   n)

    fwd_pkts = rng.integers(1, int(config["packets_range"][1]/2) + 2, n)
    bwd_pkts = rng.integers(0, int(config["packets_range"][1]/2) + 1, n)

    dates = rng.choice(
        ["2017-07-07","2017-07-11","2017-07-12","2017-07-13","2017-07-14"], n
    )
    timestamps = [
        f"{d} {h:02d}:{rng.integers(0,60):02d}:{rng.integers(0,60):02d}"
        for d, h in zip(dates, hours)
    ]

    return pd.DataFrame({
        "Flow ID"                        : [f"flow_{i}" for i in range(n)],
        "Source IP"                      : src_ips,
        "Destination IP"                 : dst_ips,
        "Source Port"                    : rng.integers(1024, 65535, n),
        "Destination Port"               : ports,
        "Protocol"                       : protos,
        "Timestamp"                      : timestamps,
        "Flow Duration"                  : duration,
        "Total Fwd Packets"              : fwd_pkts,
        "Total Backward Packets"         : bwd_pkts,
        "Total Length of Fwd Packets"    : (fwd_pkts * rng.integers(50,200,n)),
        "Total Length of Bwd Packets"    : (bwd_pkts * rng.integers(50,200,n)),
        "Flow Bytes/s"                   : bytes_ps,
        "Flow Packets/s"                 : pkts_ps,
        "Flow IAT Mean"                  : rng.uniform(10, 10000, n).round(2),
        "Fwd PSH Flags"                  : rng.integers(0, 2, n),
        "Bwd PSH Flags"                  : rng.integers(0, 2, n),
        "Fwd URG Flags"                  : rng.integers(0, 1, n),
        "Bwd URG Flags"                  : rng.integers(0, 1, n),
        "FIN Flag Count"                 : rng.integers(0, 3, n),
        "SYN Flag Count"                 : syn_f,
        "RST Flag Count"                 : rng.integers(0, 2, n),
        "PSH Flag Count"                 : rng.integers(0, 3, n),
        "ACK Flag Count"                 : rng.integers(0, 5, n),
        "URG Flag Count"                 : rng.integers(0, 1, n),
        "Label"                          : label,
        "Attack_Category"                : ATTACK_CATEGORY_MAP[label],
        "Hour"                           : hours,
        "Date"                           : dates,
    })


def main(total_rows: int = 100_000):
    os.makedirs(RAW_DIR,  exist_ok=True)
    os.makedirs(PROC_DIR, exist_ok=True)

    print(f"\n{Style.BRIGHT}Generating synthetic CICIDS2017-format dataset")
    print(f"  Total rows : {total_rows:,}")
    print(f"  Output     : data/processed/combined.csv")
    print()

    weights = np.array([c["weight"] for c in ATTACK_CONFIGS.values()])
    labels  = list(ATTACK_CONFIGS.keys())
    counts  = (weights / weights.sum() * total_rows).astype(int)
    counts[-1] += total_rows - counts.sum()  # fix rounding

    frames = []
    for label, n in tqdm(zip(labels, counts), total=len(labels),
                         desc="Generating", unit="attack-type"):
        frames.append(generate_rows(label, ATTACK_CONFIGS[label], n))

    df = pd.concat(frames, ignore_index=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # Save to processed (already clean — no preprocessing needed)
    combined_path = os.path.join(PROC_DIR, "combined.csv")
    df.to_csv(combined_path, index=False)

    print(f"\n{Fore.GREEN}{Style.BRIGHT}✅ Done!")
    print(f"  Rows generated: {len(df):,}")
    print(f"  File size     : {os.path.getsize(combined_path) / 1024 / 1024:.1f} MB")
    print()
    print("  Label distribution:")
    dist = df["Attack_Category"].value_counts()
    for label, count in dist.items():
        pct = count / len(df) * 100
        print(f"    {label:<20} {count:>8,}  ({pct:.1f}%)")

    print(f"\n{Fore.CYAN}Next step:")
    print("  python ingestion/hdfs_upload.py")
    return combined_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=100_000,
                        help="Number of synthetic rows (default: 100,000)")
    args = parser.parse_args()
    main(args.rows)
