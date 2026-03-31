#!/usr/bin/env python3
"""
import_data.py - One-time import of company CSV files into SQLite.

Usage:
    python import_data.py
    python import_data.py --data-dir "F:/interview-company-wise-problems-main"
    python import_data.py --db-path "./leetcode.db"
"""

import csv
import os
import sqlite3
import sys
import argparse

PERIOD_MAP = {
    "1. Thirty Days.csv":          "thirty_days",
    "2. Three Months.csv":         "three_months",
    "3. Six Months.csv":           "six_months",
    "4. More Than Six Months.csv": "more_than_six",
    "5. All.csv":                  "all",
}

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS problems (
    slug        TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    difficulty  TEXT NOT NULL,
    link        TEXT NOT NULL,
    acceptance  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS companies (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS topics (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS problem_topics (
    slug     TEXT NOT NULL REFERENCES problems(slug),
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    PRIMARY KEY (slug, topic_id)
);

CREATE TABLE IF NOT EXISTS appearances (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_slug TEXT NOT NULL REFERENCES problems(slug),
    company_id   INTEGER NOT NULL REFERENCES companies(id),
    period       TEXT NOT NULL,
    frequency    REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_app_company   ON appearances(company_id);
CREATE INDEX IF NOT EXISTS idx_app_period    ON appearances(period);
CREATE INDEX IF NOT EXISTS idx_app_comp_per  ON appearances(company_id, period);
CREATE INDEX IF NOT EXISTS idx_app_slug      ON appearances(problem_slug);
CREATE INDEX IF NOT EXISTS idx_prob_diff     ON problems(difficulty);
CREATE INDEX IF NOT EXISTS idx_pt_topic      ON problem_topics(topic_id);
"""


def slug_from_link(link: str) -> str:
    return link.rstrip("/").split("/")[-1]


def import_all(data_dir: str, db_path: str):
    print(f"Data dir : {data_dir}")
    print(f"DB path  : {db_path}")

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)

    companies_seen = 0
    rows_inserted = 0
    skipped = 0

    entries = sorted(os.listdir(data_dir))
    # Skip hidden directories, the browser app directory, and any non-company dirs
    SKIP_DIRS = {"leetcode-browser", ".claude", ".git", "__pycache__"}
    company_dirs = [
        e for e in entries
        if os.path.isdir(os.path.join(data_dir, e))
        and not e.startswith(".")
        and e not in SKIP_DIRS
    ]
    total_companies = len(company_dirs)
    print(f"Found {total_companies} company directories.\n")

    for i, company_name in enumerate(company_dirs):
        company_path = os.path.join(data_dir, company_name)

        # Insert company
        conn.execute(
            "INSERT OR IGNORE INTO companies(name) VALUES (?)", (company_name,)
        )
        row = conn.execute(
            "SELECT id FROM companies WHERE name = ?", (company_name,)
        ).fetchone()
        company_id = row[0]
        companies_seen += 1

        for csv_filename, period_key in PERIOD_MAP.items():
            csv_path = os.path.join(company_path, csv_filename)
            if not os.path.exists(csv_path):
                continue

            try:
                with open(csv_path, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            title = row.get("Title", "").strip()
                            link  = row.get("Link", "").strip()
                            diff  = row.get("Difficulty", "").strip().upper()
                            freq  = float(row.get("Frequency", 0))
                            acc   = float(row.get("Acceptance Rate", 0))
                            tags  = row.get("Topics", "").strip()

                            if not title or not link:
                                skipped += 1
                                continue

                            slug = slug_from_link(link)

                            conn.execute(
                                "INSERT OR IGNORE INTO problems(slug, title, difficulty, link, acceptance)"
                                " VALUES (?, ?, ?, ?, ?)",
                                (slug, title, diff, link, acc),
                            )

                            for tag in tags.split(","):
                                tag = tag.strip()
                                if not tag:
                                    continue
                                conn.execute(
                                    "INSERT OR IGNORE INTO topics(name) VALUES (?)", (tag,)
                                )
                                topic_row = conn.execute(
                                    "SELECT id FROM topics WHERE name = ?", (tag,)
                                ).fetchone()
                                conn.execute(
                                    "INSERT OR IGNORE INTO problem_topics(slug, topic_id) VALUES (?, ?)",
                                    (slug, topic_row[0]),
                                )

                            conn.execute(
                                "INSERT INTO appearances(problem_slug, company_id, period, frequency)"
                                " VALUES (?, ?, ?, ?)",
                                (slug, company_id, period_key, freq),
                            )
                            rows_inserted += 1

                        except (ValueError, KeyError) as e:
                            skipped += 1
                            continue
            except Exception as e:
                print(f"  WARNING: could not read {csv_path}: {e}")

        if (i + 1) % 50 == 0 or (i + 1) == total_companies:
            print(f"  Processed {i + 1}/{total_companies} companies...")

    conn.commit()
    conn.close()

    print(f"\nDone.")
    print(f"  Companies : {companies_seen}")
    print(f"  Rows      : {rows_inserted}")
    print(f"  Skipped   : {skipped}")

    # Quick verify
    conn2 = sqlite3.connect(db_path)
    problems_count    = conn2.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
    appearances_count = conn2.execute("SELECT COUNT(*) FROM appearances").fetchone()[0]
    topics_count      = conn2.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
    conn2.close()

    print(f"\nDB summary:")
    print(f"  problems    : {problems_count}")
    print(f"  appearances : {appearances_count}")
    print(f"  topics      : {topics_count}")


def main():
    parser = argparse.ArgumentParser(description="Import LeetCode company CSVs into SQLite.")
    parser.add_argument(
        "--data-dir",
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data")),
        help="Path to the directory containing company folders (default: ../data relative to this script)",
    )
    parser.add_argument(
        "--db-path",
        default=os.path.join(os.path.dirname(__file__), "leetcode.db"),
        help="Output SQLite database path (default: ./leetcode.db)",
    )
    args = parser.parse_args()
    import_all(args.data_dir, args.db_path)


if __name__ == "__main__":
    main()
