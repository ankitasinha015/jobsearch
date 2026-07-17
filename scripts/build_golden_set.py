"""Transcribe the 22 labeled golden-set postings into golden_set.jsonl.

Fetches full descriptions live (ATS JSON APIs, Uber careers API, raw HTML for
Google/Intuitive) and writes one Job record + expected_tier + label_reason per
line. Run: python scripts/build_golden_set.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from radar import config  # noqa: E402

config.bootstrap_env()

import requests  # noqa: E402

from radar.models import Job  # noqa: E402
from radar.normalize import (infer_remote, normalize_ashby,  # noqa: E402
                             normalize_greenhouse, strip_html)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) job-radar/0.1"}

# (num, expected_tier, reason, method, params)
ENTRIES = [
    (1, "strong", "Definitely applying this week", "ashby",
     {"co": "Headway", "slug": "headway", "uuid": "d0d1aaed"}),
    (2, "excellent", "Drop everything, apply today", "ashby",
     {"co": "Abridge", "slug": "abridge", "uuid": "9c7ba6c3"}),
    (3, "excellent", "Drop everything, apply today", "greenhouse",
     {"co": "Databricks", "slug": "databricks", "id": 8560772002}),
    (4, "excellent", "Drop everything, apply today", "greenhouse",
     {"co": "Maven Clinic", "slug": "mavenclinic", "id": 8599673002}),
    (5, "excellent", "Drop everything, apply today", "ashby",
     {"co": "Commure", "slug": "commure", "uuid": "a745736e"}),
    (6, "excellent", "Drop everything, apply today", "greenhouse",
     {"co": "Scale AI", "slug": "scaleai", "id": 4709281005}),
    (7, "strong", "Definitely applying this week", "ashby",
     {"co": "Infinitus", "slug": "infinitus", "uuid": "794bbc47"}),
    (8, "strong", "Dream company - PM II level is fine", "html",
     {"co": "Google", "title": "Product Manager II, Core", "loc": "United States",
      "url": "https://www.google.com/about/careers/applications/jobs/results/103807688755815110-product-manager-ii/"}),
    (9, "strong", "Dream company - healthcare robotics, commutable", "html",
     {"co": "Intuitive", "title": "Sr Product Manager, Upstream Software, ION",
      "loc": "Sunnyvale, CA",
      "url": "https://careers.intuitive.com/en/jobs/744000127493169/JOB215303/sr-product-manager-upstream-software-ion/"}),
    (10, "strong", "Dream company + GenAI at Senior level", "uber",
     {"co": "Uber", "id": 159550, "title": "Senior Product Manager, Generative AI",
      "loc": "New York, NY; Seattle, WA; Sunnyvale, CA; San Francisco, CA"}),
    (11, "strong", "Dream company + applied AI, commutable", "uber",
     {"co": "Uber", "id": 159480, "title": "Senior Product Manager, Applied AI",
      "loc": "San Francisco, CA; Sunnyvale, CA"}),
    (12, "excellent", "Drop everything, apply today", "ashby",
     {"co": "Abridge", "slug": "abridge", "uuid": "c45524b6"}),
    (13, "possible", "Maybe - would read fully, apply on a slow week", "greenhouse",
     {"co": "Anthropic", "slug": "anthropic", "id": 5124623008}),
    (14, "possible", "Maybe - would read fully, apply on a slow week", "greenhouse",
     {"co": "Datadog", "slug": "datadog", "id": 7785350}),
    (15, "possible", "Maybe - would read fully, apply on a slow week", "greenhouse",
     {"co": "Fivetran", "slug": "fivetran", "id": 7535819003}),
    (16, "strong", "Definitely applying this week", "greenhouse",
     {"co": "Glean", "slug": "gleanwork", "id": 4702151005}),
    (17, "hard-reject", "Doesn't align with my experience (Director/people-management scope)",
     "ashby", {"co": "Abridge", "slug": "abridge", "uuid": "7745d77e"}),
    (18, "hard-reject", "Doesn't align with my experience (too junior)", "greenhouse",
     {"co": "Databricks", "slug": "databricks", "id": 7586263002}),
    (19, "hard-reject", "Doesn't align with my experience (non-US geography)", "greenhouse",
     {"co": "GitLab", "slug": "gitlab", "id": 8568868002}),
    (20, "hard-reject", "Doesn't align with my experience (non-US geography)", "ashby",
     {"co": "Cohere", "slug": "cohere", "uuid": "1d1b300d"}),
    (21, "hard-reject", "Doesn't align with my experience (corp-dev, not product ownership)",
     "greenhouse", {"co": "Datadog", "slug": "datadog", "id": 8011158}),
    (22, "hard-reject", "Doesn't align with my experience (design role)", "greenhouse",
     {"co": "Amplitude", "slug": "amplitude", "id": 8622704002}),
]

_ashby_cache: dict[str, list] = {}


def fetch_ashby(p) -> Job:
    slug = p["slug"]
    if slug not in _ashby_cache:
        r = requests.get(
            f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true",
            headers=UA, timeout=20)
        r.raise_for_status()
        _ashby_cache[slug] = r.json().get("jobs", [])
    for raw in _ashby_cache[slug]:
        if p["uuid"] in (raw.get("jobUrl", "") + raw.get("applyUrl", "")):
            return normalize_ashby(raw, {"name": p["co"], "slug": slug, "ats": "ashby"})
    raise LookupError(f"ashby {slug}: uuid {p['uuid']} not on board (posting removed?)")


def fetch_greenhouse(p) -> Job:
    r = requests.get(
        f"https://boards-api.greenhouse.io/v1/boards/{p['slug']}/jobs/{p['id']}",
        headers=UA, timeout=20)
    r.raise_for_status()
    return normalize_greenhouse(r.json(), {"name": p["co"], "slug": p["slug"], "ats": "greenhouse"})


BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _extract_json_string(html_text: str, key: str) -> str:
    """Pull the LONGEST "key":"..." value out of embedded JSON.

    Uber ships the JD inside a double-escaped React flight stream, so we
    normalize \\" -> " first, then scan every occurrence and keep the longest
    (short ones are UI labels and meta teasers)."""
    candidates = []
    for text in (html_text, html_text.replace('\\\\', '\\').replace('\\"', '"')):
        marker = f'"{key}":"'
        start = 0
        while True:
            start = text.find(marker, start)
            if start < 0:
                break
            i = start + len(marker)
            out = []
            while i < len(text):
                ch = text[i]
                if ch == "\\":
                    out.append(text[i:i + 2])
                    i += 2
                    continue
                if ch == '"':
                    break
                out.append(ch)
                i += 1
            raw = "".join(out)
            try:
                raw = json.loads(f'"{raw}"')
            except json.JSONDecodeError:
                pass
            candidates.append(raw)
            start = i
    return max(candidates, key=len) if candidates else ""


def fetch_uber(p) -> Job:
    # Uber's careers pages are JS-rendered and the search API omits
    # descriptions, so these two JDs were captured via a rendered browser
    # (2026-07-16) into data/uber_{id}.txt.
    path = config.ROOT / "data" / f"uber_{p['id']}.txt"
    desc = path.read_text(encoding="utf-8")
    title = p["title"]
    remote, prov = infer_remote(title, p["loc"], desc)
    if remote == "unknown":
        remote, prov = "hybrid", "stated"  # "at least 50% of their time in-office"
    url = f"https://www.uber.com/careers/list/{p['id']}/"
    return Job(title=title, company="Uber", location=p["loc"],
               remote_status=remote, remote_status_provenance=prov,
               description=desc[:12000], salary_min=190000, salary_max=211000,
               currency="USD", date_posted="2026-06-19",
               source="golden_set:uber", source_type="golden_set",
               source_url=url, canonical_url=url)


JD_START_MARKERS = ["About the job", "About the Role", "Primary Function",
                    "Job Description", "Minimum qualifications"]


def fetch_html(p) -> Job:
    r = requests.get(p["url"], headers=BROWSER_HEADERS, timeout=30)
    r.raise_for_status()
    desc = strip_html(r.text)
    # cut page-chrome noise: start at the JD body if a marker is present
    for marker in JD_START_MARKERS:
        idx = desc.find(marker)
        if idx > 0:
            desc = desc[idx:]
            break
    desc = desc[:12000]
    remote, prov = infer_remote(p["title"], p["loc"], desc)
    return Job(title=p["title"], company=p["co"], location=p["loc"],
               remote_status=remote, remote_status_provenance=prov,
               description=desc, source="golden_set:html",
               source_type="golden_set", source_url=p["url"], canonical_url=p["url"])


FETCHERS = {"ashby": fetch_ashby, "greenhouse": fetch_greenhouse,
            "uber": fetch_uber, "html": fetch_html}


def main():
    out = []
    for num, tier, reason, method, p in ENTRIES:
        try:
            job = FETCHERS[method](p)
        except Exception as e:
            print(f"{num:>2} FAILED {p.get('co')}: {type(e).__name__}: {e}")
            continue
        rec = job.model_dump()
        rec["expected_tier"] = tier
        rec["label_reason"] = reason
        out.append(rec)
        print(f"{num:>2} ok  {job.company:<12} {job.title[:55]:<57} [{tier}] "
              f"desc={len(job.description)}ch")
    path = config.ROOT / "golden_set.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in out) + "\n", encoding="utf-8")
    print(f"\nwrote {len(out)}/{len(ENTRIES)} records -> {path}")


if __name__ == "__main__":
    main()
