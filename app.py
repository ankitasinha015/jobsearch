"""Job Radar dashboard — ranked feed, save/dismiss, Tune box, manual scan.

Run: streamlit run app.py
"""
import difflib
import json
import subprocess
import sys

import streamlit as st

from radar import config, db

config.bootstrap_env()

st.set_page_config(page_title="Job Radar", page_icon="📡", layout="wide")

DISMISS_REASONS = [
    "too junior", "too senior", "wrong product domain", "wrong industry",
    "wrong location", "not truly remote", "compensation too low",
    "company not interesting", "responsibilities not appealing",
    "missing required qualification", "duplicate", "stale or expired", "other"]

TIER_LABELS = {"excellent": "Excellent matches", "strong": "Strong matches",
               "possible": "Possible matches"}


@st.cache_resource
def get_conn():
    return db.connect()


conn = get_conn()

# ---------- header ----------
last = conn.execute(
    "SELECT * FROM scan_runs ORDER BY id DESC LIMIT 1").fetchone()
st.title("Job Radar")
if last is None:
    st.info("No scans yet. Run one below or: python -m radar.pipeline")
else:
    errors = json.loads(last["errors"] or "[]")
    if last["status"] == "failed":
        st.error(f"LAST SCAN FAILED — 0 of {last['sources_attempted']} sources "
                 f"succeeded ({last['started_at']}). The feed below may be stale.")
    else:
        line = (f"Last scan {last['completed_at'] or last['started_at']} — "
                f"{last['sources_succeeded']}/{last['sources_attempted']} sources, "
                f"{last['raw_count']} raw, {last['new_count']} new, "
                f"{last['scored_count']} scored")
        if errors:
            line += f", {len(errors)} source errors"
        st.caption(line)
        if errors:
            with st.expander(f"Source errors ({len(errors)})"):
                for e in errors:
                    st.text(e)

scan_locked = db.scan_in_progress(conn)
col_a, col_b = st.columns([1, 5])
with col_a:
    if st.button("Run scan now", disabled=scan_locked,
                 help="Disabled while a scan is running"):
        with st.spinner("Scanning (this can take several minutes)..."):
            subprocess.run([sys.executable, "-m", "radar.pipeline", "--no-jobspy"],
                           cwd=config.ROOT, timeout=3600)
        st.rerun()
if scan_locked:
    st.caption("A scan is currently running.")

# ---------- feed ----------
items = db.feed(conn)
fresh = [i for i in items if i["disposition"] is None]
saved = [i for i in items if i["disposition"] == "saved"]
applied = [i for i in items if i["disposition"] == "applied"]
dismissed = [i for i in items if i["disposition"] == "dismissed"]


def job_card(item, key_prefix=""):
    job = item["job"]
    key = item["job_key"]
    salary = ""
    if job.salary_min or job.salary_max:
        lo = f"{job.salary_min:,}" if job.salary_min else "?"
        hi = f"{job.salary_max:,}" if job.salary_max else "?"
        salary = f" · {lo}–{hi} {job.currency or ''}"
    remote = job.remote_status
    if job.remote_status_provenance == "inferred":
        remote += " (inferred)"
    with st.container(border=True):
        left, right = st.columns([4, 1])
        with left:
            st.markdown(f"**{job.title}** — {job.company}")
            st.caption(f"{job.location} · {remote}{salary} · "
                       f"score {item['overall']} ({item['tier']}) · "
                       f"confidence {item['confidence']} · first seen {item['first_seen_at'][:10]}")
            st.markdown("**Why it matches**")
            for r in item["reasons"]:
                st.markdown(f"- {r}")
            if item["concerns"]:
                st.markdown("**Potential concerns**")
                for c in item["concerns"]:
                    st.markdown(f"- {c}")
            with st.expander("Score breakdown & description"):
                st.json(item["dimension_scores"])
                st.text(job.description[:4000])
        with right:
            st.link_button("Open posting", job.canonical_url or job.source_url,
                           use_container_width=True)
            if item["disposition"] is None:
                if st.button("Save", key=f"{key_prefix}save-{key}", use_container_width=True):
                    db.set_disposition(conn, key, "saved")
                    st.rerun()
                reason = st.selectbox("Dismiss reason", DISMISS_REASONS,
                                      key=f"{key_prefix}reason-{key}",
                                      label_visibility="collapsed")
                if st.button("Dismiss", key=f"{key_prefix}dis-{key}", use_container_width=True):
                    db.set_disposition(conn, key, "dismissed", reason)
                    st.rerun()
            else:
                st.caption(f"{item['disposition']}"
                           + (f": {item['disposition_reason']}" if item["disposition_reason"] else ""))
                if item["disposition"] == "saved":
                    if st.button("Mark applied", key=f"{key_prefix}app-{key}",
                                 use_container_width=True):
                        db.set_disposition(conn, key, "applied")
                        st.rerun()
                if st.button("Restore", key=f"{key_prefix}res-{key}", use_container_width=True):
                    db.set_disposition(conn, key, None)
                    st.rerun()


