"""Pull all live jobs from verified companies.yaml boards; inventory PM-ish titles.

Output: scripts/pm_title_inventory.txt (company | title | location | url)
Run: python scripts/pull_pm_titles.py
"""
import os
import re
import sys

os.environ.setdefault("REQUESTS_CA_BUNDLE", r"C:\Users\ankit\certs\cacert.pem")
import requests  # noqa: E402
import yaml  # noqa: E402

HERE = os.path.dirname(__file__)
PM_RE = re.compile(
    r"product (manager|lead|management)|director,? product|head of product"
    r"|product strategy|forward deployed", re.I,
)

S = requests.Session()
S.headers["User-Agent"] = "job-radar-setup/0.1 (personal job search tool)"


def fetch(ats, slug):
    """Yield (title, location, url) for every live job on the board."""
    try:
        if ats == "greenhouse":
            r = S.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", timeout=15)
            for j in r.json().get("jobs", []):
                yield j["title"], (j.get("location") or {}).get("name", "?"), j["absolute_url"]
        elif ats == "lever":
            r = S.get(f"https://api.lever.co/v0/postings/{slug}?mode=json", timeout=15)
            for j in r.json():
                loc = (j.get("categories") or {}).get("location") or "?"
                yield j["text"], loc, j["hostedUrl"]
        elif ats == "ashby":
            r = S.get(
                f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true",
                timeout=15,
            )
            for j in r.json().get("jobs", []):
                yield j["title"], j.get("location", "?"), j.get("jobUrl") or j.get("applyUrl", "?")
    except Exception as e:
        print(f"  !! {slug}: {type(e).__name__}", file=sys.stderr)


def main():
    with open(os.path.join(HERE, "..", "companies.yaml"), encoding="utf-8") as f:
        companies = yaml.safe_load(f)["companies"]
    total = pm = 0
    rows = []
    for c in companies:
        for title, loc, url in fetch(c["ats"], c["slug"]):
            total += 1
            if PM_RE.search(title):
                pm += 1
                rows.append(f"{c['name']} | {title} | {loc} | {url}")
    out = os.path.join(HERE, "pm_title_inventory.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(rows)) + "\n")
    print(f"boards={len(companies)} total_jobs={total} pm_titled={pm} -> {out}")


if __name__ == "__main__":
    main()
