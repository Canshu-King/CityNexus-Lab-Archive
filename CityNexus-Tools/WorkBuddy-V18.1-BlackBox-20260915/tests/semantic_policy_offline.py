#!/usr/bin/env python3
"""Deterministic, offline SemanticEnvelope policy tests (scenario F).

Verifies that a validated DeepSeek envelope is mapped to a safe CityNexus route
and is NOT re-overridden by a low-level substring classifier. Pure: no network,
no server, no database.

Run:
    python tests/semantic_policy_offline.py --repo <repo_copy/backend> \
        --out evidence/results_semantic.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

RESULTS: list[dict[str, Any]] = []


def record(cid: str, name: str, expected: str, actual: str, status: str,
           evidence: Any = None) -> None:
    RESULTS.append({"id": cid, "name": name, "expected": expected,
                    "actual": actual, "status": status, "evidence": evidence})
    mark = {"PASS": "PASS", "FAIL": "FAIL", "NOT_TESTED": "SKIP"}.get(status, status)
    print(f"[{mark}] {cid:6} {name}")
    if status == "FAIL":
        print(f"        expected: {expected}")
        print(f"        actual  : {actual}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="path to repo_copy/backend")
    ap.add_argument("--out", default="evidence/results_semantic.json")
    args = ap.parse_args()
    sys.path.insert(0, os.path.abspath(args.repo))

    from app.integrations.ai.semantic_compiler import (  # noqa: E402
        SemanticEnvelope, apply_semantic_policy,
    )
    from app.integrations.ai.copilot_contract import classify_copilot_message  # noqa: E402

    def env(**over: Any) -> SemanticEnvelope:
        base = dict(intent="DISRUPTION_REPORT", assertion_status="ASSERTED",
                    effective_time="NOW", event_type="CLOSURE", requested_action="REQUEST_REPLAN",
                    confidence=0.9, reasoning_summary="t", entities={}, constraints=[])
        base.update(over)
        return SemanticEnvelope(**base)

    # ---- assertion-status -> route table -----------------------------------
    table = [
        ("F1", "ASSERTED NOW CLOSURE -> live Event",
         env(assertion_status="ASSERTED", effective_time="NOW", event_type="CLOSURE"),
         {"route": "DISRUPTION_REPORT", "create_event": True}),
        ("F2", "ASSERTED FUTURE WEATHER -> live Event",
         env(assertion_status="ASSERTED", effective_time="FUTURE", event_type="WEATHER"),
         {"route": "DISRUPTION_REPORT", "create_event": True}),
        ("F3", "HYPOTHETICAL -> WHAT_IF, no Event",
         env(assertion_status="HYPOTHETICAL", event_type="WEATHER"),
         {"route": "WHAT_IF", "create_event": False}),
        ("F4", "UNVERIFIED -> VERIFY_FACT, no Event",
         env(assertion_status="UNVERIFIED", event_type="CLOSURE"),
         {"route": "VERIFY_FACT", "create_event": False}),
        ("F5", "NEGATED -> UNKNOWN, no Event",
         env(assertion_status="NEGATED", event_type="CLOSURE"),
         {"route": "UNKNOWN", "create_event": False}),
        ("F6", "HISTORICAL -> UNKNOWN, no Event",
         env(assertion_status="HISTORICAL", event_type="CLOSURE"),
         {"route": "UNKNOWN", "create_event": False}),
        ("F7", "PERSONAL -> no city Event",
         env(intent="PERSONAL_ASSISTANCE", event_type="PERSONAL", requested_action="REQUEST_ASSISTANCE"),
         {"route": "PERSONAL_ASSISTANCE", "create_event": False}),
        ("F8", "ASSERTED PAST -> not a live Event",
         env(assertion_status="ASSERTED", effective_time="PAST", event_type="CLOSURE"),
         {"route": "DISRUPTION_REPORT", "create_event": False}),
        ("F9", "EXPLAIN_PLAN -> no Event",
         env(intent="EXPLAIN_PLAN", event_type="NONE", requested_action="EXPLAIN"),
         {"route": "EXPLAIN_PLAN", "create_event": False}),
    ]
    for cid, name, e, exp in table:
        d = apply_semantic_policy(e)
        ok = d.route_intent == exp["route"] and d.create_event == exp["create_event"]
        record(cid, name, f"route={exp['route']} create_event={exp['create_event']}",
               f"route={d.route_intent} create_event={d.create_event}",
               "PASS" if ok else "FAIL", {"reason": d.reason})

    # ---- schema validation rejects malformed envelopes ---------------------
    bad_cases = [
        ("F10", "missing key rejected", {"intent": "DISRUPTION_REPORT"}),
        ("F11", "out-of-enum assertion rejected",
         {"intent": "DISRUPTION_REPORT", "assertion_status": "MAYBE", "effective_time": "NOW",
          "event_type": "CLOSURE", "requested_action": "REQUEST_REPLAN", "confidence": 0.5,
          "reasoning_summary": "x", "entities": {}, "constraints": []}),
        ("F12", "confidence out of range rejected",
         {"intent": "DISRUPTION_REPORT", "assertion_status": "ASSERTED", "effective_time": "NOW",
          "event_type": "CLOSURE", "requested_action": "REQUEST_REPLAN", "confidence": 1.7,
          "reasoning_summary": "x", "entities": {}, "constraints": []}),
    ]
    for cid, name, mapping in bad_cases:
        got = SemanticEnvelope.from_mapping(mapping)
        record(cid, name, "None (rejected)", "None" if got is None else "accepted",
               "PASS" if got is None else "FAIL")

    # ---- the anti-override seam --------------------------------------------
    # A hypothetical utterance must NOT be treated as a live disruption even if a
    # low-level substring classifier is tempted to. The semantic policy wins.
    seam_msg = "如果明天下雨会怎样？"
    fallback = classify_copilot_message(seam_msg)
    policy = apply_semantic_policy(env(assertion_status="HYPOTHETICAL", event_type="WEATHER",
                                       intent="DISRUPTION_REPORT"))
    ok = policy.route_intent == "WHAT_IF" and policy.create_event is False
    record("F13", "semantic policy overrides substring temptation (hypothetical)",
           "WHAT_IF / create_event=False regardless of fallback",
           f"fallback={fallback.intent} policy={policy.route_intent} create_event={policy.create_event}",
           "PASS" if ok else "FAIL",
           {"fallback_intent": fallback.intent, "policy_route": policy.route_intent})

    neg_msg = "博物馆没有关门。"
    neg_fb = classify_copilot_message(neg_msg)
    neg_policy = apply_semantic_policy(env(assertion_status="NEGATED", event_type="CLOSURE"))
    ok = neg_policy.create_event is False and neg_policy.route_intent == "UNKNOWN"
    record("F14", "negated claim never creates a live Event",
           "UNKNOWN / create_event=False",
           f"fallback={neg_fb.intent} policy={neg_policy.route_intent} create_event={neg_policy.create_event}",
           "PASS" if ok else "FAIL", {"fallback_intent": neg_fb.intent})

    summary = {"PASS": 0, "FAIL": 0, "NOT_TESTED": 0}
    for r in RESULTS:
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    payload = {"meta": {"generated_at": __import__("datetime").datetime.utcnow().isoformat(),
                        "harness": "tests/semantic_policy_offline.py", "repo": args.repo},
               "summary": summary, "scenarios": RESULTS}
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
