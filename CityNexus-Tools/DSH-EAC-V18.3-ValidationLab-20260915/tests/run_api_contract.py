"""DSH-EAC V18.3 — live runtime / API contract re-check (P1, section 5).

Targets the isolated backend on :8022 (snapshot code). Confirms whether the
V18.2 F1/F2 defects are still present in the CURRENT snapshot, plus the
DIRECT/Hermes response contract and SSE truth. Never modifies the main tree.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_common import client, get_scenario, EVIDENCE  # noqa: E402

SC = get_scenario()
JID = SC["journey_id"]
import uuid  # noqa: E402
UNK = str(uuid.uuid4())


def jget(c, path, **kw):
    try:
        r = c.get(path, **kw)
        return r.status_code, r.text[:800]
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"


def jpost(c, path, **kw):
    try:
        r = c.post(path, **kw)
        return r.status_code, r.text[:800]
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"


def main() -> int:
    c = client()
    findings = []
    checks = []

    # C1 runtime-status
    s, b = jget(c, "/api/v1/agent/runtime-status")
    rt = json.loads(b) if b.startswith("{") else {}
    checks.append({"id": "C1_runtime_status", "status": s, "body": rt})
    findings.append(f"C1 runtime-status={s} identity={rt.get('runtime_identity')} native_proven={rt.get('native_mcp_proven')}")

    # C2 capabilities (configured path)
    s, b = jget(c, "/api/v1/agent/hermes/capabilities")
    cap = json.loads(b) if b.startswith("{") else {}
    has_ready = "ready" in cap
    checks.append({"id": "C2_capabilities_configured", "status": s, "has_ready_key": has_ready, "body": cap})
    findings.append(f"C2 capabilities(status={s}) configured={cap.get('configured')} has_ready_key={has_ready}")

    # C3 global unknown run (F1 re-check)
    s, b = jget(c, f"/api/v1/agent/hermes/runs/{UNK}")
    checks.append({"id": "C3_global_unknown_run_F1", "status": s, "body": b[:200]})
    f1_global = s == 502
    findings.append(f"C3 GET /agent/hermes/runs/{{unknown}} -> {s} (F1 fixed={f1_global}, want 502 not 500)")

    # C4 journey-scoped unknown run (F1 re-check)
    s, b = jget(c, f"/api/v1/journeys/{JID}/agent/hermes/runs/{UNK}")
    checks.append({"id": "C4_journey_unknown_run_F1", "status": s, "body": b[:200]})
    f1_j = s == 502
    findings.append(f"C4 GET /journeys/{{j}}/agent/hermes/runs/{{unknown}} -> {s} (F1 fixed={f1_j})")

    # C5 stop unknown run (F1 re-check)
    s, b = jpost(c, f"/api/v1/journeys/{JID}/agent/hermes/runs/{UNK}/stop", json={})
    checks.append({"id": "C5_stop_unknown_run_F1", "status": s, "body": b[:200]})
    f1_stop = s == 502
    findings.append(f"C5 POST .../stop -> {s} (F1 fixed={f1_stop})")

    # C6 SSE unknown run global (truth check: must not fake completion)
    s, b = jget(c, f"/api/v1/agent/hermes/runs/{UNK}/events")
    checks.append({"id": "C6_sse_unknown_global", "status": s, "body_len": len(b), "body_head": b[:120]})
    findings.append(f"C6 GET /agent/hermes/runs/{{unknown}}/events -> {s} body_len={len(b)} (empty 200 would be a lie)")

    # C7 SSE unknown run journey-scoped
    s, b = jget(c, f"/api/v1/journeys/{JID}/agent/hermes/runs/{UNK}/events")
    checks.append({"id": "C7_sse_unknown_journey", "status": s, "body_len": len(b), "body_head": b[:120]})
    findings.append(f"C7 GET /journeys/{{j}}/.../events -> {s} body_len={len(b)}")

    # C8 copilot messages -> runtime identity contract
    s, b = jpost(c, f"/api/v1/journeys/{JID}/copilot/messages",
                 json={"message": "地铁延误了，帮我看看行程并给出重规划建议。", "locale": "zh"})
    cop = json.loads(b) if b.startswith("{") else {}
    ar = cop.get("agent_run") or {}
    checks.append({"id": "C8_copilot_contract", "status": s, "runtime_identity": ar.get("runtime_identity"), "has_run_id": bool(ar.get("run_id"))})
    findings.append(f"C8 copilot -> {s} runtime_identity={ar.get('runtime_identity')} run_id_present={bool(ar.get('run_id'))}")

    # C9 plans/generate on seeded journey (empty-place 500 is a separate scenario)
    s, b = jpost(c, f"/api/v1/journeys/{JID}/plans/generate")
    checks.append({"id": "C9_plans_generate_seeded", "status": s, "body_head": b[:200]})
    findings.append(f"C9 POST /plans/generate (seeded) -> {s}")

    # C10 health AI readiness
    s, b = jget(c, "/api/v1/health")
    h = json.loads(b) if b.startswith("{") else {}
    checks.append({"id": "C10_health", "status": s, "ai": h.get("ai")})
    findings.append(f"C10 health -> {s} ai={h.get('ai')}")

    result = {
        "f1_resolved_in_snapshot": f1_global and f1_j and f1_stop,
        "f2_unconfigured_missing_ready": "SOURCE-CONFIRMED (native_client.native_hermes_status unconfigured branch omits 'ready')",
        "checks": checks,
    }
    (EVIDENCE / "api_contract.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n".join(findings))
    print("F1_RESOLVED_IN_SNAPSHOT=", result["f1_resolved_in_snapshot"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
