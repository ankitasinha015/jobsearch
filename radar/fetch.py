"""Source fetchers. ATS JSON APIs are primary; JobSpy is supplementary and may
die when blocked — the scan must succeed without it (BUILDSPEC)."""
from __future__ import annotations

import requests

UA = {"User-Agent": "job-radar/0.1 (personal job search tool)"}
TIMEOUT = 20


def fetch_greenhouse(slug: str) -> list[dict]:
    r = requests.get(
        f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
        headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json().get("jobs", [])


def fetch_lever(slug: str) -> list[dict]:
    r = requests.get(f"https://api.lever.co/v0/postings/{slug}?mode=json",
                     headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else []


def fetch_ashby(slug: str) -> list[dict]:
    # GET, not POST — POST returns 401 (verified live 2026-07-16).
    r = requests.get(
        f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true",
        headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json().get("jobs", [])


ATS_FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
}


def fetch_company(company: dict) -> list[dict]:
    """Fetch raw postings for one companies.yaml entry."""
    return ATS_FETCHERS[company["ats"]](company["slug"])


def fetch_jobspy(search_term: str, location: str = "United States",
                 results_wanted: int = 50) -> list[dict]:
    """Supplementary aggregator fetch. Import inside the function so a broken
    or missing jobspy install can never take down the ATS path."""
    from jobspy import scrape_jobs  # noqa: PLC0415
    df = scrape_jobs(
        site_name=["indeed", "zip_recruiter", "google"],  # LinkedIn stays OFF (PRD §5)
        search_term=search_term, location=location,
        results_wanted=results_wanted, hours_old=72, country_indeed="USA")
    return df.to_dict("records")
