"""Environment + config loading. Sets the Norton TLS bundle before any HTTPS."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CA_BUNDLE = r"C:\Users\ankit\certs\cacert.pem"

# Personal data (radar.db, profile.md, preferences.yaml) lives in DATA_DIR.
# Locally that's the repo folder (gitignored files); in the cloud it's a
# persistent disk (RADAR_DATA_DIR=/data) because these files are never in git.
DATA_DIR = Path(os.environ.get("RADAR_DATA_DIR", str(ROOT)))


def _data_file(name: str) -> Path:
    p = DATA_DIR / name
    return p if p.exists() else ROOT / name


def configured() -> bool:
    """True when the scorer's personal inputs exist."""
    return _data_file("profile.md").exists() and _data_file("preferences.yaml").exists()


def bootstrap_env() -> None:
    """Set TLS bundle + API key. Call before importing anthropic/requests users."""
    if os.path.exists(CA_BUNDLE):
        os.environ["REQUESTS_CA_BUNDLE"] = CA_BUNDLE
        os.environ["SSL_CERT_FILE"] = CA_BUNDLE
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def load_weights() -> dict:
    return json.loads((ROOT / "weights.json").read_text(encoding="utf-8"))


def load_companies() -> list[dict]:
    data = yaml.safe_load((ROOT / "companies.yaml").read_text(encoding="utf-8"))
    return data["companies"]


def preferences_text() -> str:
    p = _data_file("preferences.yaml")
    return p.read_text(encoding="utf-8") if p.exists() else ""


def profile_text() -> str:
    p = _data_file("profile.md")
    return p.read_text(encoding="utf-8") if p.exists() else ""


def save_preferences(text: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "preferences.yaml").write_text(text, encoding="utf-8")


def save_profile(text: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "profile.md").write_text(text, encoding="utf-8")


def prefs_hash() -> str:
    return hashlib.sha256(preferences_text().encode()).hexdigest()[:12]


def profile_hash() -> str:
    return hashlib.sha256(profile_text().encode()).hexdigest()[:12]
