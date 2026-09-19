"""Probe the isolated V19 runtime to learn the real request/response shapes."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
os.environ.setdefault("CITYNEXUS_DATABASE_URL", f"sqlite:///{LAB / 'v19_probe2.db'}")
sys.path.insert(0, str(LAB / "repo_copy" / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

import app.main as main_module  # noqa: E402

client = TestClient(main_module.app)
out: dict[str, object] = {}

r = client.post("/api/v1/demo/reset")
out["demo_reset"] = {"status": r.status_code, "body": r.json() if r.status_code == 200 else r.text[:400]}
jid = r.json().get("journey_id") if r.status_code == 200 else None

if jid:
    r = client.get(f"/api/v1/journeys/{jid}")
    out["journey"] = {"status": r.status_code, "body": r.json() if r.status_code == 200 else r.text[:400]}

    r = client.post(f"/api/v1/journeys/{jid}/plans/generate", json={})
    out["plans_generate"] = {"status": r.status_code, "body": (r.json() if r.status_code < 300 else r.text[:600])}

    r = client.post(
        f"/api/v1/journeys/{jid}/copilot/messages",
        json={"message": "我想少走点路", "locale": "zh"},
    )
    body = r.json() if r.status_code < 300 else r.text[:600]
    out["copilot"] = {"status": r.status_code, "body": body}
    if isinstance(body, dict):
        out["copilot_keys"] = sorted(body.keys())

    r = client.post(
        f"/api/v1/journeys/{jid}/constraints",
        json={"kind": "HARD", "category": "capability", "rule_code": "STEP_FREE_REQUIRED", "params": {}},
    )
    out["constraint_unsupported_hard"] = {"status": r.status_code, "body": (r.json() if r.status_code < 300 else r.text[:600])}

    r = client.post(
        f"/api/v1/journeys/{jid}/constraints",
        json={"kind": "HARD", "category": "mobility", "rule_code": "MAX_WALKING_PER_LEG_M", "params": {"max_m": 500}},
    )
    out["constraint_walking_hard"] = {"status": r.status_code, "body": (r.json() if r.status_code < 300 else r.text[:600])}

    r = client.post(
        f"/api/v1/journeys/{jid}/constraints",
        json={"kind": "SOFT", "category": "capability", "rule_code": "QUIET_ENVIRONMENT", "params": {}},
    )
    out["constraint_soft"] = {"status": r.status_code, "body": (r.json() if r.status_code < 300 else r.text[:600])}

    r = client.post(
        f"/api/v1/journeys/{jid}/replans",
        json={"candidate_count": 2, "reason": "probe"},
    )
    out["replans"] = {"status": r.status_code, "body": (r.json() if r.status_code < 300 else r.text[:600])}

    r = client.get(f"/api/v1/journeys/{jid}/twin")
    out["twin"] = {"status": r.status_code, "body": (r.json() if r.status_code < 300 else r.text[:400])}

    r = client.get(f"/api/v1/agent/tools/v2")
    out["agent_tools_v2"] = {"status": r.status_code, "body": r.json() if r.status_code < 300 else r.text[:400]}

    r = client.get(f"/api/v1/agent/hermes/capabilities")
    out["hermes_capabilities"] = {"status": r.status_code, "body": r.json() if r.status_code < 300 else r.text[:400]}

(LAB / "_probe_shapes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print("written")
