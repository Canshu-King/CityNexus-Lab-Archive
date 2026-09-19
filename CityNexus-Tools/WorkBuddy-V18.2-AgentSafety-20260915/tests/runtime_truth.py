#!/usr/bin/env python3
"""V18.2 Family A - runtime truthfulness (live, isolated backend).

The V18.2 chain claims a runtime identity; this suite checks that the claim is
*earned*, that unconfigured native-Hermes surfaces degrade cleanly, and that the
copilot never fabricates a native run.

Run:
    python tests/runtime_truth.py --base-url http://127.0.0.1:8021 \
        --out evidence/results_runtime_truth.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

RESULTS: list[dict[str, Any]] = []


def _req(method, url, body=None, timeout=20.0):
    data = None
    hdrs = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(raw)
            except json.JSONDecodeError:
                return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw
    except Exception as e:  # noqa: BLE001
        return 0, {"transport_error": str(e)}


def get(b, p, **kw): return _req("GET", b + p, **kw)
def post(b, p, body=None, **kw): return _req("POST", b + p, body=body, **kw)


def record(cid, name, expected, actual, status, evidence=None):
    RESULTS.append({"id": cid, "name": name, "expected": expected, "actual": actual,
                    "status": status, "evidence": evidence})
    mark = {"PASS": "PASS", "FAIL": "FAIL", "NOT_TESTED": "SKIP"}.get(status, status)
    print(f"[{mark}] {cid:6} {name}")
    if status == "FAIL":
        print(f"        expected: {expected}")
        print(f"        actual  : {actual}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8021")
    ap.add_argument("--out", default="evidence/results_runtime_truth.json")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    c, health = get(base, "/api/v1/health")
    if c != 200:
        print("FATAL backend unreachable", c, health); return 2

    # A1 - the runtime identity must be the computed one, not a constant.
    c, rs = get(base, "/api/v1/agent/runtime-status")
    ident = rs.get("runtime_identity") if isinstance(rs, dict) else None
    proven = rs.get("native_mcp_proven") if isinstance(rs, dict) else None
    ok = (c == 200 and isinstance(rs, dict)
          and ident in {"NOT_CONFIGURED", "NATIVE_DEEPSEEK_TOOL_LOOP",
                        "HERMES_COMPAT_ENDPOINT", "HERMES_NATIVE_MCP"}
          and (ident != "HERMES_NATIVE_MCP" or proven is True))
    record("A1", "runtime_identity is computed and never claims HERMES_NATIVE_MCP unproven",
           "identity in known set AND (identity!=HERMES_NATIVE_MCP OR native_mcp_proven=true)",
           f"identity={ident} native_mcp_proven={proven}", "PASS" if ok else "FAIL", rs)

    # A2 - capabilities must expose `ready` in EVERY branch (V18.1 defect F2).
    c, cap = get(base, "/api/v1/agent/hermes/capabilities")
    has_ready = isinstance(cap, dict) and "ready" in cap
    record("A2", "hermes/capabilities exposes `ready` in the unconfigured branch",
           "response contains the `ready` key",
           f"keys={sorted(cap) if isinstance(cap, dict) else cap}",
           "PASS" if has_ready else "FAIL", cap)

    # A3 - native proxy endpoints must degrade cleanly (V18.1 defect F1).
    fake = str(uuid4())
    rc, rb = get(base, f"/api/v1/agent/hermes/runs/{fake}")
    sc, sb = post(base, f"/api/v1/journeys/22222222-2222-4222-8222-222222222222"
                        f"/agent/hermes/runs/{fake}/stop", {})
    no_500 = rc != 500 and sc != 500
    record("A3", "unconfigured native-Hermes proxy endpoints do not 500",
           "GET runs/{id} and POST stop return 4xx/5xx-with-envelope, never a bare 500",
           f"GET runs={rc} POST stop={sc}",
           "PASS" if no_500 else "FAIL",
           {"get_body": rb if not isinstance(rb, dict) else rb,
            "stop_body": sb if not isinstance(sb, dict) else sb})

    # A4 - copilot must not fabricate a native run while Hermes is down.
    c, ids = post(base, "/api/v1/demo/reset", {})
    jid = ids.get("journey_id") if isinstance(ids, dict) else None
    if jid:
        c, cb = post(base, f"/api/v1/journeys/{jid}/copilot/messages",
                     {"message": "暴雨导致海河游船延误了"})
        run = cb.get("agent_run") if isinstance(cb, dict) else None
        record("A4", "copilot does not fabricate a HERMES_NATIVE_MCP run when Hermes is down",
               "agent_run is null",
               f"http={c} agent_run={run}",
               "PASS" if run is None else "FAIL", cb if isinstance(cb, dict) else None)

    # A5 - tool catalogue honesty: read tools declare no domain mutation.
    c, cat = get(base, "/api/v1/agent/tools/v2")
    reads = {"inspect_journey", "inspect_twin", "list_replans", "search_city_services"}
    mutators = {"replace_activity", "reschedule_activity", "create_booking",
                "cancel_refundable_booking", "request_commitment_change"}
    names = {t.get("name") for t in cat} if isinstance(cat, list) else set()
    read_flags_ok = all(
        t.get("mutates_domain_truth") is False for t in (cat or []) if t.get("name") in reads
    )
    mut_flags_ok = all(
        t.get("mutates_domain_truth") is True for t in (cat or []) if t.get("name") in mutators
    )
    ok = reads <= names and mutators <= names and read_flags_ok and mut_flags_ok
    record("A5", "tool catalogue: read tools declare mutates_domain_truth=false, mutators true",
           "all reads false, all typed mutators true",
           f"names_ok={reads <= names and mutators <= names} reads={read_flags_ok} mutators={mut_flags_ok}",
           "PASS" if ok else "FAIL",
           {"catalog": cat if isinstance(cat, list) else str(cat)[:200]})

    # A6 - an unknown tool must be refused, not silently accepted.
    c, ub = post(base, f"/api/v1/agent/tools/v2/{uuid4()}", {"request_id": str(uuid4()),
                                                            "journey_id": jid})
    refused = c in {404, 422} or (isinstance(ub, dict) and isinstance(ub.get("error"), dict))
    record("A6", "unknown v2 tool name is refused",
           "404/422 error envelope", f"http={c} body={str(ub)[:120]}",
           "PASS" if refused else "FAIL")

    summary = {"PASS": 0, "FAIL": 0, "NOT_TESTED": 0}
    for r in RESULTS:
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    payload = {"meta": {"harness": "tests/runtime_truth.py", "base_url": base,
                        "generated_at": datetime.now(timezone.utc).isoformat()},
               "summary": summary, "scenarios": RESULTS}
    out = args.out if os.path.isabs(args.out) else os.path.join(root, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(payload, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n== SUMMARY ==  PASS={summary['PASS']} FAIL={summary['FAIL']} "
          f"NOT_TESTED={summary['NOT_TESTED']}")
    print("written:", out)
    return 0 if summary["FAIL"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
