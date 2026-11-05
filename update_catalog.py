#!/usr/bin/env python3
"""
TMDB Movie Catalog Downloader and Indexer

Fetches the latest official movie export from The Movie Database (TMDB)
and builds an indexed SQLite database with B-Trees and FTS5 full-text search.
"""

import sys
import os
import gzip
import json
import sqlite3
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

EXPORT_BASE_URL = "http://files.tmdb.org/p/exports"
DB_FILE = os.path.join(os.path.dirname(__file__), "movies.db")
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def find_latest_export_url() -> Tuple[str, str]:
    """Finds the most recent available TMDB movie export URL."""
    now = datetime.now(timezone.utc)
    for days_ago in range(5):
        date_obj = now - timedelta(days=days_ago)
        date_str = date_obj.strftime("%m_%d_%Y")
        url = f"{EXPORT_BASE_URL}/movie_ids_{date_str}.json.gz"
        
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "TMDB-Catalog-Bot/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    return url, date_str
        except Exception:
            continue
            
    raise RuntimeError("Could not find a valid TMDB export file within the last 5 days.")


def download_and_index(db_path: str = DB_FILE, save_raw: bool = True):
    url, date_str = find_latest_export_url()
    print(f"[*] Found latest TMDB export: {url} (Date: {date_str})")

    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    raw_file_path = os.path.join(RAW_DATA_DIR, f"movie_ids_{date_str}.json.gz")
    latest_symlink = os.path.join(RAW_DATA_DIR, "movie_ids_latest.json.gz")

    if not os.path.exists(raw_file_path):
        print(f"[*] Downloading to {raw_file_path}...")
        urllib.request.urlretrieve(url, raw_file_path)
        print(f"[+] Download complete ({os.path.getsize(raw_file_path) / (1024*1024):.2f} MB)")
    else:
        print(f"[*] Using existing export cache: {raw_file_path}")

    # Update symlink
    if os.path.lexists(latest_symlink):
        os.remove(latest_symlink)
    os.symlink(os.path.basename(raw_file_path), latest_symlink)

    print(f"[*] Building indexed database at {db_path}...")
    temp_db = db_path + ".tmp"
    if os.path.exists(temp_db):
        os.remove(temp_db)

    conn = sqlite3.connect(temp_db)
    cur = conn.cursor()

    # Optimize SQLite for fast bulk load
    cur.execute("PRAGMA synchronous = OFF;")
    cur.execute("PRAGMA journal_mode = OFF;")
    cur.execute("PRAGMA cache_size = 200000;")
    cur.execute("PRAGMA temp_store = MEMORY;")

    cur.execute("""
        CREATE TABLE movies (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            popularity REAL DEFAULT 0.0,
            adult INTEGER DEFAULT 0
        );
    """)

    batch = []
    batch_size = 50000
    total_count = 0

    print("[*] Parsing movie records and inserting...")
    with gzip.open(raw_file_path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                movie_id = item.get("id")
                title = item.get("original_title", "")
                popularity = item.get("popularity", 0.0)
                adult = 1 if item.get("adult") else 0
                if movie_id is not None and title:
                    batch.append((movie_id, title, popularity, adult))
                    total_count += 1
            except Exception:
                continue

            if len(batch) >= batch_size:
                cur.executemany(
                    "INSERT OR REPLACE INTO movies (id, title, popularity, adult) VALUES (?, ?, ?, ?)",
                    batch
                )
                batch.clear()
                print(f"    Processed {total_count:,} movies...", end="\r", flush=True)

        if batch:
            cur.executemany(
                "INSERT OR REPLACE INTO movies (id, title, popularity, adult) VALUES (?, ?, ?, ?)",
                batch
            )
            batch.clear()

    print(f"\n[+] Inserted {total_count:,} movies into catalog.")

    # Build indexes
    print("[*] Building title case-insensitive index...")
    cur.execute("CREATE INDEX idx_movies_title ON movies (title COLLATE NOCASE);")

    print("[*] Building popularity index...")
    cur.execute("CREATE INDEX idx_movies_popularity ON movies (popularity DESC);")

    print("[*] Building Full-Text Search index (FTS5)...")
    cur.execute("""
        CREATE VIRTUAL TABLE movies_fts USING fts5(
            id UNINDEXED,
            title,
            content='movies',
            content_rowid='id'
        );
    """)
    cur.execute("INSERT INTO movies_fts(movies_fts) VALUES('rebuild');")

    conn.commit()
    conn.close()

    # Move temp_db to destination
    if os.path.exists(db_path):
        os.remove(db_path)
    os.rename(temp_db, db_path)

    print(f"[+] Catalog successfully created: {db_path} ({os.path.getsize(db_path) / (1024*1024):.2f} MB)")
    print(f"[+] Total records indexed: {total_count:,}")


if __name__ == "__main__":
    download_and_index()
