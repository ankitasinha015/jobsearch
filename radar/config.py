"""Environment + config loading. Sets the Norton TLS bundle before any HTTPS."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CA_BUNDLE = r"C:\Users\ankit\certs\cacert.pem"


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
    return (ROOT / "preferences.yaml").read_text(encoding="utf-8")


def profile_text() -> str:
    return (ROOT / "profile.md").read_text(encoding="utf-8")


def prefs_hash() -> str:
    return hashlib.sha256(preferences_text().encode()).hexdigest()[:12]


def profile_hash() -> str:
    return hashlib.sha256(profile_text().encode()).hexdigest()[:12]
