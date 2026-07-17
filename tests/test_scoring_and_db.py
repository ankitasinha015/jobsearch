import json
from datetime import date

from conftest import make_job

from radar import db
from radar.models import LLM_DIMENSIONS
from radar.score import compute_overall, freshness_score, tier_for


def dims(v: int) -> dict:
    d = {k: v for k in LLM_DIMENSIONS}
    d["posting_freshness"] = v
    return d


def test_weighted_sum_all_tens_is_100():
    assert compute_overall(dims(10), WEIGHTS) == 100.0
    assert compute_overall(dims(0), WEIGHTS) == 0.0


def test_half_open_band_edges():
    # 84.99 -> strong, 85.0 -> excellent (eng review: half-open intervals)
    assert tier_for(84.9, WEIGHTS) == "strong"
    assert tier_for(85.0, WEIGHTS) == "excellent"
    assert tier_for(75.0, WEIGHTS) == "strong"
    assert tier_for(74.9, WEIGHTS) == "possible"
    assert tier_for(60.0, WEIGHTS) == "possible"
    assert tier_for(39.9, WEIGHTS) == "hidden"


def test_freshness_mechanical():
    today = date(2026, 7, 16)
    assert freshness_score("2026-07-14", today) == 10
    assert freshness_score("2026-07-04", today) == 7
    assert freshness_score("2026-06-20", today) == 4
    assert freshness_score("2026-01-01", today) == 2
    assert freshness_score(None, today) == 5  # unknown stays neutral


def test_upsert_lifecycle_new_updated_seen(conn):
    job = make_job()
    assert db.upsert_job(conn, job) == "new"
    assert db.upsert_job(conn, job) == "seen"
    changed = make_job(description="Meaningfully different responsibilities. " * 10)
    assert db.upsert_job(conn, changed) == "updated"


def test_absence_counting_and_possibly_removed(conn):
    job = make_job()
    db.upsert_job(conn, job)
    for _ in range(3):
        db.mark_absences(conn, job.source, set(), threshold=3)
    row = conn.execute("SELECT status, absence_count FROM jobs").fetchone()
    assert row["status"] == "possibly_removed" and row["absence_count"] == 3
    # reappearing resets
    db.upsert_job(conn, job)
    row = conn.execute("SELECT status, absence_count FROM jobs").fetchone()
    assert row["status"] == "active" and row["absence_count"] == 0


def test_absence_never_counted_for_failed_source(conn):
    """D9: mark_absences is only invoked for successful sources — verify a
    non-invoked source keeps its jobs active (the pipeline enforces this by
    only iterating seen_by_source, which contains successful sources only)."""
    job = make_job()
    db.upsert_job(conn, job)
    db.mark_absences(conn, "some-other-source", set(), threshold=3)
    row = conn.execute("SELECT status, absence_count FROM jobs").fetchone()
    assert row["status"] == "active" and row["absence_count"] == 0


def test_dispositions_persist_and_restore(conn):
    job = make_job()
    db.upsert_job(conn, job)
    db.set_disposition(conn, job.job_key, "dismissed", "wrong location")
    row = conn.execute("SELECT * FROM dispositions").fetchone()
    assert row["status"] == "dismissed" and row["reason"] == "wrong location"
    db.set_disposition(conn, job.job_key, None)  # restore
    assert conn.execute("SELECT COUNT(*) c FROM dispositions").fetchone()["c"] == 0


def test_scan_lock_exclusive(conn):
    assert db.acquire_scan_lock(conn)
    assert not db.acquire_scan_lock(conn)
    db.release_scan_lock(conn)
    assert db.acquire_scan_lock(conn)


def test_feed_joins_latest_eval_and_sorts(conn, weights):
    hi, lo = make_job(), make_job(title="Staff Product Manager, Data")
    db.upsert_job(conn, hi)
    db.upsert_job(conn, lo)
    db.save_evaluation(conn, "k1", hi.job_key, dims(9), 90.0, "excellent",
                       ["r1", "r2"], [], "high", "strongly_review", "v1")
    db.save_evaluation(conn, "k2", lo.job_key, dims(6), 62.0, "possible",
                       ["r1", "r2"], ["c1"], "medium", "consider", "v1")
    items = db.feed(conn)
    assert [i["overall"] for i in items] == [90.0, 62.0]
    assert items[0]["job"].job_key == hi.job_key


# module-level weights fixture value for the pure-math tests
from conftest import weights as _wfix  # noqa: E402

WEIGHTS = {
    "weights": {
        "functional_responsibility_match": 25, "seniority_scope_match": 15,
        "product_domain_match": 15, "skills_experience_match": 15,
        "location_work_arrangement": 10, "industry_mission_match": 8,
        "compensation_match": 5, "company_stage_match": 4, "posting_freshness": 3,
    },
    "tier_bands": {"excellent": [85, 101], "strong": [75, 85],
                   "possible": [60, 75], "weak": [40, 60], "hidden_below": 40},
}


def test_dream_company_boost(monkeypatch):
    from radar import config
    from radar.score import dream_boost
    monkeypatch.setattr(config, "preferences_text",
                        lambda: "dream_companies:\n  - Google\n  - Uber\n")
    assert dream_boost(70.0, "Google") == (75.0, True)
    assert dream_boost(98.0, "Uber") == (100.0, True)   # capped
    assert dream_boost(70.0, "Headway") == (70.0, False)


def test_nyc_cap():
    from radar.score import nyc_cap
    assert nyc_cap(78.8, "New York, New York, USA") == (74.0, True)
    assert nyc_cap(80.0, "New York, NY; San Francisco, CA") == (80.0, False)
    assert nyc_cap(70.0, "New York, NY") == (70.0, False)  # already below strong
    assert nyc_cap(90.0, "Remote, US") == (90.0, False)
