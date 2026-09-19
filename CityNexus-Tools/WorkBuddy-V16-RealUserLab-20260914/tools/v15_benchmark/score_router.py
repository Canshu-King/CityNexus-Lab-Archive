"""Score the optional reference router against the benchmark (offline, no API)."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.agent.semantic_router import JourneyContext, route  # noqa: E402

BENCH = ROOT / "COPILOT_SEMANTIC_BENCHMARK.jsonl"
OUT = ROOT / "evidence" / "router_benchmark_results.json"
EVENT_EXPECTATION = {
    "FORBIDDEN": False, "NONE": False,
    "WEATHER": True, "TRAFFIC_DELAY": True, "PROVIDER_EVENT": True, "MAYBE": None,
}


def main() -> int:
    rows = [json.loads(l) for l in BENCH.read_text(encoding="utf-8").splitlines() if l.strip()]
    intent_ok = policy_ok = confirm_ok = event_ok = 0
    by_intent: Counter = Counter()
    by_intent_ok: Counter = Counter()
    by_family: Counter = Counter()
    by_family_ok: Counter = Counter()
    mismatches: list[dict] = []
    event_fp: list[dict] = []
    override_permissive: list[dict] = []
    confirm_missed: list[dict] = []

    for case in rows:
        ctx = JourneyContext(
            city_code=case["city_code"], timezone=case["timezone"],
            currency=case["currency"], locale=case["locale"],
            journey_state=case["journey_state"],
        )
        r = route(case["message"], ctx)
        by_intent[case["expected_intent"]] += 1
        by_family[case["case_family"]] += 1
        if r.intent == case["expected_intent"]:
            intent_ok += 1
            by_intent_ok[case["expected_intent"]] += 1
            by_family_ok[case["case_family"]] += 1
        else:
            mismatches.append({
                "id": case["id"], "message": case["message"],
                "expected": case["expected_intent"], "predicted": r.intent,
                "rationale": r.rationale, "family": case["case_family"],
            })
        if r.mutation_policy == case["expected_mutation_policy"]:
            policy_ok += 1
        if bool(r.requires_confirmation) == bool(case["expected_requires_confirmation"]):
            confirm_ok += 1
        elif case["expected_requires_confirmation"]:
            confirm_missed.append({"id": case["id"], "message": case["message"], "policy": r.mutation_policy})
        exp_event = EVENT_EXPECTATION.get(case["expected_event_creation"])
        if exp_event is None or bool(r.creates_real_event) == exp_event:
            event_ok += 1
        elif exp_event is False:
            event_fp.append({"id": case["id"], "message": case["message"], "intent": r.intent})
        if case["expected_mutation_policy"] == "REJECT_OVERRIDE" and r.mutation_policy in {
            "REQUEST_ONLY", "REQUEST_WITH_CONFIRMATION", "EVENT_THEN_MISSION"
        }:
            override_permissive.append({"id": case["id"], "message": case["message"], "policy": r.mutation_policy})

    n = len(rows)
    pct = lambda a, b: round(100.0 * a / b, 1) if b else 0.0
    out = {
        "scored": n,
        "intent_accuracy_pct": pct(intent_ok, n),
        "mutation_policy_accuracy_pct": pct(policy_ok, n),
        "requires_confirmation_accuracy_pct": pct(confirm_ok, n),
        "event_boundary_accuracy_pct": pct(event_ok, n),
        "counts": {
            "intent_correct": intent_ok, "policy_correct": policy_ok,
            "confirmation_correct": confirm_ok, "event_boundary_correct": event_ok,
            "event_false_positives": len(event_fp),
            "authority_override_permissive": len(override_permissive),
            "confirmation_missed": len(confirm_missed),
        },
        "per_intent": {k: {"total": by_intent[k], "correct": by_intent_ok[k], "accuracy_pct": pct(by_intent_ok[k], by_intent[k])} for k in sorted(by_intent)},
        "per_family": {k: {"total": by_family[k], "correct": by_family_ok[k], "accuracy_pct": pct(by_family_ok[k], by_family[k])} for k in sorted(by_family)},
        "intent_mismatches": mismatches,
        "event_false_positives": event_fp,
        "authority_override_permissive": override_permissive,
        "confirmation_missed": confirm_missed,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"reference router scored on {n} cases")
    print(f"  intent               {out['intent_accuracy_pct']}%")
    print(f"  mutation policy      {out['mutation_policy_accuracy_pct']}%")
    print(f"  requires_confirmation{out['requires_confirmation_accuracy_pct']}%")
    print(f"  event boundary       {out['event_boundary_accuracy_pct']}%")
    print("  counts:", json.dumps(out["counts"], ensure_ascii=False))
    print("  per_family:", json.dumps(out["per_family"], ensure_ascii=False))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
