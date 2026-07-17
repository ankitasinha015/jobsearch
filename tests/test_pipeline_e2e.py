"""E2E: fixtures -> normalize -> dedupe -> filter -> score (stubbed LLM) -> db -> feed.
Also covers cache invalidation via prefs-hash change and the per-run cap."""
import json

import pytest
from conftest import make_job

import radar.pipeline as pipeline
from radar import config, db
from radar.models import LLM_DIMENSIONS
from radar.score import cache_key

GH_FIXTURE = [{
    "title": "Senior Product Manager, Clinical AI",
    "location": {"name": "Remote - US"},
    "content": "&lt;p&gt;Own clinical AI agent roadmap. Evaluation frameworks, guardrails, HITL escalation.&lt;/p&gt;",
    "absolute_url": "https://boards.greenhouse.io/acme/jobs/1",
    "updated_at": "2026-07-12T00:00:00Z",
}, {
    "title": "Associate Product Manager, New Grad",
    "location": {"name": "San Francisco, CA"},
    "content": "&lt;p&gt;Early career program.&lt;/p&gt;",
    "absolute_url": "https://boards.greenhouse.io/acme/jobs/2",
    "updated_at": "2026-07-12T00:00:00Z",
}]


def stub_eval(client, job, weights, system_blocks):
    dims = {k: 8 for k in LLM_DIMENSIONS}
    dims["posting_freshness"] = 10
    return {"dimension_scores": dims, "overall": 82.0, "tier": "strong",
            "reasons": ["clinical AI matches her Upward Health agent work",
                        "evaluation frameworks are her core skill"],
            "concerns": [], "confidence": "high", "recommendation": "review"}


@pytest.fixture
def wired(tmp_path, conn, weights, monkeypatch):
    monkeypatch.setattr(config, "load_weights", lambda: weights)
    monkeypatch.setattr(config, "load_companies",
                        lambda: [{"name": "Acme Health", "ats": "greenhouse", "slug": "acme"}])
    monkeypatch.setattr(pipeline, "fetch_company", lambda c: list(GH_FIXTURE))
    import radar.score as scorer
    monkeypatch.setattr(scorer, "evaluate_job", stub_eval)
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda: object())
    monkeypatch.setattr(scorer, "build_system_blocks", lambda: [])
    return conn


def test_full_scan_end_to_end(wired):
    conn = wired
    result = pipeline.run_scan(conn=conn, include_jobspy=False, log=lambda *a: None)
    assert result["status"] == "ok"
    assert result["sources_succeeded"] == 1
    assert result["new_count"] == 2          # both stored
    assert result["scored_count"] == 1       # APM hard-filtered before the LLM
    rej = conn.execute("SELECT filter_reason FROM rejected").fetchone()
    assert rej["filter_reason"] == "excluded_seniority_title"
    items = db.feed(conn)
    assert len(items) == 1 and items[0]["tier"] == "strong"
    assert "&lt;" not in items[0]["job"].description  # unescape ran


def test_second_scan_uses_cache_no_new_scoring(wired):
    conn = wired
    pipeline.run_scan(conn=conn, include_jobspy=False, log=lambda *a: None)
    r2 = pipeline.run_scan(conn=conn, include_jobspy=False, log=lambda *a: None)
    assert r2["new_count"] == 0 and r2["scored_count"] == 0  # unchanged job not re-scored


def test_all_sources_failed_marks_scan_failed(wired, monkeypatch):
    conn = wired
    monkeypatch.setattr(pipeline, "fetch_company",
                        lambda c: (_ for _ in ()).throw(RuntimeError("boom")))
    result = pipeline.run_scan(conn=conn, include_jobspy=False, log=lambda *a: None)
    assert result["status"] == "failed" and result["sources_succeeded"] == 0
    row = conn.execute("SELECT status FROM scan_runs ORDER BY id DESC").fetchone()
    assert row["status"] == "failed"
    # and no absence was counted for the failed source (D9)
    assert conn.execute("SELECT COUNT(*) c FROM jobs WHERE absence_count>0").fetchone()["c"] == 0


def test_prefs_change_invalidates_cache_key(monkeypatch, weights):
    job = make_job()
    monkeypatch.setattr(config, "prefs_hash", lambda: "aaa")
    monkeypatch.setattr(config, "profile_hash", lambda: "bbb")
    k1 = cache_key(job, weights)
    monkeypatch.setattr(config, "prefs_hash", lambda: "ccc")
    assert cache_key(job, weights) != k1


def test_cap_scores_freshest_first(wired, weights, monkeypatch):
    conn = wired
    weights["scoring"]["max_llm_calls_per_run"] = 1
    jobs = [make_job(title=f"Senior Product Manager {i}", date_posted=f"2026-07-{10+i:02d}",
                     description=f"Distinct role {i}. " * 20) for i in range(3)]
    # regression: equal dates must not fall through to comparing Job objects
    jobs.insert(0, make_job(title="Senior Product Manager tie",
                            date_posted="2026-07-10",
                            description="Tie-date role. " * 20))
    scored = pipeline.score_pending(conn, jobs, weights, log=lambda *a: None)
    assert scored == 1
    freshest = max(jobs, key=lambda j: j.date_posted)
    row = conn.execute("SELECT job_key FROM evaluations").fetchone()
    assert row["job_key"] == freshest.job_key  # freshest (07-12) won the cap slot
