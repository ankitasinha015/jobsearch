"""Scan orchestration: fetch -> normalize -> dedupe -> filter -> score -> db.

Source-failure semantics (eng review D9): absence counting runs ONLY for
sources whose fetch succeeded; zero successful sources marks the scan failed.
"""
from __future__ import annotations

import json
from datetime import date, timedelta

from . import config, db
from .dedupe import dedupe_batch, match_existing
from .fetch import fetch_company, fetch_jobspy
from .filters import hard_filter
from .models import Job
from .normalize import NORMALIZERS, normalize_jobspy

JOBSPY_SEARCHES = ["senior product manager AI", "staff product manager"]


def run_scan(conn=None, include_jobspy: bool = True, log=print) -> dict:
    config.bootstrap_env()
    conn = conn or db.connect()
    if not db.acquire_scan_lock(conn):
        raise RuntimeError("scan already in progress")
    run_id = conn.execute(
        "INSERT INTO scan_runs(started_at, status) VALUES(?, 'running')",
        (db.now(),)).lastrowid
    conn.commit()
    try:
        result = _scan(conn, include_jobspy, log)
        status = "failed" if result["sources_succeeded"] == 0 else "ok"
        conn.execute(
            "UPDATE scan_runs SET completed_at=?, status=?, sources_attempted=?,"
            " sources_succeeded=?, raw_count=?, new_count=?, updated_count=?,"
            " scored_count=?, errors=? WHERE id=?",
            (db.now(), status, result["sources_attempted"], result["sources_succeeded"],
             result["raw_count"], result["new_count"], result["updated_count"],
             result["scored_count"], json.dumps(result["errors"]), run_id))
        conn.commit()
        result["status"] = status
        return result
    finally:
        db.release_scan_lock(conn)


def _scan(conn, include_jobspy: bool, log) -> dict:
    weights = config.load_weights()
    companies = config.load_companies()
    threshold = weights["dedupe"]["near_dup_similarity_threshold"]
    absence_threshold = weights["freshness"]["possibly_removed_after_consecutive_absences"]

    errors: list[str] = []
    batch: list[Job] = []
    seen_by_source: dict[str, set[str]] = {}
    attempted = succeeded = 0

    for company in companies:
        attempted += 1
        source = f"{company['ats']}:{company['slug']}"
        try:
            raws = fetch_company(company)
            normalizer = NORMALIZERS[company["ats"]]
            jobs = []
            for raw in raws:
                try:
                    jobs.append(normalizer(raw, company))
                except Exception as e:  # malformed posting: skip with log
                    errors.append(f"normalize {source}: {e}")
            batch.extend(jobs)
            seen_by_source[source] = {j.job_key for j in jobs}
            succeeded += 1
            log(f"  ok   {source}: {len(jobs)} jobs")
        except Exception as e:
            errors.append(f"fetch {source}: {type(e).__name__}: {e}")
            log(f"  FAIL {source}: {type(e).__name__}")

    if include_jobspy:
        attempted += 1
        try:
            spy_jobs = []
            for term in JOBSPY_SEARCHES:
                for raw in fetch_jobspy(term):
                    try:
                        spy_jobs.append(normalize_jobspy(raw))
                    except Exception as e:
                        errors.append(f"normalize jobspy: {e}")
            batch.extend(spy_jobs)
            succeeded += 1
            log(f"  ok   jobspy: {len(spy_jobs)} jobs")
        except Exception as e:  # supplementary source dies gracefully
            errors.append(f"jobspy unavailable: {type(e).__name__}: {e}")
            log(f"  FAIL jobspy (supplementary, continuing): {type(e).__name__}")

    if succeeded == 0:
        return {"sources_attempted": attempted, "sources_succeeded": 0,
                "raw_count": len(batch), "new_count": 0, "updated_count": 0,
                "scored_count": 0, "errors": errors}

    raw_count = len(batch)
    batch = dedupe_batch(batch, threshold)

    # Preload active jobs grouped by company ONCE — querying and JSON-parsing
    # the whole table per incoming job is quadratic (found by the first full
    # 44-board scan, which spent 30+ minutes here).
    existing_by_co: dict[str, list[Job]] = {}
    for row in conn.execute("SELECT data FROM jobs WHERE status='active'"):
        j = Job.model_validate_json(row["data"])
        existing_by_co.setdefault(j.normalized_company, []).append(j)

    new_count = updated_count = 0
    to_score: list[Job] = []
    for job in batch:
        existing = match_existing(
            job, existing_by_co.get(job.normalized_company, []), threshold)
        if existing and existing.job_key != job.job_key:
            # near-dup of a stored job from another source: refresh, don't re-add
            seen_by_source.get(existing.source, set()).add(existing.job_key)
            continue
        state = db.upsert_job(conn, job)
        if state == "new":
            new_count += 1
            existing_by_co.setdefault(job.normalized_company, []).append(job)
        elif state == "updated":
            updated_count += 1
        reason = hard_filter(job)
        if reason:
            db.save_rejection(conn, job, reason)
            continue
        to_score.append(job)
    conn.commit()

    # Absence counting — successful sources only (D9)
    for source, seen in seen_by_source.items():
        db.mark_absences(conn, source, seen, absence_threshold)
    conn.commit()

    scored = score_pending(conn, to_score, weights, log)
    return {"sources_attempted": attempted, "sources_succeeded": succeeded,
            "raw_count": raw_count, "new_count": new_count,
            "updated_count": updated_count, "scored_count": scored, "errors": errors}


