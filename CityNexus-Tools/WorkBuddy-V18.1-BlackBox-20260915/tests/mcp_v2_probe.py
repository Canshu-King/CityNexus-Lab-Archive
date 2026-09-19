#!/usr/bin/env python3
"""Direct CityNexus MCP V2 surface probe (the MCP link of the chain).

Imports the real `citynexus_mcp` package (the mcp SDK import is lazy, so this
needs only httpx) and exercises the V2 tool allowlist plus one real tool call
against the isolated backend.

Run:
    PYTHONPATH=<repo_copy/agent-mcp> python tests/mcp_v2_probe.py \
        --base-url http://127.0.0.1:8020 --journey-id <uuid> \
        --out evidence/results_mcp.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

RESULTS: list[dict[str, Any]] = []


def record(family: str, cid: str, name: str, expected: str, actual: str,
           status: str, evidence: Any = None) -> None:
    RESULTS.append({"family": family, "id": cid, "name": name, "expected": expected,
                    "actual": actual, "status": status, "evidence": evidence})
    mark = {"PASS": "PASS", "FAIL": "FAIL", "NOT_TESTED": "SKIP"}.get(status, status)
    print(f"[{mark}] {cid:6} {name}")
    if status == "FAIL":
        print(f"        expected: {expected}")
        print(f"        actual  : {actual}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8020")
    ap.add_argument("--journey-id", default="")
    ap.add_argument("--out", default="evidence/results_mcp.json")
    args = ap.parse_args()

    try:
        from citynexus_mcp.client import CityNexusAgentClient
        from citynexus_mcp.server import CityNexusMCPServer, TOOL_DESCRIPTIONS
        from citynexus_mcp.schemas import V2_TOOL_NAMES, MCPToolCall
    except Exception as exc:  # noqa: BLE001
        record("MCP", "M0", "import citynexus_mcp", "importable", f"{type(exc).__name__}: {exc}", "FAIL")
        _write(args, RESULTS)
        return 1

    adapter = CityNexusMCPServer(client=CityNexusAgentClient(base_url=args.base_url))

    # M1 - the V2 allowlist is exactly the 11 documented tools
    v2 = adapter.list_tools_v2()
    names = [t["name"] for t in v2]
    expected = {"inspect_journey", "inspect_twin", "list_replans", "search_city_services",
                "request_replan", "accept_replan", "replace_activity", "reschedule_activity",
                "create_booking", "cancel_refundable_booking", "request_commitment_change"}
    ok = set(names) == expected
    record("MCP", "M1", "V2 tool allowlist == 11 documented tools",
           "exact 11-tool allowlist", f"{len(names)} tools; symmetric_diff={sorted(set(names) ^ expected)}",
           "PASS" if ok else "FAIL", {"tools": names})

    # M2 - the V1 surface is the pinned 6-tool subset
    v1 = [t["name"] for t in adapter.list_tools()]
    ok = len(v1) == 6 and set(v1).issubset(set(names))
    record("MCP", "M2", "V1 surface is the pinned 6-tool subset",
           "6 tools, subset of V2", f"{len(v1)} tools {v1}", "PASS" if ok else "FAIL")

    # M3 - allowlist enforcement rejects an unknown tool
    try:
        adapter.call("delete_everything", MCPToolCall(request_id="x", agent_id="mcp-client", arguments={}))
        record("MCP", "M3", "unknown tool rejected by allowlist", "ValueError", "no error raised", "FAIL")
    except ValueError:
        record("MCP", "M3", "unknown tool rejected by allowlist", "ValueError", "ValueError raised", "PASS")
    except Exception as exc:  # noqa: BLE001
        record("MCP", "M3", "unknown tool rejected by allowlist", "ValueError", f"{type(exc).__name__}", "FAIL")

    # M4 - a REAL MCP tool call against a real journey (the MCP boundary proof)
    jid = args.journey_id
    if not jid:
        record("MCP", "M4", "real inspect_journey tool call", "journey id supplied", "none", "NOT_TESTED")
    else:
        try:
            result = adapter.call(
                "inspect_journey",
                MCPToolCall(request_id="blackbox-m4", agent_id="mcp-client",
                            arguments={"journey_id": jid}),
            )
            ok = isinstance(result, dict) and bool(result)
            record("MCP", "M4", "real inspect_journey tool call returns server data",
                   "non-empty dict from the HTTP tool bridge",
                   f"keys={sorted(result)[:8] if isinstance(result, dict) else type(result).__name__}",
                   "PASS" if ok else "FAIL",
                   {"sample": {k: result[k] for k in list(result)[:5]} if isinstance(result, dict) else result})
        except Exception as exc:  # noqa: BLE001
            record("MCP", "M4", "real inspect_journey tool call", "non-empty dict",
                   f"{type(exc).__name__}: {exc}", "FAIL")

    # M5 - read-only annotation is present for inspection tools
    ro = {t["name"]: t.get("annotations", {}).get("readOnlyHint") for t in v2}
    ok = ro.get("inspect_journey") is True and ro.get("request_replan") is not True
    record("MCP", "M5", "read-only hints distinguish inspect vs mutate",
           "inspect_* readOnly, mutating tools not readOnly",
           f"inspect_journey={ro.get('inspect_journey')} request_replan={ro.get('request_replan')}",
           "PASS" if ok else "FAIL", {"read_only": ro})

    _write(args, RESULTS)
    return 0


def _write(args: Any, results: list[dict[str, Any]]) -> None:
    summary = {"PASS": 0, "FAIL": 0, "NOT_TESTED": 0}
    for r in results:
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    import datetime
    payload = {"meta": {"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "harness": "tests/mcp_v2_probe.py", "base_url": args.base_url},
               "summary": summary, "scenarios": results}
    out = args.out
    if not os.path.isabs(out):
        out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"\n== SUMMARY ==  PASS={summary['PASS']} FAIL={summary['FAIL']} NOT_TESTED={summary['NOT_TESTED']}")
    print(f"written: {out}")


if __name__ == "__main__":
    sys.exit(main())
