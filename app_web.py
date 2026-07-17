"""Job Radar web dashboard — FastAPI + HTMX, replaces the Streamlit app.

Run: python app_web.py   (serves http://127.0.0.1:8990)
"""
from __future__ import annotations

import difflib
import json
import subprocess
import sys
import threading

import yaml
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from radar import config, db

config.bootstrap_env()

app = FastAPI(title="Job Radar")
app.mount("/static", StaticFiles(directory=str(config.ROOT / "static")), name="static")
templates = Jinja2Templates(directory=str(config.ROOT / "templates"))

DISMISS_REASONS = [
    "too junior", "too senior", "wrong product domain", "wrong industry",
    "wrong location", "not truly remote", "compensation too low",
    "company not interesting", "responsibilities not appealing",
    "missing required qualification", "duplicate", "stale or expired", "other"]

TIERS = [("excellent", "Excellent matches"), ("strong", "Strong matches"),
         ("possible", "Possible matches")]

_tune_proposals: dict[str, str] = {}


def conn():
    return db.connect()


def feed_context(request: Request) -> dict:
    c = conn()
    last = c.execute("SELECT * FROM scan_runs ORDER BY id DESC LIMIT 1").fetchone()
    items = db.feed(c)
    fresh = [i for i in items if i["disposition"] is None]
    sections = [(key, label, [i for i in fresh if i["tier"] == key])
                for key, label in TIERS]
    buckets = {name: [i for i in items if i["disposition"] == name]
               for name in ("saved", "applied", "dismissed")}
    ctx = {
        "request": request,
        "sections": sections,
        "buckets": buckets,
        "reasons": DISMISS_REASONS,
        "scan_running": db.scan_in_progress(c),
        "last": dict(last) if last else None,
        "last_errors": json.loads(last["errors"] or "[]") if last else [],
        "fresh_count": len(fresh),
    }
    c.close()
    return ctx


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", feed_context(request))


@app.get("/scan/status", response_class=HTMLResponse)
def scan_status(request: Request):
    return templates.TemplateResponse(request, "_scanbar.html", feed_context(request))


def _run_scan():
    subprocess.run([sys.executable, "-m", "radar.pipeline", "--no-jobspy"],
                   cwd=config.ROOT, timeout=7200)


@app.post("/scan", response_class=HTMLResponse)
def start_scan(request: Request):
    c = conn()
    running = db.scan_in_progress(c)
    c.close()
    if not running:
        threading.Thread(target=_run_scan, daemon=True).start()
    return templates.TemplateResponse(request, "_scanbar.html", feed_context(request))


@app.post("/disposition/{job_key}", response_class=HTMLResponse)
def disposition(request: Request, job_key: str, status: str = Form(...),
                reason: str = Form(None)):
    if status not in ("saved", "dismissed", "applied", "restore"):
        raise HTTPException(400, "bad status")
    c = conn()
    db.set_disposition(c, job_key, None if status == "restore" else status, reason)
    c.close()
    # Return the whole feed body — sections shift when a card moves buckets.
    return templates.TemplateResponse(request, "_feed.html", feed_context(request))


@app.post("/tune/propose", response_class=HTMLResponse)
def tune_propose(request: Request, feedback: str = Form(...)):
    import anthropic
    import secrets
    client = anthropic.Anthropic()
    current = config.preferences_text()
    resp = client.messages.create(
        model=config.load_weights()["scoring"]["model"], max_tokens=2500,
        thinking={"type": "disabled"},
        system=("You maintain a job-search preferences.yaml. Apply the user's "
                "feedback as a minimal edit. Output ONLY the complete updated "
                "YAML file, no fences, no commentary. Preserve comments and "
                "structure. Never delete unrelated sections."),
        messages=[{"role": "user",
                   "content": f"Current preferences.yaml:\n{current}\n\nFeedback: {feedback}"}])
    proposed = "".join(b.text for b in resp.content if b.type == "text").strip()
    if proposed.startswith("```"):
        proposed = proposed.strip("`").lstrip("yaml").strip()
    token = secrets.token_hex(8)
    _tune_proposals[token] = proposed
    diff = "\n".join(difflib.unified_diff(
        current.splitlines(), proposed.splitlines(), "current", "proposed", lineterm=""))
    return templates.TemplateResponse(request, "_tunediff.html", {
        "diff": diff or "(no change proposed)", "token": token})


@app.post("/tune/apply", response_class=HTMLResponse)
def tune_apply(request: Request, token: str = Form(...)):
    proposed = _tune_proposals.pop(token, None)
    if proposed is None:
        raise HTTPException(410, "proposal expired")
    yaml.safe_load(proposed)  # parse before write — invalid YAML never lands
    (config.ROOT / "preferences.yaml").write_text(proposed, encoding="utf-8")
    return HTMLResponse(
        "<div class='tune-note ok'>Applied. Active jobs rescore on the next scan "
        "(dismissed jobs stay dismissed).</div>")


@app.post("/tune/reject", response_class=HTMLResponse)
def tune_reject(token: str = Form(...)):
    _tune_proposals.pop(token, None)
    return HTMLResponse("<div class='tune-note'>Rejected — preferences unchanged.</div>")


if __name__ == "__main__":
    import os

    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8990")))
