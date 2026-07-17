# Job Radar — Project Instructions

Single-user personal job-discovery radar for Ankita's PM job search.
**PRD.md** is the product vision (full scope). **BUILDSPEC.md** is the approved,
eng-reviewed v1 design — when they disagree, BUILDSPEC.md wins for v1.

## What this is

Borrowed discovery, built matcher. Fetch PM job listings from public ATS JSON APIs
(Greenhouse/Lever/Ashby via companies.yaml) + JobSpy (supplementary only), normalize,
dedupe, hard-filter, then LLM-score each new listing against profile.md +
preferences.yaml with evidence-cited reasons and concerns. SQLite + Streamlit
ranked feed with save/dismiss and a natural-language Tune box.

## Stack

Python + SQLite (WAL mode) + Streamlit. Anthropic API for scoring (structured
output). Libraries: python-jobspy, rapidfuzz, pyyaml, pytest. Windows Task
Scheduler runs the daily scan.

## Environment (critical, verified 2026-07-16)

- **Norton TLS interception breaks Python HTTPS by default.** The app MUST set
  `REQUESTS_CA_BUNDLE=C:\Users\ankit\certs\cacert.pem` at startup (bundle already
  exists; verified against all three ATS APIs). Do NOT use `truststore` (RecursionError
  under anaconda Python) and NEVER `verify=False`.
- curl in shells needs `--ssl-no-revoke` (anaconda schannel curl).
- Ashby API is **GET** `api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true`
  — POST returns 401.
- Greenhouse `content` is HTML-ESCAPED HTML: `html.unescape` then strip tags before
  hashing or scoring.

## Key design rules (do not violate)

- LLM outputs per-dimension 0-10 scores + evidence only. Python computes the
  weighted 0-100 overall and maps tier via half-open bands in weights.json
  (Excellent [85,100], Strong [75,85), Possible [60,75), Weak [40,60), hidden <40).
- Evaluation cache key: (content_hash, prompt_version, hash(preferences.yaml),
  hash(profile.md)). weights.json changes = Python recompute only, no LLM re-call.
- Never invent missing fields — unknown stays unknown; inferred values labeled
  `inferred`, stated values labeled `stated`.
- Hard filters are deterministic Python, separate from ranking. Rejected rows kept
  in DB with filter_reason.
- Prompt-cache the shared prefix (profile + preferences + rubric).
  max_llm_calls_per_run caps each scan, freshest postings first; first run scores
  only postings ≤30 days old.
- Near-dup: rapidfuzz ≥90, compared only new-vs-active within the same normalized
  company.
- Source-failure semantics: a failed source fetch NEVER counts toward a job's
  absence counter (3 consecutive absences on successful scans → possibly_removed).
  Zero successful sources → scan status=failed + dashboard banner.
- One scan-in-progress lock; the Streamlit manual-scan button is disabled while held.
- Tune box: LLM proposes a preferences.yaml diff; user approves before write;
  approval invalidates cached evaluations for active jobs only (dismissed stay
  dismissed).

## Build order (from BUILDSPEC.md Next Steps)

1. golden_set.jsonl — 15 hand-labeled postings in the normalized schema (5 great /
   5 borderline / 5 wrong) BEFORE any pipeline code.
2. profile.md + preferences.yaml + weights.json.
3. score.py + eval script → iterate until ≥12/15 tier agreement with the labels.
4. fetch.py → normalize.py → dedupe.py → filters.py.
5. SQLite schema + app.py (feed, save/dismiss, Tune box).
6. Task Scheduler daily scan ("run as soon as possible after a missed start") →
   two-week trial.

## Testing

Full pytest suite written alongside the code (see BUILDSPEC.md Test Strategy):
recorded per-ATS JSON fixtures in tests/fixtures/, unit tests for dedupe/filters/
scoring-math/cache/cap, an E2E pipeline test with a stubbed LLM, and the golden-set
eval as the quality gate. Run: `pytest`.

## Compliance guardrails (PRD non-goals stand)

No auto-apply, no LinkedIn scraping, no anti-bot evasion, no login-gated sources.
JobSpy is a labeled best-effort exception (public pages, no login); if it gets
blocked the radar must run on ATS sources alone.

## Repo hygiene

profile.md, preferences.yaml, golden_set.jsonl, radar.db, and .env are gitignored
(they contain resume-derived personal data). Secrets never in source control.

## Open items to confirm before building on them

- D1 (recommended 1A): app sets REQUESTS_CA_BUNDLE itself at startup — treat as
  decided unless Ankita objects.
- D4 (recommended 4A): single pydantic Job model in models.py validated at
  normalize output, golden_set load, and score input; SQLite schema derived from it.