def score_pending(conn, jobs: list[Job], weights: dict, log=print) -> int:
    """LLM-score jobs without a cached evaluation. Freshest first, capped per
    run; first run scores only postings <= first_run_max_posting_age_days old."""
    from . import score as scorer  # anthropic import stays off the fetch path

    import anthropic
    scoring = weights["scoring"]
    first_run = conn.execute(
        "SELECT COUNT(*) c FROM evaluations").fetchone()["c"] == 0
    cutoff = (date.today() - timedelta(days=scoring["first_run_max_posting_age_days"])).isoformat()

    pending = []
    for job in jobs:
        key = scorer.cache_key(job, weights)
        if db.has_evaluation(conn, key):
            continue
        if first_run and job.date_posted and job.date_posted < cutoff:
            continue
        pending.append((job.date_posted or "0000-00-00", job, key))
    pending.sort(key=lambda t: t[0], reverse=True)  # freshest first
    cap = scoring["max_llm_calls_per_run"]
    if len(pending) > cap:
        log(f"  cap: scoring {cap} of {len(pending)} pending (rest next run)")
        pending = pending[:cap]

    if not pending:
        return 0
    client = anthropic.Anthropic()
    system_blocks = scorer.build_system_blocks()
    scored = 0
    for _, job, key in pending:
        try:
            ev = scorer.evaluate_job(client, job, weights, system_blocks)
        except Exception as e:
            log(f"  skip {job.company} / {job.title}: {e}")
            continue
        db.save_evaluation(conn, key, job.job_key, ev["dimension_scores"], ev["overall"],
                           ev["tier"], ev["reasons"], ev["concerns"], ev["confidence"],
                           ev["recommendation"], scoring["prompt_version"])
        scored += 1
        if scored % 10 == 0:
            conn.commit()
            log(f"  scored {scored}/{len(pending)}")
    conn.commit()
    return scored


if __name__ == "__main__":
    import sys
    include_spy = "--no-jobspy" not in sys.argv
    result = run_scan(include_jobspy=include_spy)
    print(json.dumps({k: v for k, v in result.items() if k != "errors"}, indent=1))
    if result["errors"]:
        print(f"errors ({len(result['errors'])}):")
        for e in result["errors"][:10]:
            print(" ", e)
