"""Consistent SQLite backup, including a live WAL database. Never copies just the .db file."""

import argparse
import os
from pathlib import Path
import sqlite3

parser = argparse.ArgumentParser(
    description="Create a consistent ParcelHub database backup."
)
parser.add_argument(
    "--source", default=str(Path(os.getenv("DATA_DIR", "./data")) / "parcelhub.sqlite3")
)
parser.add_argument(
    "destination", help="A NEW backup .sqlite3 path; existing files are never replaced."
)
args = parser.parse_args()
source = Path(args.source).resolve()
destination = Path(args.destination).resolve()
if not source.is_file():
    parser.error("Source database does not exist.")
if destination.exists() or source == destination:
    parser.error("Destination must be a new file.")
destination.parent.mkdir(parents=True, exist_ok=True)
fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
os.close(fd)
with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as src, sqlite3.connect(
    destination
) as dst:
    src.backup(dst)
    integrity = dst.execute("PRAGMA integrity_check").fetchone()[0]
if integrity != "ok":
    raise RuntimeError("Backup integrity check failed.")
print(f"Backup verified: {destination}")
