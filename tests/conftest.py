import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from radar import db  # noqa: E402
from radar.models import Job  # noqa: E402


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "test.db")
    yield c
    c.close()


@pytest.fixture
def weights():
    return {
        "weights": {
            "functional_responsibility_match": 25, "seniority_scope_match": 15,
            "product_domain_match": 15, "skills_experience_match": 15,
            "location_work_arrangement": 10, "industry_mission_match": 8,
            "compensation_match": 5, "company_stage_match": 4, "posting_freshness": 3,
        },
        "tier_bands": {"excellent": [85, 101], "strong": [75, 85],
                       "possible": [60, 75], "weak": [40, 60], "hidden_below": 40},
        "scoring": {"model": "stub", "prompt_version": "v1",
                    "max_llm_calls_per_run": 150,
                    "first_run_max_posting_age_days": 30, "max_retries_per_listing": 2},
        "dedupe": {"near_dup_similarity_threshold": 90},
        "freshness": {"possibly_removed_after_consecutive_absences": 3},
    }


def make_job(**over) -> Job:
    base = dict(
        title="Senior Product Manager, AI Platform", company="Acme Health",
        location="Remote, US", remote_status="remote", remote_status_provenance="stated",
        employment_type="full-time",
        description="Own the AI platform roadmap. Partner with clinical and eng teams. " * 8,
        salary_min=180000, salary_max=220000, currency="USD", date_posted="2026-07-10",
        source="greenhouse:acme", source_type="ats", ats="greenhouse",
        source_url="https://boards.greenhouse.io/acme/jobs/1",
        canonical_url="https://boards.greenhouse.io/acme/jobs/1")
    base.update(over)
    return Job(**base)
