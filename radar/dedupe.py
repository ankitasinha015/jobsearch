"""Dedup: exact key match + near-dup within the same normalized company
(eng review D6 — compare new listings only against active ones at that company).
Canonical preference: ATS-direct beats aggregator (PRD §14.2)."""
from __future__ import annotations

from rapidfuzz import fuzz

from .models import Job


def is_near_dup(a: Job, b: Job, threshold: int) -> bool:
    if a.normalized_company != b.normalized_company:
        return False
    if fuzz.ratio(a.normalized_title, b.normalized_title) < 80:
        return False
    return fuzz.token_sort_ratio(a.description[:2000], b.description[:2000]) >= threshold


def dedupe_batch(jobs: list[Job], threshold: int) -> list[Job]:
    """Collapse duplicates inside one scan batch. ATS-direct wins over aggregator."""
    jobs = sorted(jobs, key=lambda j: 0 if j.source_type == "ats" else 1)
    kept: list[Job] = []
    by_key: dict[str, Job] = {}
    by_company: dict[str, list[Job]] = {}
    for job in jobs:
        if job.job_key in by_key:
            continue
        if any(is_near_dup(job, k, threshold) for k in by_company.get(job.normalized_company, [])):
            continue
        by_key[job.job_key] = job
        by_company.setdefault(job.normalized_company, []).append(job)
        kept.append(job)
    return kept


def match_existing(job: Job, existing_same_company: list[Job], threshold: int) -> Job | None:
    """Return the stored active job this one duplicates, if any."""
    for other in existing_same_company:
        if other.job_key == job.job_key or is_near_dup(job, other, threshold):
            return other
    return None
