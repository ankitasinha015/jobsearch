"""Per-ATS normalization into the Job schema (eng review D3 rules).

- Greenhouse: `content` is HTML-ESCAPED HTML — unescape then strip tags.
- Lever: description = descriptionPlain + lists[] assembled.
- Ashby: descriptionPlain, isRemote, compensation come directly.
- Remote status chain: structured field -> title/location regex -> unknown
  (LLM may refine later); every value labeled stated|inferred|unknown (PRD §13.2).
- Unknown stays unknown — never invent fields.
"""
from __future__ import annotations

import html
import re

from .models import Job

TAG_RE = re.compile(r"<[^>]+>")
REMOTE_RE = re.compile(r"\bremote\b|\bwork from home\b|\bdistributed\b", re.I)
HYBRID_RE = re.compile(r"\bhybrid\b|\bdays? (in|per) (the )?office\b", re.I)


def strip_html(escaped_html: str) -> str:
    text = html.unescape(escaped_html or "")
    text = re.sub(r"</(p|div|li|ul|ol|h[1-6]|br)>", "\n", text, flags=re.I)
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = TAG_RE.sub(" ", text)
    text = html.unescape(text)  # entities that were double-encoded
    return re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", text)).strip()


def infer_remote(title: str, location: str, description: str) -> tuple[str, str]:
    """Rule chain on free text. Returns (status, provenance)."""
    blob_primary = f"{title} {location}"
    if REMOTE_RE.search(blob_primary):
        return "remote", "inferred"
    if HYBRID_RE.search(blob_primary):
        return "hybrid", "inferred"
    head = description[:600]
    if REMOTE_RE.search(head):
        return "remote", "inferred"
    if HYBRID_RE.search(head):
        return "hybrid", "inferred"
    return "unknown", "unknown"


def normalize_greenhouse(raw: dict, company: dict) -> Job:
    title = raw.get("title", "")
    location = (raw.get("location") or {}).get("name") or "unknown"
    description = strip_html(raw.get("content", ""))
    remote, prov = infer_remote(title, location, description)
    return Job(
        title=title, company=company["name"], location=location,
        remote_status=remote, remote_status_provenance=prov,
        description=description,
        date_posted=(raw.get("updated_at") or raw.get("first_published") or "")[:10] or None,
        source=f"greenhouse:{company['slug']}", source_type="ats", ats="greenhouse",
        source_url=raw.get("absolute_url", ""), canonical_url=raw.get("absolute_url", ""))


def normalize_lever(raw: dict, company: dict) -> Job:
    title = raw.get("text", "")
    cats = raw.get("categories") or {}
    location = cats.get("location") or "unknown"
    parts = [raw.get("descriptionPlain") or strip_html(raw.get("description", ""))]
    for lst in raw.get("lists") or []:
        parts.append(lst.get("text", ""))
        parts.append(strip_html(lst.get("content", "")))
    description = "\n".join(p for p in parts if p).strip()
    workplace = (raw.get("workplaceType") or "").lower()
    if workplace in ("remote", "hybrid"):
        remote, prov = workplace, "stated"
    elif workplace in ("onsite", "on-site"):
        remote, prov = "onsite", "stated"
    else:
        remote, prov = infer_remote(title, location, description)
    return Job(
        title=title, company=company["name"], location=location,
        remote_status=remote, remote_status_provenance=prov,
        description=description,
        employment_type=(cats.get("commitment") or "unknown"),
        date_posted=None,
        source=f"lever:{company['slug']}", source_type="ats", ats="lever",
        source_url=raw.get("hostedUrl", ""), canonical_url=raw.get("hostedUrl", ""))


def normalize_ashby(raw: dict, company: dict) -> Job:
    title = raw.get("title", "")
    location = raw.get("location") or "unknown"
    description = raw.get("descriptionPlain") or strip_html(raw.get("descriptionHtml", ""))
    if raw.get("isRemote") is True:
        remote, prov = "remote", "stated"
    elif raw.get("isRemote") is False:
        remote, prov = infer_remote(title, location, description)
        if remote == "unknown":
            remote, prov = "onsite", "stated"
    else:
        remote, prov = infer_remote(title, location, description)
    comp = raw.get("compensation") or {}
    salary_min = salary_max = currency = None
    for tier in (comp.get("summaryComponents") or []):
        if tier.get("compensationType") == "Salary":
            salary_min = int(tier["minValue"]) if tier.get("minValue") else None
            salary_max = int(tier["maxValue"]) if tier.get("maxValue") else None
            currency = tier.get("currencyCode")
            break
    return Job(
        title=title, company=company["name"], location=location,
        remote_status=remote, remote_status_provenance=prov,
        description=description,
        employment_type=(raw.get("employmentType") or "unknown"),
        salary_min=salary_min, salary_max=salary_max, currency=currency,
        date_posted=(raw.get("publishedAt") or "")[:10] or None,
        source=f"ashby:{company['slug']}", source_type="ats", ats="ashby",
        source_url=raw.get("jobUrl") or raw.get("applyUrl", ""),
        canonical_url=raw.get("jobUrl") or raw.get("applyUrl", ""))


NORMALIZERS = {
    "greenhouse": normalize_greenhouse,
    "lever": normalize_lever,
    "ashby": normalize_ashby,
}


def normalize_jobspy(raw: dict) -> Job:
    title = str(raw.get("title") or "")
    location = str(raw.get("location") or "unknown")
    description = str(raw.get("description") or "")
    if raw.get("is_remote") is True:
        remote, prov = "remote", "stated"
    else:
        remote, prov = infer_remote(title, location, description)
    def _num(v):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None
    return Job(
        title=title, company=str(raw.get("company") or "unknown"), location=location,
        remote_status=remote, remote_status_provenance=prov,
        description=description,
        salary_min=_num(raw.get("min_amount")), salary_max=_num(raw.get("max_amount")),
        currency=str(raw.get("currency")) if raw.get("currency") else None,
        date_posted=str(raw.get("date_posted"))[:10] if raw.get("date_posted") else None,
        source=f"jobspy:{raw.get('site', 'aggregator')}", source_type="aggregator",
        source_url=str(raw.get("job_url") or ""),
        canonical_url=str(raw.get("job_url_direct") or raw.get("job_url") or ""))
