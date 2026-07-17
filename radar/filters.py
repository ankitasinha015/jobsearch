"""Deterministic hard filters (PRD §15.2). Rejected jobs are retained with a
reason — inspectable, never silently dropped. Salary floor only applies when
salary is STATED below the floor; unknown passes (PRD §13.2)."""
from __future__ import annotations

import re

import yaml

from .config import preferences_text
from .models import Job

EXCLUDED_SENIORITY_RE = re.compile(
    r"\b(junior|jr\.?|associate|assistant|intern(ship)?|early career|new grad(uate)?|campus)\b", re.I)
NON_PM_RE = re.compile(
    r"\b(product marketing|product design(er)?|product analyst|product owner|"
    r"product support|product operations|product counsel)\b", re.I)
PM_TITLE_RE = re.compile(
    r"product (manager|lead|management)|director,? product|head of product"
    r"|product strategy|forward deployed", re.I)
NON_US_HINTS = (
    "toronto", "vancouver", "london", "dublin", "berlin", "paris", "amsterdam",
    "bangalore", "bengaluru", "hyderabad", "singapore", "tokyo", "sydney",
    "tel aviv", "warsaw", "lisbon", "mexico city", "sao paulo", "serbia",
    "novi sad", "ireland", "israel", "united kingdom", "canada", "india", "emea")
US_HINTS = ("united states", ", us", "usa", "u.s.", "remote - us", "remote, us", "amer")
US_STATE_RE = re.compile(r",\s*(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b")

# Explicit no-sponsorship language only — silence about sponsorship passes
# (PRD §13.2: unknown stays unknown; the scorer flags it as a concern instead).
NO_SPONSORSHIP_RE = re.compile(
    r"\b(?:unable|not able|cannot|can not|will not|won'?t|does not|do not|no)\b"
    r"[^.\n]{0,40}\bsponsor"                                   # "unable to sponsor visas"
    r"|without[^.\n]{0,30}\bsponsorship"                       # "authorized to work without (the need for) sponsorship"
    r"|sponsorship\s+(?:is\s+)?not\s+(?:available|offered|provided)"
    r"|\bu\.?s\.?\s+citizens?\s+(?:only|required)"
    r"|\bmust\s+be\s+(?:a\s+)?u\.?s\.?\s+citizen"
    r"|\bcitizenship\s+(?:is\s+)?required"
    r"|\b(?:green\s*card\s+holders?|permanent\s+residents?)\s+only"
    r"|\bu\.?s\.?\s+persons?\s+(?:only|required)|\bitar\b"     # export-control roles
    r"|security\s+clearance\s+(?:is\s+)?required"
    r"|\bactive\s+(?:ts/?sci|top.?secret|security)\s+clearance"
    r"|\bts/?sci\s+clearance",
    re.I)


def _prefs() -> dict:
    return yaml.safe_load(preferences_text())


def hard_filter(job: Job, prefs: dict | None = None) -> str | None:
    """Return a rejection reason, or None if the job passes to LLM scoring."""
    prefs = prefs or _prefs()

    if EXCLUDED_SENIORITY_RE.search(job.title):
        return "excluded_seniority_title"

    if NON_PM_RE.search(job.title):
        return "not_product_management"
    if not PM_TITLE_RE.search(job.title):
        return "title_not_pm_scope"

    loc = job.location.lower()
    if job.remote_status != "remote":
        if any(h in loc for h in NON_US_HINTS) and not (
            any(h in loc for h in US_HINTS) or US_STATE_RE.search(job.location)
        ):
            return "location_not_us"
    else:
        # Remote but explicitly scoped to a non-US region
        if any(h in loc for h in NON_US_HINTS) and not (
            any(h in loc for h in US_HINTS) or US_STATE_RE.search(job.location)
        ):
            return "remote_but_not_us_eligible"

    if prefs.get("visa_sponsorship_required") and NO_SPONSORSHIP_RE.search(
            f"{job.title}\n{job.description}"):
        return "no_visa_sponsorship"

    excluded_companies = [c.lower() for c in (prefs.get("companies_excluded") or [])]
    if job.company.lower() in excluded_companies:
        return "company_excluded"

    et = (job.employment_type or "unknown").lower()
    if et not in ("unknown", "") and not any(
        k in et for k in ("full", "fulltime", "full-time", "permanent")):
        return "not_full_time"

    floor = (prefs.get("compensation") or {}).get("min_base_salary_usd")
    if floor and job.salary_max is not None and (job.currency in (None, "USD")):
        if job.salary_max < int(floor):
            return "stated_salary_below_floor"

    return None
