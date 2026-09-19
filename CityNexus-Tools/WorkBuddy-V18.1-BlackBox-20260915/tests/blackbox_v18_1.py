#!/usr/bin/env python3
"""CityNexus V18.1 Black-Box validation harness (tests-only, no production edits).

Drives the *isolated* CityNexus backend over HTTP and records the truth of the
runtime chain:

    DeepSeek SemanticEnvelope -> runtime router -> DIRECT / HERMES_NATIVE_MCP
    -> Hermes Runs/SSE -> CityNexus MCP V2 -> AgentToolGateway/Guardian
    -> Desktop/Mobile Agent Timeline

Hard rule: a native Hermes run only counts as proven when a *real CityNexus MCP
tool event* appears in the run's event stream.

Usage:
    python tests/blackbox_v18_1.py --base-url http://127.0.0.1:8020 \
        --out evidence/results.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

RESULTS: list[dict[str, Any]] = []
META: dict[str, Any] = {}


# --------------------------------------------------------------------------
# HTTP helpers (stdlib only)
# --------------------------------------------------------------------------
def _req(method: str, url: str, body: Any = None, timeout: float = 30.0,
         headers: dict[str, str] | None = None) -> tuple[int, Any]:
    data = None
    hdrs = {"Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw
    except Exception as exc:  # noqa: BLE001 - record transport failures
        return 0, {"transport_error": str(exc)}


def get(base: str, path: str, **kw) -> tuple[int, Any]:
    return _req("GET", base + path, **kw)


def post(base: str, path: str, body: Any = None, **kw) -> tuple[int, Any]:
    return _req("POST", base + path, body=body, **kw)


def intent_name(body: Any) -> Any:
    """Copilot responses expose the interpreted intent under intent.name."""
    if not isinstance(body, dict):
        return None
    node = body.get("intent")
    if isinstance(node, dict):
        return node.get("name")
    return node


def record(family: str, cid: str, name: str, expected: str, actual: str,
           status: str, evidence: Any = None) -> None:
    RESULTS.append({
        "family": family, "id": cid, "name": name,
        "expected": expected, "actual": actual,
        "status": status, "evidence": evidence,
    })
    mark = {"PASS": "PASS", "FAIL": "FAIL", "NOT_TESTED": "SKIP"}.get(status, status)
    print(f"[{mark}] {cid:6} {name}")
    if status == "FAIL":
        print(f"        expected: {expected}")
        print(f"        actual  : {actual}")


# --------------------------------------------------------------------------
# Bootstrap
# --------------------------------------------------------------------------
def bootstrap_journey(base: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    start = now + timedelta(days=1)
    end = start + timedelta(days=2)
    code, trav = post(base, "/api/v1/travelers", {
        "display_name": "V18.1 BlackBox Traveller",
        "timezone": "Asia/Shanghai",
        "locale": "en-GB",
    })
    if code not in (200, 201):
        return {"ok": False, "step": "traveler", "code": code, "body": trav}
    code, journey = post(base, "/api/v1/journeys", {
        "traveler_id": trav["id"],
        "title": "V18.1 BlackBox Validation Journey",
        "city_code": "tianjin",
        "timezone": "Asia/Shanghai",
        "start_at": start.isoformat(),
        "end_at": end.isoformat(),
        "budget": {"amount_minor": 180000, "currency": "CNY"},
        "party_size": 2,
    })
    if code not in (200, 201):
        return {"ok": False, "step": "journey", "code": code, "body": journey}
    jid = journey["id"]
    # generate a plan so the copilot context is rich
    pcode, plan = post(base, f"/api/v1/journeys/{jid}/plans/generate", {})
    return {"ok": True, "journey_id": jid, "traveler_id": trav["id"],
            "plan_code": pcode, "plan": plan if isinstance(plan, dict) else None}


# --------------------------------------------------------------------------
# A. Runtime truth
# --------------------------------------------------------------------------
def scenario_runtime_truth(base: str) -> None:
    code, status = get(base, "/api/v1/agent/runtime-status")
    code2, caps = get(base, "/api/v1/agent/hermes/capabilities")
    code3, tools = get(base, "/api/v1/agent/tools/v2")
    META["runtime_status"] = status
    META["hermes_capabilities"] = caps
    META["tools_v2"] = tools

    # A0 - runtime-status is reachable and well formed
    ok = code == 200 and isinstance(status, dict) and "runtime_identity" in status
    record("A_runtime_truth", "A0", "runtime-status reachable + shaped",
           "200 with runtime_identity/native_binary_detected/native_mcp_proven",
           f"{code} {json.dumps(status)[:180] if isinstance(status, dict) else status}",
           "PASS" if ok else "FAIL", {"status": code})

    ident = (status or {}).get("runtime_identity")
    gateway = (status or {}).get("hermes_native_gateway") or {}
    gateway_ready = bool(gateway.get("ready"))

    # A1 - identity is a *derived* fact, not a hardcoded claim
    #      (isolated instance has no hermes config -> must NOT claim Hermes)
    if isinstance(status, dict):
        if gateway_ready:
            # live instance with a ready gateway: identity may be HERMES_NATIVE_MCP
            ok = ident == "HERMES_NATIVE_MCP"
            record("A_runtime_truth", "A1", "identity == HERMES_NATIVE_MCP only when gateway ready",
                   "gateway ready -> HERMES_NATIVE_MCP", f"ident={ident} ready={gateway_ready}",
                   "PASS" if ok else "FAIL")
        else:
            ok = ident != "HERMES_NATIVE_MCP"
            record("A_runtime_truth", "A1", "no ready gateway -> must NOT claim HERMES_NATIVE_MCP",
                   "identity != HERMES_NATIVE_MCP", f"ident={ident} ready={gateway_ready}",
                   "PASS" if ok else "FAIL")
    else:
        record("A_runtime_truth", "A1", "identity derivation", "dict", str(status), "FAIL")

    # A2 - native_mcp_proven is an *audit flag*, never inferred from reachability
    proven = (status or {}).get("native_mcp_proven")
    record("A_runtime_truth", "A2", "native_mcp_proven is an explicit audit flag",
           "boolean flag independent of gateway reachability",
           f"native_mcp_proven={proven} (gateway_ready={gateway_ready})",
           "PASS" if isinstance(proven, bool) else "FAIL",
           {"flag": proven, "gateway_ready": gateway_ready,
            "note": "flag is set from CITYNEXUS_HERMES_NATIVE_PROVEN, not from a real run"})

    # A3 - capabilities expose the Hermes Runs contract.
    #      Contract inconsistency: the unconfigured branch omits "ready" entirely,
    #      so a consumer reading caps["ready"] would KeyError.
    ok = code2 == 200 and isinstance(caps, dict) and "configured" in caps
    shape_ok = isinstance(caps, dict) and "ready" in caps
    record("A_runtime_truth", "A3", "hermes/capabilities exposes readiness",
           "200 with ready/runs/events/approval in BOTH configured and unconfigured states",
           f"{code2} configured={caps.get('configured') if isinstance(caps,dict) else '?'} ready_key_present={shape_ok}",
           "PASS" if (ok and shape_ok) else ("FAIL" if ok else "FAIL"),
           {"caps": caps, "note": "unconfigured branch omits the 'ready' key"})

    # A4 - MCP V2 tool surface advertises the 11 CityNexus tools
    names = [t.get("name") for t in tools] if isinstance(tools, list) else []
    expected_tools = {"inspect_journey", "inspect_twin", "list_replans", "search_city_services",
                      "request_replan", "accept_replan", "replace_activity", "reschedule_activity",
                      "create_booking", "cancel_refundable_booking", "request_commitment_change"}
    missing = expected_tools - set(names)
    record("A_runtime_truth", "A4", "MCP V2 tool surface == 11 CityNexus tools",
           "all 11 tools advertised", f"{len(names)} tools, missing={sorted(missing)}",
           "PASS" if not missing and len(names) >= 11 else "FAIL", {"tools": names})


# --------------------------------------------------------------------------
# E. DeepSeek/Hermes routing
# --------------------------------------------------------------------------
DIRECT_CASES = [
    ("为什么这样安排？", "EXPLAIN_PLAN"),
    ("如果博物馆多待一小时会怎样？", "WHAT_IF"),
    ("Why is the plan arranged this way?", "EXPLAIN_PLAN"),
    ("What if we stayed one more hour at the museum?", "WHAT_IF"),
]


def scenario_routing(base: str, journey_id: str) -> None:
    for i, (msg, expect_intent) in enumerate(DIRECT_CASES, 1):
        code, body = post(base, f"/api/v1/journeys/{journey_id}/copilot/messages",
                          {"message": msg})
        if code != 200 or not isinstance(body, dict):
            record("E_routing", f"E{i}", f"DIRECT: {msg[:26]}",
                   f"200 intent={expect_intent}", f"{code} {str(body)[:120]}", "FAIL")
            continue
        intent = intent_name(body)
        agent_run = body.get("agent_run")
        # DIRECT: no native run must be created and identity must not be claimed
        ok = intent == expect_intent and agent_run is None
        record("E_routing", f"E{i}", f"DIRECT stays DIRECT: {msg[:26]}",
               f"intent={expect_intent} and agent_run=null",
               f"intent={intent} agent_run={'set' if agent_run else 'null'}",
               "PASS" if ok else "FAIL",
               {"intent": body.get("intent"), "agent_run": agent_run})

    # Hermes-suitable multi-step request
    hermes_msg = ("检查当前行程与受保护承诺，搜索几个室内替代地点，比较后提出少走路的重规划方案，但不要提交。")
    code, body = post(base, f"/api/v1/journeys/{journey_id}/copilot/messages",
                      {"message": hermes_msg})
    if code == 200 and isinstance(body, dict):
        intent = intent_name(body)
        agent_run = body.get("agent_run")
        caps = META.get("hermes_capabilities") or {}
        if caps.get("ready"):
            ok = intent == "REPLAN_REQUEST" and isinstance(agent_run, dict) and agent_run.get("run_id")
            record("E_routing", "E5", "multi-step PLAN_ONLY -> Hermes run",
                   "intent=REPLAN_REQUEST and agent_run.run_id present",
                   f"intent={intent} agent_run={agent_run}", "PASS" if ok else "FAIL")
        else:
            # native unavailable: must fall back explicitly, must NOT fake identity
            fake = isinstance(agent_run, dict) and agent_run.get("runtime_identity") == "HERMES_NATIVE_MCP"
            ok = (not fake)
            record("E_routing", "E5", "native unavailable -> explicit fallback (no fake Hermes)",
                   "agent_run null or no HERMES_NATIVE_MCP identity when gateway not ready",
                   f"intent={intent} agent_run={agent_run}",
                   "PASS" if ok else "FAIL")
    else:
        record("E_routing", "E5", "multi-step PLAN_ONLY routing", "200", f"{code} {str(body)[:120]}", "FAIL")


# --------------------------------------------------------------------------
# D. Stop proxy
# --------------------------------------------------------------------------
def scenario_stop(base: str, journey_id: str) -> None:
    # A stop for an unknown run must fail cleanly (502/404), never expose the key.
    code, body = post(base, f"/api/v1/journeys/{journey_id}/agent/hermes/runs/blackbox-unknown-run/stop", {})
    ok = code in (404, 502, 422)
    record("D_stop", "D1", "stop proxy fails cleanly for unknown run",
           "404/502/422 (no key leakage)", f"{code} {str(body)[:120]}",
           "PASS" if ok else "FAIL")
    # Response must never contain the bearer key material
    txt = json.dumps(body) if not isinstance(body, str) else body
    leaked = "Bearer " in txt or "api_server_key" in txt.lower()
    record("D_stop", "D2", "stop response carries no credential material",
           "no bearer/key in body", f"leaked={leaked}", "PASS" if not leaked else "FAIL")


# --------------------------------------------------------------------------
# X. Native-Hermes proxy robustness (unconfigured state)
# --------------------------------------------------------------------------
def scenario_proxy_robustness(base: str, journey_id: str) -> None:
    """When native Hermes is not configured, the three proxy endpoints must
    return a clean 502 - never an unhandled 500 and never a broken stream.

    Root cause: `client = HermesNativeClient()` is constructed OUTSIDE the
    try/except in all three handlers, so the ValueError raised by an
    unconfigured client escapes the 502 mapping.
    """
    code, body = get(base, "/api/v1/agent/hermes/runs/blackbox-unknown-run", timeout=12)
    record("X_proxy_robustness", "X1", "GET run-status -> clean 502 when unconfigured",
           "502 (mapped) not 500 (unhandled)", f"{code}",
           "PASS" if code == 502 else "FAIL",
           {"handler": "get_native_hermes_run", "observed": code})

    code, body = post(base, f"/api/v1/journeys/{journey_id}/agent/hermes/runs/blackbox-unknown-run/stop", {}, timeout=12)
    record("X_proxy_robustness", "X2", "POST stop -> clean 502 when unconfigured",
           "502 (mapped) not 500 (unhandled)", f"{code}",
           "PASS" if code == 502 else "FAIL",
           {"handler": "stop_native_hermes_run", "observed": code})

    code, body = get(base, "/api/v1/agent/hermes/runs/blackbox-unknown-run/events", timeout=12)
    record("X_proxy_robustness", "X3", "GET events stream -> clean refusal when unconfigured",
           "definite status (502) instead of a broken/aborted stream",
           f"{code}" + ("" if code else " (transport aborted)"),
           "PASS" if code == 502 else "FAIL",
           {"handler": "stream_native_hermes_events", "observed": code})


# --------------------------------------------------------------------------
# F. Semantic truth (live, only if a model is configured)
# --------------------------------------------------------------------------
SEMANTIC_LIVE = [
    ("现在博物馆关门了。", {"create_event": True}),
    ("如果明天下雨会怎样？", {"create_event": False}),
    ("有人说这家博物馆关门了。", {"create_event": False}),
    ("博物馆没有关门。", {"create_event": False}),
    ("昨天博物馆关门了。", {"create_event": False}),
]


def scenario_semantic_live(base: str, journey_id: str) -> None:
    ai_on = (META.get("runtime_status") or {}).get("deepseek_configured")
    for i, (msg, expect) in enumerate(SEMANTIC_LIVE, 1):
        code, body = post(base, f"/api/v1/journeys/{journey_id}/copilot/messages", {"message": msg})
        if code != 200 or not isinstance(body, dict):
            record("F_semantic", f"F{i}", f"semantic live: {msg[:20]}", str(expect), f"{code}", "FAIL")
            continue
        env = (body.get("intent") or {}).get("semantic_envelope")
        if not env:
            record("F_semantic", f"F{i}", f"semantic live: {msg[:20]}",
                   "semantic_envelope present (DeepSeek)", "no envelope (fallback path)",
                   "NOT_TESTED", {"ai_on": bool(ai_on), "intent": body.get("intent")})
            continue
        actual_ce = bool(env.get("create_event"))
        ok = actual_ce == expect["create_event"]
        record("F_semantic", f"F{i}", f"semantic live: {msg[:20]}",
               f"create_event={expect['create_event']}",
               f"create_event={actual_ce} assertion={env.get('assertion_status')} route={env.get('route_intent')}",
               "PASS" if ok else "FAIL", {"envelope": env})


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8020")
    ap.add_argument("--out", default="evidence/results.json")
    ap.add_argument("--label", default="isolated-8020")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    META.update({
        "base_url": base, "label": args.label,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "harness": "tests/blackbox_v18_1.py",
    })

    code, health = get(base, "/api/v1/health")
    META["health"] = health
    if code != 200:
        print(f"FATAL: backend not reachable at {base} ({code})")
        return 2

    boot = bootstrap_journey(base)
    META["bootstrap"] = boot
    jid = boot.get("journey_id")

    scenario_runtime_truth(base)
    if jid:
        scenario_routing(base, jid)
        scenario_stop(base, jid)
        scenario_proxy_robustness(base, jid)
        scenario_semantic_live(base, jid)
    else:
        record("E_routing", "E0", "journey bootstrap", "created", str(boot), "FAIL")

    summary = {"PASS": 0, "FAIL": 0, "NOT_TESTED": 0}
    for r in RESULTS:
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    payload = {"meta": META, "summary": summary, "scenarios": RESULTS}

    out = args.out
    if not os.path.isabs(out):
        out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"\n== SUMMARY ==  PASS={summary['PASS']} FAIL={summary['FAIL']} NOT_TESTED={summary['NOT_TESTED']}")
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
