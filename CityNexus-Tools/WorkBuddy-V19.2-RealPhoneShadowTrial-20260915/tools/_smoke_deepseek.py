"""Smoke: is the DeepSeek credential present and reachable from this sandbox?

Never prints the credential.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915")
SNAP = LAB / "snapshot_a"
sys.path.insert(0, str(SNAP / "backend"))

os.environ.setdefault("CITYNEXUS_DATABASE_URL", f"sqlite:///{LAB / 'evidence' / '_db' / 'semantic_probe.db'}")
os.environ.setdefault("CITYNEXUS_ENV", "test")


def credential() -> str | None:
    for name in ("DEEPSEEK_API_KEY", "CITYNEXUS_AI_API_KEY"):
        value = os.getenv(name)
        if value:
            return value
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as handle:
            value, _ = winreg.QueryValueEx(handle, "DEEPSEEK_API_KEY")
            return str(value) or None
    except OSError:
        return None


key = credential()
print(f"credential_present={bool(key)}")
if not key:
    raise SystemExit(2)

from app.integrations.ai.responses import DeepSeekResponsesClient  # noqa: E402
from app.integrations.ai.semantic_compiler import (  # noqa: E402
    compile_semantic_envelope,
)

client = DeepSeekResponsesClient(
    api_key=key,
    model=os.getenv("CITYNEXUS_AI_MODEL", "deepseek-v4-flash"),
    base_url=os.getenv("CITYNEXUS_DEEPSEEK_API_URL", "https://api.deepseek.com/responses"),
    reasoning_effort="none",
    timeout_seconds=45.0,
)

CONTEXT = {
    "journey_id": "22222222-2222-4222-8222-222222222222",
    "city_code": "CNX-DEMO",
    "timezone": "Asia/Shanghai",
    "status": "DRAFT",
    "protected_commitments": [],
    "preferences": [],
    "known_venue_accessibility_evidence": [],
}

try:
    env = compile_semantic_envelope(client, "我妈妈用轮椅，必须全程无障碍", CONTEXT)
    print("LIVE_OK")
    print(f"intent={getattr(env, 'intent', None)} assertion={getattr(env, 'assertion_status', None)}")
except Exception as exc:  # noqa: BLE001
    print(f"LIVE_FAILED {type(exc).__name__}: {str(exc)[:300]}")
