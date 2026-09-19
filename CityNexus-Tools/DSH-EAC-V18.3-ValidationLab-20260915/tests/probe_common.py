"""Shared helpers for DSH-EAC V18.3 live validation streams.

All HTTP goes through a proxy-disabled client so localhost (:8022) is not
routed through the environment HTTP_PROXY. Never logs or persists credentials.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
LAB_DATA = WORKSPACE / "lab-data"
EVIDENCE = WORKSPACE / "evidence"
BASE = "http://127.0.0.1:8022"
HERMES_BASE = "http://127.0.0.1:8653"

# Force direct connections (bypass corporate/env proxy for localhost).
os.environ.setdefault("no_proxy", "127.0.0.1,localhost")
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)


def get_scenario() -> dict:
    return json.loads((LAB_DATA / "scenario.json").read_text(encoding="utf-8"))


def client() -> "httpx.Client":
    import httpx

    return httpx.Client(base_url=BASE, timeout=httpx.Timeout(20.0, read=900.0), trust_env=False)


def hermes_client() -> "httpx.Client":
    import httpx

    key = (LAB_DATA / "hermes_lab_api_key.txt").read_text(encoding="utf-8").strip()
    return httpx.Client(
        base_url=HERMES_BASE,
        timeout=httpx.Timeout(20.0, read=900.0),
        trust_env=False,
        headers={"Authorization": f"Bearer {key}"},
    )


def record_jsonl(name: str, record: dict) -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with (EVIDENCE / name).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
