"""SQLite persistence (WAL mode) — jobs, evaluations, dispositions, scan runs."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from .config import DATA_DIR
from .models import Job

DB_PATH = DATA_DIR / "radar.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  job_key TEXT PRIMARY KEY,
  content_hash TEXT NOT NULL,
  data TEXT NOT NULL,             -- Job as JSON
  status TEXT NOT NULL DEFAULT 'active',  -- active | possibly_removed
  source TEXT NOT NULL,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  absence_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS evaluations (
  cache_key TEXT PRIMARY KEY,     -- content_hash|prompt_version|prefs_hash|profile_hash
  job_key TEXT NOT NULL,
  dimension_scores TEXT NOT NULL, -- JSON incl. computed posting_freshness
  overall REAL NOT NULL,
  tier TEXT NOT NULL,
  reasons TEXT NOT NULL,
  concerns TEXT NOT NULL,
  confidence TEXT NOT NULL,
  recommendation TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  evaluated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dispositions (
  job_key TEXT PRIMARY KEY,
  status TEXT NOT NULL,           -- saved | dismissed | applied
  reason TEXT,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rejected (
  job_key TEXT PRIMARY KEY,
  filter_reason TEXT NOT NULL,
  data TEXT NOT NULL,
  seen_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scan_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  status TEXT NOT NULL,           -- running | ok | failed
  sources_attempted INTEGER DEFAULT 0,
  sources_succeeded INTEGER DEFAULT 0,
  raw_count INTEGER DEFAULT 0,
  new_count INTEGER DEFAULT 0,
  updated_count INTEGER DEFAULT 0,
  scored_count INTEGER DEFAULT 0,
  errors TEXT DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS locks (
  name TEXT PRIMARY KEY,
  acquired_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_eval_job ON evaluations(job_key);
"""

STALE_LOCK_SECONDS = 3600


def connect(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def acquire_scan_lock(conn) -> bool:
    """Single scan-in-progress lock; stale locks (crashed scans) expire."""
    conn.execute("DELETE FROM locks WHERE name='scan' AND acquired_at < ?",
                 (time.time() - STALE_LOCK_SECONDS,))
    try:
        conn.execute("INSERT INTO locks(name, acquired_at) VALUES('scan', ?)", (time.time(),))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def release_scan_lock(conn) -> None:
    conn.execute("DELETE FROM locks WHERE name='scan'")
    conn.commit()


def scan_in_progress(conn) -> bool:
    row = conn.execute("SELECT acquired_at FROM locks WHERE name='scan'").fetchone()
    return bool(row and row["acquired_at"] > time.time() - STALE_LOCK_SECONDS)


def upsert_job(conn, job: Job) -> str:
    """Insert or refresh a job. Returns 'new' | 'updated' | 'seen'."""
    row = conn.execute("SELECT content_hash FROM jobs WHERE job_key=?", (job.job_key,)).fetchone()
    ts = now()
    if row is None:
        conn.execute(
            "INSERT INTO jobs(job_key, content_hash, data, source, first_seen_at, last_seen_at)"
            " VALUES(?,?,?,?,?,?)",
            (job.job_key, job.content_hash, job.model_dump_json(), job.source, ts, ts))
        return "new"
    conn.execute(
        "UPDATE jobs SET last_seen_at=?, absence_count=0, status='active', data=?, content_hash=?"
        " WHERE job_key=?",
        (ts, job.model_dump_json(), job.content_hash, job.job_key))
    return "updated" if row["content_hash"] != job.content_hash else "seen"


def mark_absences(conn, source: str, seen_keys: set[str], threshold: int) -> None:
    """Increment absence for this source's active jobs not seen in a SUCCESSFUL scan.

    Never called for failed sources (eng review D9): a failed fetch must not
    count as a job disappearing.
    """
    rows = conn.execute(
        "SELECT job_key, absence_count FROM jobs WHERE source=? AND status='active'",
        (source,)).fetchall()
    for r in rows:
        if r["job_key"] in seen_keys:
            continue
        n = r["absence_count"] + 1
        status = "possibly_removed" if n >= threshold else "active"
        conn.execute("UPDATE jobs SET absence_count=?, status=? WHERE job_key=?",
                     (n, status, r["job_key"]))


def get_job(conn, job_key: str) -> Job | None:
    row = conn.execute("SELECT data FROM jobs WHERE job_key=?", (job_key,)).fetchone()
    return Job.model_validate_json(row["data"]) if row else None


def active_jobs_for_company(conn, normalized_company: str) -> list[Job]:
    rows = conn.execute("SELECT data FROM jobs WHERE status='active'").fetchall()
    jobs = [Job.model_validate_json(r["data"]) for r in rows]
    return [j for j in jobs if j.normalized_company == normalized_company]


def save_rejection(conn, job: Job, reason: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO rejected(job_key, filter_reason, data, seen_at) VALUES(?,?,?,?)",
        (job.job_key, reason, job.model_dump_json(), now()))


def has_evaluation(conn, cache_key: str) -> bool:
    return conn.execute("SELECT 1 FROM evaluations WHERE cache_key=?", (cache_key,)).fetchone() is not None


def save_evaluation(conn, cache_key: str, job_key: str, dims: dict, overall: float,
                    tier: str, reasons: list, concerns: list, confidence: str,
                    recommendation: str, prompt_version: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO evaluations VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (cache_key, job_key, json.dumps(dims), overall, tier, json.dumps(reasons),
         json.dumps(concerns), confidence, recommendation, prompt_version, now()))


def set_disposition(conn, job_key: str, status: str | None, reason: str | None = None) -> None:
    if status is None:
        conn.execute("DELETE FROM dispositions WHERE job_key=?", (job_key,))
    else:
        conn.execute("INSERT OR REPLACE INTO dispositions VALUES(?,?,?,?)",
                     (job_key, status, reason, now()))
    conn.commit()


def feed(conn, cache_prefix_filter: str | None = None) -> list[dict]:
    """Active, non-dismissed jobs joined with their latest evaluation, best first."""
    rows = conn.execute("""
        SELECT j.job_key, j.data, j.first_seen_at, j.source, e.overall, e.tier,
               e.dimension_scores, e.reasons, e.concerns, e.confidence, e.recommendation,
               d.status AS disposition, d.reason AS disposition_reason
        FROM jobs j
        JOIN evaluations e ON e.job_key = j.job_key
          AND e.evaluated_at = (SELECT MAX(evaluated_at) FROM evaluations WHERE job_key = j.job_key)
        LEFT JOIN dispositions d ON d.job_key = j.job_key
        WHERE j.status = 'active'
        ORDER BY e.overall DESC
    """).fetchall()
    out = []
    for r in rows:
        item = dict(r)
        item["job"] = Job.model_validate_json(item.pop("data"))
        for f in ("dimension_scores", "reasons", "concerns"):
            item[f] = json.loads(item[f])
        out.append(item)
    return out
