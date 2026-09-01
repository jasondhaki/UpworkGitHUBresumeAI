"""SQLite, not PostgreSQL (Section 7's stated primary) -- a deliberate
substitution for this demo's scale: single hardcoded user, no concurrent
writers, no vector search performed against stored data yet. Zero-config and
free, matching "everything free tier." Swap for real Postgres if this needs
to survive concurrent users or vector search over stored claims later --
the repository.py functions are the seam to swap behind, not the callers.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/app.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_runs (
            run_id TEXT PRIMARY KEY,
            freelancer_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            result_json TEXT NOT NULL,
            claims_json TEXT NOT NULL
        )
        """
    )
    return conn
