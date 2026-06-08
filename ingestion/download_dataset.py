"""
download_dataset.py
────────────────────
Downloads the CICIDS2017 dataset from the University of New Brunswick.

The full dataset is 2.3 GB. This script downloads the MachineLearning
CSV files (already feature-extracted — no raw PCAP needed).

Official source:
  https://www.unb.ca/cic/datasets/ids-2017.html

Direct download base URL (UNB public server):
  http://205.174.165.80/CICDataset/CIC-IDS-2017/Dataset/MachineLearningCVE/

Files to download (8 CSVs, ~2.3 GB total):
  Monday-WorkingHours.pcap_ISCX.csv       ~436 MB  (benign only)
  Tuesday-WorkingHours.pcap_ISCX.csv      ~157 MB  (FTP/SSH Brute Force)
  Wednesday-workingHours.pcap_ISCX.csv    ~603 MB  (DoS, Heartbleed)
  Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv  ~175 MB
  Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv  ~35 MB
  Friday-WorkingHours-Morning.pcap_ISCX.csv   ~200 MB  (Port Scan)
  Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv  ~295 MB
  Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv  ~397 MB

Usage:
    python ingestion/download_dataset.py

    # Download only small files for testing:
    python ingestion/download_dataset.py --small-only
"""

import os
import sys
import time
import argparse
import requests
from tqdm import tqdm
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

BASE_URL = (
    "http://205.174.165.80/CICDataset/CIC-IDS-2017/"
    "Dataset/MachineLearningCVE/"
)

# (filename, size_mb, is_small)
DATASET_FILES = [
    ("Tuesday-WorkingHours.pcap_ISCX.csv",                              157,  True),
    ("Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",      35,  True),
    ("Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",          175, False),
    ("Friday-WorkingHours-Morning.pcap_ISCX.csv",                       200, False),
    ("Wednesday-workingHours.pcap_ISCX.csv",                            603, False),
    ("Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",                295, False),
    ("Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",            397, False),
    ("Monday-WorkingHours.pcap_ISCX.csv",                               436, False),
]

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def download_file(url: str, dest_path: str, filename: str):
    """Stream-download a file with a progress bar."""
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    with open(dest_path, "wb") as f, tqdm(
        desc=f"  {filename[:45]:<45}",
        total=total,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        leave=False,
    ) as bar:
        for chunk in response.iter_content(chunk_size=65536):
            f.write(chunk)
            bar.update(len(chunk))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--small-only", action="store_true",
                        help="Download only the two smallest files (~200 MB total)")
    args = parser.parse_args()

    os.makedirs(RAW_DIR, exist_ok=True)

    files = [f for f in DATASET_FILES if (not args.small_only or f[2])]
    total_mb = sum(f[1] for f in files)

    print(f"\n{Style.BRIGHT}CICIDS2017 Dataset Downloader")
    print("=" * 55)
    print(f"Files to download: {len(files)}")
    print(f"Estimated size:    {total_mb:,} MB ({total_mb/1024:.1f} GB)")
    print(f"Destination:       {RAW_DIR}")
    print()

    if not args.small_only:
        print(f"{Fore.YELLOW}Tip: Use --small-only to download just 2 files "
              f"(~192 MB) for testing.")
        print()

    for filename, size_mb, _ in files:
        dest = os.path.join(RAW_DIR, filename)

        if os.path.exists(dest):
            actual_mb = os.path.getsize(dest) / (1024 * 1024)
            if actual_mb > size_mb * 0.9:
                print(f"  {Fore.GREEN}✓ Already downloaded: {filename}")
                continue

        url = BASE_URL + filename
        print(f"{Fore.CYAN}Downloading: {filename} (~{size_mb} MB)")
        try:
            t0 = time.time()
            download_file(url, dest, filename)
            elapsed = time.time() - t0
            actual_mb = os.path.getsize(dest) / (1024 * 1024)
            speed = actual_mb / elapsed
            print(f"  {Fore.GREEN}✓ Done: {actual_mb:.1f} MB in {elapsed:.0f}s ({speed:.1f} MB/s)")
        except Exception as e:
            print(f"  {Fore.RED}✗ Failed: {e}")
            if os.path.exists(dest):
                os.remove(dest)

    # Summary
    downloaded = [f for f in os.listdir(RAW_DIR) if f.endswith(".csv")]
    print(f"\n{Style.BRIGHT}{Fore.GREEN}Downloaded {len(downloaded)} files to data/raw/")
    print("\nNext step:")
    print("  python ingestion/preprocess.py")


if __name__ == "__main__":
    main()
