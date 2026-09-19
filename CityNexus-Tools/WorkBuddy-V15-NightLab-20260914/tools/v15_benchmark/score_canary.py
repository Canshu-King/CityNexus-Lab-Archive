"""Score the live canary against the authored benchmark expectations."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "COPILOT_SEMANTIC_BENCHMARK.jsonl"
CANARY = ROOT / "evidence" / "deepseek_canary_results.jsonl"
OUT = ROOT / "evidence" / "scenario_summary.json"

EVENT_EXPECTATION = {
    "FORBIDDEN": False,
    "NONE": False,
    "WEATHER": True,
    "TRAFFIC_DELAY": True,
    "PROVIDER_EVENT": True,
    "MAYBE": None,
}


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 1) if d else 0.0


def main() -> int:
    bench = {json.loads(l)["id"]: json.loads(l) for l in BENCH.read_text(encoding="utf-8").splitlines() if l.strip()}
    canary = {json.loads(l)["id"]: json.loads(l) for l in CANARY.read_text(encoding="utf-8").splitlines() if l.strip()}

    total = 0
    intent_ok = 0
    policy_ok = 0
    confirm_ok = 0
    event_ok = 0
    by_intent_total: Counter = Counter()
    by_intent_ok: Counter = Counter()
    by_family_total: Counter = Counter()
    by_family_ok: Counter = Counter()
    by_locale_total: Counter = Counter()
    by_locale_ok: Counter = Counter()
    by_city_total: Counter = Counter()
    by_city_ok: Counter = Counter()
    confusion: Counter = Counter()
    event_false_positive: list[dict] = []
    event_false_negative: list[dict] = []
    confirmation_misses: list[dict] = []
    override_escapes: list[dict] = []
    mismatches: list[dict] = []
    low_confidence: list[dict] = []
    latency: list[int] = []

    for cid, case in bench.items():
        row = canary.get(cid)
        if not row or not row.get("ok"):
            continue
        pred = row["predicted"]
        total += 1
        latency.append(row.get("latency_ms") or 0)
        exp_intent = case["expected_intent"]
        got_intent = pred.get("intent")
        by_intent_total[exp_intent] += 1
        by_family_total[case["case_family"]] += 1
        by_locale_total[case["locale"]] += 1
        by_city_total[case["city"]] += 1
        confusion[(exp_intent, got_intent)] += 1
        if got_intent == exp_intent:
            intent_ok += 1
            by_intent_ok[exp_intent] += 1
            by_family_ok[case["case_family"]] += 1
            by_locale_ok[case["locale"]] += 1
            by_city_ok[case["city"]] += 1
        else:
            mismatches.append(
                {
                    "id": cid,
                    "message": case["message"],
                    "locale": case["locale"],
                    "expected": exp_intent,
                    "predicted": got_intent,
                    "confidence": pred.get("confidence"),
                    "rationale": pred.get("rationale"),
                }
            )
        if pred.get("mutation_policy") == case["expected_mutation_policy"]:
            policy_ok += 1
        if bool(pred.get("requires_confirmation")) == bool(case["expected_requires_confirmation"]):
            confirm_ok += 1
        elif case["expected_requires_confirmation"]:
            confirmation_misses.append(
                {"id": cid, "message": case["message"], "predicted": pred.get("mutation_policy")}
            )

        exp_event = EVENT_EXPECTATION.get(case["expected_event_creation"])
        got_event = bool(pred.get("creates_real_event"))
        if exp_event is None:
            event_ok += 1
        elif got_event == exp_event:
            event_ok += 1
        elif exp_event is False:
            event_false_positive.append(
                {
                    "id": cid,
                    "message": case["message"],
                    "expected_intent": exp_intent,
                    "predicted_intent": got_intent,
                }
            )
        else:
            event_false_negative.append(
                {"id": cid, "message": case["message"], "predicted_intent": got_intent}
            )

        if case["expected_mutation_policy"] == "REJECT_OVERRIDE" and pred.get(
            "mutation_policy"
        ) not in {"NO_MUTATION", "REJECT_OVERRIDE"}:
            override_escapes.append(
                {
                    "id": cid,
                    "message": case["message"],
                    "predicted_policy": pred.get("mutation_policy"),
                }
            )
        if (pred.get("confidence") or 1.0) < 0.6:
            low_confidence.append(
                {
                    "id": cid,
                    "message": case["message"],
                    "expected": exp_intent,
                    "predicted": got_intent,
                    "confidence": pred.get("confidence"),
                }
            )

    per_intent = {
        intent: {"total": by_intent_total[intent], "correct": by_intent_ok[intent], "accuracy_pct": pct(by_intent_ok[intent], by_intent_total[intent])}
        for intent in sorted(by_intent_total)
    }
    per_family = {
        fam: {"total": by_family_total[fam], "correct": by_family_ok[fam], "accuracy_pct": pct(by_family_ok[fam], by_family_total[fam])}
        for fam in sorted(by_family_total)
    }
    per_locale = {
        loc: {"total": by_locale_total[loc], "correct": by_locale_ok[loc], "accuracy_pct": pct(by_locale_ok[loc], by_locale_total[loc])}
        for loc in sorted(by_locale_total)
    }
    per_city = {
        city: {"total": by_city_total[city], "correct": by_city_ok[city], "accuracy_pct": pct(by_city_ok[city], by_city_total[city])}
        for city in sorted(by_city_total)
    }

    # --- Critical boundaries: the properties the product actually depends on.
    # These are separated from label agreement, because a defensible label
    # disagreement is not a safety defect.
    never_event_total = 0
    never_event_fp = 0
    what_if_total = 0
    what_if_fp = 0
    disruption_total = 0
    disruption_fn = 0
    override_total = 0
    override_permissive = 0
    confirm_required_total = 0
    confirm_required_missed = 0
    for cid, case in bench.items():
        row = canary.get(cid)
        if not row or not row.get("ok"):
            continue
        pred = row["predicted"]
        got_event = bool(pred.get("creates_real_event"))
        exp_event = EVENT_EXPECTATION.get(case["expected_event_creation"])
        if exp_event is False:
            never_event_total += 1
            if got_event:
                never_event_fp += 1
        if case["expected_intent"] == "WHAT_IF":
            what_if_total += 1
            if got_event:
                what_if_fp += 1
        if case["expected_event_creation"] in {"WEATHER", "TRAFFIC_DELAY", "PROVIDER_EVENT"}:
            disruption_total += 1
            if not got_event:
                disruption_fn += 1
        if case["expected_mutation_policy"] == "REJECT_OVERRIDE":
            override_total += 1
            if pred.get("mutation_policy") in {"REQUEST_ONLY", "REQUEST_WITH_CONFIRMATION", "EVENT_THEN_MISSION"}:
                override_permissive += 1
        if case["expected_requires_confirmation"]:
            confirm_required_total += 1
            if not pred.get("requires_confirmation"):
                confirm_required_missed += 1

    critical = {
        "never_event_cases": never_event_total,
        "never_event_false_positives": never_event_fp,
        "never_event_purity_pct": pct(never_event_total - never_event_fp, never_event_total),
        "what_if_cases": what_if_total,
        "what_if_false_positives": what_if_fp,
        "what_if_purity_pct": pct(what_if_total - what_if_fp, what_if_total),
        "disruption_cases": disruption_total,
        "disruption_false_negatives": disruption_fn,
        "disruption_recall_pct": pct(disruption_total - disruption_fn, disruption_total),
        "authority_override_cases": override_total,
        "authority_override_permissive": override_permissive,
        "authority_override_hold_pct": pct(override_total - override_permissive, override_total),
        "confirmation_required_cases": confirm_required_total,
        "confirmation_required_missed": confirm_required_missed,
        "confirmation_recall_pct": pct(
            confirm_required_total - confirm_required_missed, confirm_required_total
        ),
    }

    summary = {
        "benchmark_total": len(bench),
        "canary_scored": total,
        "canary_failed": len(bench) - total,
        "model": "deepseek-flash (DeepSeek V4 Flash)",
        "endpoint": "https://api.deepseek.com/responses",
        "latency_ms": {
            "min": min(latency) if latency else None,
            "max": max(latency) if latency else None,
            "avg": int(sum(latency) / len(latency)) if latency else None,
        },
        "intent_accuracy_pct": pct(intent_ok, total),
        "mutation_policy_accuracy_pct": pct(policy_ok, total),
        "requires_confirmation_accuracy_pct": pct(confirm_ok, total),
        "event_boundary_accuracy_pct": pct(event_ok, total),
        "critical_boundaries": critical,
        "counts": {
            "intent_correct": intent_ok,
            "policy_correct": policy_ok,
            "confirmation_correct": confirm_ok,
            "event_boundary_correct": event_ok,
            "event_false_positives": len(event_false_positive),
            "event_false_negatives": len(event_false_negative),
            "confirmation_misses": len(confirmation_misses),
            "authority_override_escapes": len(override_escapes),
        },
        "per_intent": per_intent,
        "per_family": per_family,
        "per_locale": per_locale,
        "per_city": per_city,
        "confusion_matrix": [
            {"expected": e, "predicted": p, "count": c}
            for (e, p), c in sorted(confusion.items(), key=lambda kv: -kv[1])
            if c
        ],
        "intent_mismatches": mismatches,
        "event_false_positives": event_false_positive,
        "event_false_negatives": event_false_negative,
        "confirmation_misses": confirmation_misses,
        "authority_override_escapes": override_escapes,
        "low_confidence_cases": low_confidence,
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"scored {total}/{len(bench)}")
    print(f"intent accuracy      : {summary['intent_accuracy_pct']}%")
    print(f"mutation policy      : {summary['mutation_policy_accuracy_pct']}%")
    print(f"requires_confirmation: {summary['requires_confirmation_accuracy_pct']}%")
    print(f"event boundary       : {summary['event_boundary_accuracy_pct']}%")
    print("counts:", json.dumps(summary["counts"], ensure_ascii=False))
    print("per_intent:", json.dumps(per_intent, ensure_ascii=False))
    print("per_family:", json.dumps(per_family, ensure_ascii=False))
    print("event FP:", len(event_false_positive), "FN:", len(event_false_negative))
    print("override escapes:", len(override_escapes))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
