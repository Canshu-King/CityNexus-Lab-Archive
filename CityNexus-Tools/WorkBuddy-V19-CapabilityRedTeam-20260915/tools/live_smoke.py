"""Smoke-test the live DeepSeek semantic compiler (never prints the key)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
sys.path.insert(0, str(LAB / "repo_copy" / "backend"))

from app.integrations.ai.responses import DeepSeekResponsesClient  # noqa: E402
from app.integrations.ai.semantic_compiler import (  # noqa: E402
    apply_semantic_policy,
    compile_semantic_envelope,
)

key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("CITYNEXUS_AI_API_KEY")
if not key:
    # Reuse the existing Windows User-scope credential from inside the child
    # process only.  The value is never printed or persisted.
    try:
        import winreg  # noqa: PLC0415

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as handle:
            key, _ = winreg.QueryValueEx(handle, "DEEPSEEK_API_KEY")
    except OSError:
        key = None
lines = [f"key_present={bool(key)}"]
if key:
    client = DeepSeekResponsesClient(api_key=key, reasoning_effort="none", timeout_seconds=45.0)
    for text in ("必须全程无障碍，一步楼梯都不能走", "最好少走点楼梯", "我妈以前膝盖不好，现在好了"):
        try:
            envelope = compile_semantic_envelope(client, text, {"city_code": "CNX-DEMO"})
            decision = apply_semantic_policy(envelope) if envelope else None
            lines.append(
                json.dumps(
                    {
                        "text": text,
                        "envelope": envelope.as_dict() if envelope else None,
                        "policy": decision.__dict__ if decision else None,
                    },
                    ensure_ascii=False,
                )[:700]
            )
        except Exception as exc:  # noqa: BLE001
            lines.append(f"ERR {type(exc).__name__}: {str(exc)[:300]}")

(LAB / "_live_smoke.txt").write_text("\n".join(lines), encoding="utf-8")
print("done")