shown = 0
for tier in ("excellent", "strong", "possible"):
    tier_items = [i for i in fresh if i["tier"] == tier]
    if not tier_items:
        continue
    st.header(f"{TIER_LABELS[tier]} ({len(tier_items)})")
    for item in tier_items:
        job_card(item)
        shown += 1
if shown == 0 and last is not None and last["status"] != "failed":
    st.info("No new excellent/strong/possible matches right now.")

for label, bucket in (("Saved", saved), ("Applied", applied), ("Dismissed", dismissed)):
    if bucket:
        with st.expander(f"{label} ({len(bucket)})"):
            for item in bucket:
                job_card(item, key_prefix=label.lower())

# ---------- tune box ----------
st.divider()
st.subheader("Tune the radar")
st.caption("Plain English, e.g. “stop showing NYC roles entirely” or "
           "“I care more about healthcare than dev tools”. You approve every change.")
feedback = st.text_area("Feedback", key="tune_text", label_visibility="collapsed")
if st.button("Propose preferences update", disabled=not feedback.strip()):
    import anthropic
    client = anthropic.Anthropic()
    current = config.preferences_text()
    resp = client.messages.create(
        model=config.load_weights()["scoring"]["model"], max_tokens=2500,
        system=("You maintain a job-search preferences.yaml. Apply the user's "
                "feedback as a minimal edit. Output ONLY the complete updated "
                "YAML file, no fences, no commentary. Preserve comments and "
                "structure. Never delete unrelated sections."),
        messages=[{"role": "user",
                   "content": f"Current preferences.yaml:\n{current}\n\nFeedback: {feedback}"}])
    proposed = "".join(b.text for b in resp.content if b.type == "text").strip()
    if proposed.startswith("```"):
        proposed = proposed.strip("`").lstrip("yaml").strip()
    st.session_state["proposed_prefs"] = proposed

if "proposed_prefs" in st.session_state:
    proposed = st.session_state["proposed_prefs"]
    current = config.preferences_text()
    diff = "\n".join(difflib.unified_diff(
        current.splitlines(), proposed.splitlines(),
        "current", "proposed", lineterm=""))
    st.code(diff or "(no change proposed)", language="diff")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Approve — apply and rescore on next scan", type="primary"):
            import yaml
            yaml.safe_load(proposed)  # parse before write — invalid YAML never lands
            (config.ROOT / "preferences.yaml").write_text(proposed, encoding="utf-8")
            del st.session_state["proposed_prefs"]
            st.success("Applied. Active jobs rescore on the next scan "
                       "(dismissed jobs stay dismissed).")
            st.rerun()
    with c2:
        if st.button("Reject"):
            del st.session_state["proposed_prefs"]
            st.rerun()
