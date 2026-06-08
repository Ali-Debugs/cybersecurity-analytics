"""
hdfs_upload.py
──────────────
Uploads processed CSV files from data/processed/ to HDFS using
the hdfs Python client (WebHDFS REST API on port 9870).

Usage:
    python ingestion/hdfs_upload.py
"""

import os
import glob
import sys
import time
import hdfs
import colorama
from colorama import Fore, Style
from tqdm import tqdm

colorama.init(autoreset=True)

# ── Config ─────────────────────────────────────────────────────────
WEBHDFS_URL  = "http://localhost:9870"
HDFS_DEST    = "/cybersecurity/processed"
LOCAL_SRC    = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed"
)


def get_hdfs_client() -> hdfs.InsecureClient:
    """Create and return an HDFS client (WebHDFS, no auth)."""
    try:
        client = hdfs.InsecureClient(WEBHDFS_URL, user="ali")
        # Quick connectivity check
        client.list("/")
        print(f"{Fore.GREEN}✓ Connected to HDFS at {WEBHDFS_URL}")
        return client
    except Exception as e:
        print(f"{Fore.RED}✗ Cannot connect to HDFS: {e}")
        print("  Make sure HDFS is running: start-dfs.sh")
        sys.exit(1)


def ensure_hdfs_dirs(client: hdfs.InsecureClient):
    """Create destination directories if they don't exist."""
    for path in ["/cybersecurity", "/cybersecurity/raw",
                 "/cybersecurity/processed", "/cybersecurity/results"]:
        try:
            client.makedirs(path)
        except hdfs.util.HdfsError:
            pass  # Already exists — that's fine


def upload_file(client: hdfs.InsecureClient, local_path: str,
                hdfs_path: str) -> float:
    """
    Upload one file to HDFS.
    Returns upload speed in MB/s.
    """
    size_bytes = os.path.getsize(local_path)
    size_mb    = size_bytes / (1024 * 1024)

    start = time.time()
    client.upload(hdfs_path, local_path, overwrite=True)
    elapsed = time.time() - start

    speed = size_mb / elapsed if elapsed > 0 else 0
    return speed


def run_upload():
    print(f"\n{Style.BRIGHT}HDFS Upload Module — Cybersecurity Analytics")
    print("=" * 55)

    client = get_hdfs_client()
    ensure_hdfs_dirs(client)

    csv_files = sorted(glob.glob(os.path.join(LOCAL_SRC, "*.csv")))
    if not csv_files:
        print(f"{Fore.RED}No CSV files in data/processed/")
        print("Run preprocessing first: python ingestion/preprocess.py")
        sys.exit(1)

    print(f"\nUploading {len(csv_files)} file(s) to {HDFS_DEST}")

    total_size = sum(os.path.getsize(f) for f in csv_files)
    print(f"Total size: {total_size / (1024*1024):.1f} MB\n")

    results = []
    for local_path in tqdm(csv_files, desc="Uploading to HDFS", unit="file"):
        filename  = os.path.basename(local_path)
        hdfs_path = f"{HDFS_DEST}/{filename}"

        try:
            speed = upload_file(client, local_path, hdfs_path)
            size_mb = os.path.getsize(local_path) / (1024 * 1024)
            results.append((filename, size_mb, speed, "✓"))
            print(f"  {Fore.GREEN}✓ {filename} ({size_mb:.1f} MB, {speed:.1f} MB/s)")
        except Exception as e:
            results.append((filename, 0, 0, f"✗ {e}"))
            print(f"  {Fore.RED}✗ {filename}: {e}")

    # List uploaded files
    print(f"\n{Fore.CYAN}Files now in HDFS {HDFS_DEST}:")
    try:
        for f in client.list(HDFS_DEST):
            status = client.status(f"{HDFS_DEST}/{f}")
            size   = status["length"] / (1024 * 1024)
            print(f"  {f:45s} {size:7.1f} MB")
    except Exception as e:
        print(f"  {Fore.YELLOW}Could not list: {e}")

    print(f"\n{Style.BRIGHT}{Fore.GREEN}Upload complete!")


if __name__ == "__main__":
    run_upload()
