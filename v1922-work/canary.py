"""One bounded live DeepSeek semantic canary.

Never prints or packages the API key.  If the credential is unavailable the
result is reported as LIVE_DEEPSEEK_CANARY_PENDING_PHYSICAL_TRIAL.
"""

from __future__ import annotations

import io
import json
import os
import sys
import winreg
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BACKEND = Path("D:/moodle/CityNexus/backend")
sys.path.insert(0, str(BACKEND))

OUT = Path("D:/moodle/_v1922_work/evidence_canary.json")


def load_key() -> str | None:
    key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("CITYNEXUS_AI_API_KEY")
    if key:
        return key
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as handle:
            value, _ = winreg.QueryValueEx(handle, "DEEPSEEK_API_KEY")
            return str(value) or None
    except OSError:
        return None


CANARY_INPUTS = [
    "I don't need a wheelchair, I can walk.",
    "I need step-free access for this trip.",
    "走路不能超过 1.5 公里。",
]

result: dict = {"canary": "LIVE_DEEPSEEK_CANARY", "inputs": [], "status": None}
key = load_key()
if not key:
    result["status"] = "LIVE_DEEPSEEK_CANARY_PENDING_PHYSICAL_TRIAL"
    result["reason"] = "no DEEPSEEK_API_KEY available in the environment"
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1))
    raise SystemExit(0)

os.environ["DEEPSEEK_API_KEY"] = key
os.environ["CITYNEXUS_AI_API_KEY"] = key
os.environ["CITYNEXUS_AI_ENABLED"] = "true"

from app.integrations.ai.responses import DeepSeekResponsesClient  # noqa: E402
from app.integrations.ai.semantic_compiler import (  # noqa: E402
    compile_semantic_envelope,
)
from app.capabilities import extract_capabilities_from_text  # noqa: E402

client = DeepSeekResponsesClient(api_key=key)

for message in CANARY_INPUTS:
    entry = {"input": message}
    try:
        envelope = compile_semantic_envelope(client, message, {"journey_id": None})
    except Exception as exc:  # noqa: BLE001
        entry["live_error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        envelope = None
    if envelope is not None:
        payload = envelope.as_dict() if hasattr(envelope, "as_dict") else (
            envelope.model_dump(mode="json") if hasattr(envelope, "model_dump") else dict(envelope)
        )
        caps = payload.get("capabilities") or []
        entry["live_capabilities"] = [
            {
                "code": item.get("code"),
                "severity": item.get("severity"),
                "params": item.get("params"),
            }
            for item in caps
        ]
        entry["live_assertion_status"] = payload.get("assertion_status")
    entry["local_fallback_capabilities"] = [
        {"code": item["code"], "severity": item["severity"], "params": item["params"]}
        for item in extract_capabilities_from_text(message)
    ]
    result["inputs"].append(entry)

ok = all("live_error" not in item for item in result["inputs"])
result["status"] = (
    "LIVE_DEEPSEEK_CANARY_PASSED" if ok else "LIVE_DEEPSEEK_CANARY_FAILED"
)
result["key_length_redacted"] = len(key)
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=1))
