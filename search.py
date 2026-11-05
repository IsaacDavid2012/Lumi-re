#!/usr/bin/env python3
"""
CLI search and query utility for the TMDB movie catalog.
"""

import argparse
import os
import sqlite3
import sys

DB_FILE = os.path.join(os.path.dirname(__file__), "movies.db")


def get_connection(db_path: str = DB_FILE) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}. Please run update_catalog.py first.", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def search_by_id(movie_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, popularity, adult FROM movies WHERE id = ?", (movie_id,))
    row = cur.fetchone()
    if row:
        print(f"ID:         {row['id']}")
        print(f"Title:      {row['title']}")
        print(f"Popularity: {row['popularity']}")
        print(f"Adult:      {'Yes' if row['adult'] else 'No'}")
        print(f"TMDB URL:   https://www.themoviedb.org/movie/{row['id']}")
    else:
        print(f"No movie found with ID: {movie_id}")


def search_by_title(query: str, limit: int = 20, exact: bool = False):
    conn = get_connection()
    cur = conn.cursor()

    if exact:
        cur.execute(
            "SELECT id, title, popularity, adult FROM movies WHERE title = ? COLLATE NOCASE ORDER BY popularity DESC LIMIT ?",
            (query, limit)
        )
    else:
        # FTS5 search with fallback to prefix match
        sanitized = "".join(c for c in query if c.isalnum() or c.isspace()).strip()
        fts_query = f'"{sanitized}"*' if sanitized else ""

        try:
            cur.execute("""
                SELECT m.id, m.title, m.popularity, m.adult
                FROM movies_fts f
                JOIN movies m ON m.id = f.rowid
                WHERE movies_fts MATCH ?
                ORDER BY bm25(movies_fts), m.popularity DESC
                LIMIT ?
            """, (fts_query, limit))
        except sqlite3.OperationalError:
            # Fallback to LIKE if syntax issue
            cur.execute(
                "SELECT id, title, popularity, adult FROM movies WHERE title LIKE ? ORDER BY popularity DESC LIMIT ?",
                (f"%{query}%", limit)
            )

    rows = cur.fetchall()
    if not rows:
        print(f"No movies matching '{query}' found.")
        return

    print(f"Found {len(rows)} results (limited to {limit}):\n")
    print(f"{'ID':<10} | {'POPULARITY':<10} | {'TITLE'}")
    print("-" * 60)
    for r in rows:
        print(f"{r['id']:<10} | {r['popularity']:<10.2f} | {r['title']}")


def list_top(limit: int = 20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, popularity FROM movies ORDER BY popularity DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    print(f"Top {limit} most popular movies in TMDB catalog:\n")
    print(f"{'ID':<10} | {'POPULARITY':<10} | {'TITLE'}")
    print("-" * 60)
    for r in rows:
        print(f"{r['id']:<10} | {r['popularity']:<10.2f} | {r['title']}")


def main():
    parser = argparse.ArgumentParser(description="Query the indexed TMDB movie catalog.")
    parser.add_argument("query", nargs="?", help="Title or search keywords")
    parser.add_argument("--id", type=int, help="Look up a movie by its TMDB ID")
    parser.add_argument("--exact", action="store_true", help="Match exact title")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of results to display (default: 20)")
    parser.add_argument("--top", action="store_true", help="Display top movies by popularity")

    args = parser.parse_args()

    if args.id is not None:
        search_by_id(args.id)
    elif args.top:
        list_top(args.limit)
    elif args.query:
        search_by_title(args.query, limit=args.limit, exact=args.exact)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
