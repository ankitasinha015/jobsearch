"""Web dashboard route tests — TestClient against a temp DB, stubbed LLM."""
import pytest
from conftest import make_job
from fastapi.testclient import TestClient

import app_web
from radar import db
from radar.models import LLM_DIMENSIONS


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "web.db")
    c = db.connect()
    job = make_job()
    db.upsert_job(c, job)
    dims = {k: 9 for k in LLM_DIMENSIONS}
    dims["posting_freshness"] = 10
    db.save_evaluation(c, "ck1", job.job_key, dims, 88.0, "excellent",
                       ["matches her clinical AI work", "remote US"],
                       ["sponsorship unconfirmed"], "high", "strongly_review", "v5")
    c.commit()
    c.close()
    return TestClient(app_web.app), job.job_key


def test_index_renders_feed(client):
    tc, _ = client
    r = tc.get("/")
    assert r.status_code == 200
    assert "Excellent matches" in r.text
    assert "Senior Product Manager, AI Platform" in r.text
    assert "sponsorship unconfirmed" in r.text


def test_disposition_roundtrip(client):
    tc, key = client
    r = tc.post(f"/disposition/{key}", data={"status": "dismissed", "reason": "wrong location"})
    assert r.status_code == 200
    assert "Dismissed (1)" in r.text          # moved to bucket
    assert "Excellent matches" not in r.text  # left the fresh feed
    r = tc.post(f"/disposition/{key}", data={"status": "restore"})
    assert "Excellent matches" in r.text


def test_disposition_rejects_bad_status(client):
    tc, key = client
    assert tc.post(f"/disposition/{key}", data={"status": "hacked"}).status_code == 400


def test_scan_status_and_trigger_respects_lock(client, monkeypatch):
    # Patch the scan body, NOT threading.Thread — TestClient itself runs on
    # threads, so a global Thread stub deadlocks the whole suite.
    import time
    tc, _ = client
    started = []
    monkeypatch.setattr(app_web, "_run_scan", lambda: started.append(1))
    c = db.connect()
    db.acquire_scan_lock(c)
    c.close()
    r = tc.post("/scan")
    assert r.status_code == 200 and not started  # lock held -> no scan started
    c = db.connect()
    db.release_scan_lock(c)
    c.close()
    tc.post("/scan")
    for _ in range(50):  # let the daemon thread run the stub
        if started:
            break
        time.sleep(0.05)
    assert started  # lock free -> scan ran


def test_tune_apply_validates_yaml_and_expires_token(client, tmp_path, monkeypatch):
    tc, _ = client
    from radar import config
    monkeypatch.setattr(config, "ROOT", tmp_path)
    app_web._tune_proposals["tok1"] = "valid: yes\n"
    r = tc.post("/tune/apply", data={"token": "tok1"})
    assert r.status_code == 200
    assert (tmp_path / "preferences.yaml").read_text(encoding="utf-8") == "valid: yes\n"
    # token consumed
    assert tc.post("/tune/apply", data={"token": "tok1"}).status_code == 410
    # invalid yaml never lands
    app_web._tune_proposals["tok2"] = "bad: [unclosed"
    with pytest.raises(Exception):
        tc.post("/tune/apply", data={"token": "tok2"})
    assert (tmp_path / "preferences.yaml").read_text(encoding="utf-8") == "valid: yes\n"
