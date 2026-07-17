"""The matching brain. LLM rates 8 dimensions with evidence; Python computes
posting_freshness, the weighted 0-100 overall, and the tier (BUILDSPEC: the
LLM never assigns overall or tier).

Cost controls (eng review D2): the shared prefix (profile + preferences +
rubric) carries a cache_control breakpoint — the scan is a burst of calls, the
ideal caching shape. weights.json changes trigger Python recompute only.

Cache key: (content_hash, prompt_version, prefs_hash, profile_hash).
"""
from __future__ import annotations

import json
from datetime import date

from . import config
from .models import LLM_DIMENSIONS, Job, LLMEvaluation

RUBRIC = """You are the matching engine of a personal job radar for one specific
candidate. Rate how well ONE job posting fits HER, dimension by dimension.

Score each dimension 0-10 (0 = total mismatch, 10 = exceptional fit):
- functional_responsibility_match: does the day-to-day work resemble her
  demonstrated experience (product strategy, roadmap ownership, discovery,
  cross-functional leadership, 0->1, platform/enterprise work)?
- seniority_scope_match: years asked vs hers, IC-vs-management scope,
  ownership breadth. She targets Senior/Staff/Principal-level IC product roles.
- product_domain_match: AI/agentic products, healthcare tech, data/analytics,
  developer tools, enterprise platforms, civic tech.
- skills_experience_match: required + preferred qualifications vs her profile.
  Distinguish demonstrated vs transferable vs missing.
- location_work_arrangement: remote-US and SF-Bay-Area score highest; hybrid
  within her stated limits acceptable; NYC only for exceptional roles;
  ambiguous remote status scores mid, never high.
- industry_mission_match: company business and mission vs her preferences.
- compensation_match: stated comp vs her floor. Missing salary = score 5
  (reduces confidence, not the score — never invent numbers).
- company_stage_match: company stage/size vs her preferences.

Calibration principles (derived from her labeled ground truth — these matter
more than cautious instincts):
- Tiers map to her ACTIONS: 85+ = "drop everything, apply today";
  75-84 = "definitely applying this week"; 60-74 = "maybe, on a slow week";
  40-59 = "probably not"; below 40 = never show.
- She applies on DOMAIN + COMPANY PULL. If the product domain is squarely in
  her lanes (AI/agentic, healthcare tech INCLUDING consumer/member-facing
  healthcare AI at scale — her clinical background transfers, data platforms,
  dev tools) AND the
  level is senior IC AND the location works (remote US or Bay Area), the role
  belongs at excellent/strong. Score dimensions with clear positive evidence
  8-10; use 5-7 for partial fits; reserve 0-4 for genuine mismatch.
- THE COMMON FAILURE MODE IS UNDER-SCORING roles she would apply to today.
  When domain + senior-IC level + location all hit and no major disqualifier
  exists, functional_responsibility_match, product_domain_match, and
  skills_experience_match belong at 9-10, not 7-8 — "apply today" means the
  weighted total must reach 85+.
- Strong AI-company pull: enterprise-AI and agentic-AI companies (data/AI
  platforms, AI labs, enterprise AI products) are apply-this-week (75+)
  whenever level and location fit — including function-adjacent roles there
  (growth, consumer): score those functional dimensions 7-8, not 4-5.
- Do NOT over-penalize stated qualification gaps. "10+ years", consumer-vs-B2B
  background, or a missing sub-niche are CONCERNS to list, but together they
  should cost at most one tier — she has 12 years total (6+ PM on top of
  engineering) and applies anyway.
- DREAM COMPANIES (Google, Intuitive, Uber): any US product role at PM II
  level or above is a direct target — "definitely applying this week" (75+).
  industry_mission_match and company_stage_match 9-10; functional and skills
  dimensions generously (8+) on transferable strengths — she will close gaps;
  never score seniority low just because the title band is mid-level.
- NYC-ONLY roles (no SF or remote option): location_work_arrangement at most 4
  — great roles there land at possible, not strong.
- PEOPLE-MANAGEMENT scope (managing/mentoring PMs as the core job): she is a
  senior IC — functional_responsibility_match, seniority_scope_match, AND
  skills_experience_match at most 2, and product_domain_match at most 5 even
  when the domain is perfect: the job itself is one she cannot do as specced,
  so it must drop out of view (below 40).
- ADJACENT PM functions (growth, consumer) at companies in her lanes are
  transferable (6-8), not mismatches.
- Cite EVIDENCE: every reason must reference something specific in the posting
  AND something specific in her profile. Never write generic praise like
  "your skills are a good fit".
- reasons: AT MOST 4 items — pick only the most decisive connections.
- concerns: 0-3 real gaps, uncertainties, or constraints (missing required
  qualification, seniority mismatch, ambiguous remote policy...).
- confidence reflects DATA COMPLETENESS of the posting, not job quality:
  high = clear description+location+seniority (comp stated helps),
  medium = good description, some fields missing, low = sparse or ambiguous.
- recommendation: strongly_review | review | consider | low_priority.
- She REQUIRES employer visa sponsorship. Postings that explicitly exclude
  sponsorship never reach you (hard-filtered upstream). If the posting hints at
  work-authorization restrictions (citizenship preference, clearance, export
  control, "must be authorized to work in the US" without mentioning
  sponsorship), list it as a concern. If sponsorship is explicitly offered,
  that is a real plus worth a reason.
- If information is missing, say it is missing. Never invent.

Respond with ONLY a JSON object, no markdown fences:
{"dimension_scores": {"functional_responsibility_match": 0-10, ...all 8 keys...},
 "reasons": ["...", "..."], "concerns": ["..."],
 "confidence": "high|medium|low",
 "recommendation": "strongly_review|review|consider|low_priority"}
"""


def freshness_score(date_posted: str | None, today: date | None = None) -> int:
    """Mechanical freshness (PRD: small advantage, never overpowers fit)."""
    if not date_posted:
        return 5  # unknown stays neutral
    try:
        posted = date.fromisoformat(date_posted[:10])
    except ValueError:
        return 5
    days = ((today or date.today()) - posted).days
    if days <= 7:
        return 10
    if days <= 14:
        return 7
    if days <= 30:
        return 4
    return 2


def compute_overall(dims: dict[str, int], weights: dict) -> float:
    """Deterministic weighted sum. Weights are normalized so overall is 0-100."""
    w = weights["weights"]
    total_w = sum(w.values())
    return round(sum(w[k] * dims[k] / 10 for k in w) * 100 / (10 * total_w) * 10, 1)


def tier_for(overall: float, weights: dict) -> str:
    """Half-open bands from weights.json: [min, max)."""
    bands = weights["tier_bands"]
    for name in ("excellent", "strong", "possible", "weak"):
        lo, hi = bands[name]
        if lo <= overall < hi:
            return name
    return "hidden"


BAY_OR_REMOTE_RE = None  # compiled lazily below
_BAY_MARKERS = ("san francisco", "sunnyvale", "mountain view", "oakland",
                "palo alto", "san jose", "bay area", "remote")


def nyc_cap(overall: float, location: str) -> tuple[float, bool]:
    """Her rule: NYC-only roles are 'exceptional matches only' — never above
    possible. Deterministic (the LLM applied it unevenly)."""
    loc = (location or "").lower()
    if "new york" in loc and not any(m in loc for m in _BAY_MARKERS):
        if overall >= 75:
            return 74.0, True
    return overall, False


def dream_boost(overall: float, company: str) -> tuple[float, bool]:
    """Deterministic +5 for dream companies (preferences.yaml) — company pull
    is a stated user rule, so it lives in code, not in LLM judgment."""
    import yaml
    prefs = yaml.safe_load(config.preferences_text()) or {}
    dreams = [c.lower() for c in (prefs.get("dream_companies") or [])]
    if company.lower() in dreams:
        return min(100.0, round(overall + 5, 1)), True
    return overall, False


def cache_key(job: Job, weights: dict) -> str:
    return "|".join([
        job.content_hash,
        weights["scoring"]["prompt_version"],
        config.prefs_hash(),
        config.profile_hash(),
    ])


def build_system_blocks() -> list[dict]:
    """Shared prefix, cache_control on the last stable block (prompt caching)."""
    return [{
        "type": "text",
        "text": (RUBRIC
                 + "\n\n=== CANDIDATE PROFILE ===\n" + config.profile_text()
                 + "\n\n=== CANDIDATE PREFERENCES ===\n" + config.preferences_text()),
        "cache_control": {"type": "ephemeral"},
    }]


def job_prompt(job: Job) -> str:
    payload = job.model_dump(include={
        "title", "company", "location", "remote_status", "remote_status_provenance",
        "employment_type", "salary_min", "salary_max", "currency", "date_posted"})
    payload["description"] = job.description[:12000]
    return "Job posting to evaluate:\n" + json.dumps(payload, indent=1)


def evaluate_job(client, job: Job, weights: dict, system_blocks: list[dict]) -> dict:
    """One LLM call -> validated evaluation + deterministic overall/tier.

    Raises on unrecoverable failure after retries (caller logs and skips).
    """
    scoring = weights["scoring"]
    last_err: Exception | None = None
    for _ in range(scoring["max_retries_per_listing"] + 1):
        resp = client.messages.create(
            model=scoring["model"],
            max_tokens=2000,
            # Sonnet 5 defaults to adaptive thinking, which spends from
            # max_tokens and can leave the JSON truncated or empty. Rating
            # dimensions against a rubric is deterministic — thinking off.
            thinking={"type": "disabled"},
            system=system_blocks,
            messages=[{"role": "user", "content": job_prompt(job)}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        if text.startswith("```"):
            text = text.strip("`").lstrip("json").strip()
        try:
            data = json.loads(text)
            # Clamp over-long lists instead of failing — the model tends to
            # over-explain; keeping the first (strongest) items is faithful
            # to the PRD's 2-4 reasons / 0-3 concerns format.
            if isinstance(data.get("reasons"), list):
                data["reasons"] = data["reasons"][:4]
            if isinstance(data.get("concerns"), list):
                data["concerns"] = data["concerns"][:3]
            ev = LLMEvaluation.model_validate(data)
            break
        except Exception as e:  # malformed output -> retry then skip-with-log
            last_err = e
    else:
        raise ValueError(f"unparseable evaluation for {job.title}: {last_err}")

    dims = {k: int(ev.dimension_scores[k]) for k in LLM_DIMENSIONS}
    dims["posting_freshness"] = freshness_score(job.date_posted)
    overall = compute_overall(dims, weights)
    overall, boosted = dream_boost(overall, job.company)
    if boosted:
        ev.reasons = (ev.reasons + ["Dream-company boost applied (+5)"])[:4]
    overall, capped = nyc_cap(overall, job.location)
    if capped:
        ev.concerns = (ev.concerns + ["NYC-only location (capped at possible per preferences)"])[:3]
    return {
        "dimension_scores": dims,
        "overall": overall,
        "tier": tier_for(overall, weights),
        "reasons": ev.reasons,
        "concerns": ev.concerns,
        "confidence": ev.confidence,
        "recommendation": ev.recommendation,
    }
