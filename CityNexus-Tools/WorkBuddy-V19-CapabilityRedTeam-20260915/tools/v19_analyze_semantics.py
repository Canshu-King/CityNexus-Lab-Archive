"""Analyse the live semantic results: model-side vs server-side discrimination."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
EVIDENCE = LAB / "evidence"

ROWS = [json.loads(line) for line in (EVIDENCE / "semantic_live_results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def envelope_signature(row: dict[str, Any]) -> str:
    envelope = row.get("model_envelope") or {}
    return json.dumps(
        {
            "intent": envelope.get("intent"),
            "assertion_status": envelope.get("assertion_status"),
            "effective_time": envelope.get("effective_time"),
            "event_type": envelope.get("event_type"),
            "requested_action": envelope.get("requested_action"),
            "constraints": envelope.get("constraints"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def policy_signature(row: dict[str, Any]) -> str:
    policy = row.get("final_policy") or {}
    return json.dumps(
        {
            "route_intent": policy.get("route_intent"),
            "action": policy.get("action"),
            "event_type": policy.get("event_type"),
            "create_event": policy.get("create_event"),
            "verify_evidence": policy.get("verify_evidence"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def route_only(row: dict[str, Any]) -> str:
    return str((row.get("final_policy") or {}).get("route_intent"))


by_id = {row["id"]: row for row in ROWS}
pair_ids = sorted({row["pair_id"] for row in ROWS if row["pair_id"]})

model_disc = 0
policy_disc = 0
route_disc = 0
model_yes_policy_no: list[dict[str, Any]] = []
per_bucket: Counter[str] = Counter()
per_bucket_model: Counter[str] = Counter()

for pair_id in pair_ids:
    members = sorted(
        (by_id[key] for key in by_id if key.startswith(pair_id + "-")), key=lambda item: item["id"]
    )
    if len(members) != 2:
        continue
    a, b = members
    bucket = a["bucket"]
    per_bucket[bucket] += 1
    m = envelope_signature(a) != envelope_signature(b)
    p = policy_signature(a) != policy_signature(b)
    r = route_only(a) != route_only(b)
    model_disc += int(m)
    policy_disc += int(p)
    route_disc += int(r)
    if m:
        per_bucket_model[bucket] += 1
    if m and not p:
        model_yes_policy_no.append(
            {
                "pair_id": pair_id,
                "bucket": bucket,
                "a_id": a["id"],
                "a_text": a["raw_text"],
                "a_route": route_only(a),
                "a_constraints": (a.get("model_envelope") or {}).get("constraints"),
                "b_id": b["id"],
                "b_text": b["raw_text"],
                "b_route": route_only(b),
                "b_constraints": (b.get("model_envelope") or {}).get("constraints"),
            }
        )

total_pairs = sum(per_bucket.values())

# constraint payload vocabulary
constraint_types: Counter[str] = Counter()
strict_flags = 0
constraint_keys: Counter[str] = Counter()
for row in ROWS:
    for item in (row.get("model_envelope") or {}).get("constraints") or []:
        if isinstance(item, dict):
            constraint_types[str(item.get("type") or item.get("kind") or "?")] += 1
            for key in item:
                constraint_keys[key] += 1
            if item.get("strict") is True or item.get("hard") is True or item.get("mandatory") is True:
                strict_flags += 1

# assertion status distribution, focused on the negation/historical bucket
assertion_by_bucket: dict[str, Counter[str]] = {}
for row in ROWS:
    bucket = row["bucket"]
    status = (row.get("model_envelope") or {}).get("assertion_status") or "NONE"
    assertion_by_bucket.setdefault(bucket, Counter())[status] += 1

neg_hist = [row for row in ROWS if row["bucket"] == "negation_historical" and row["role"] == "NEGATED"]
neg_hist_flagged = [
    row for row in neg_hist
    if (row.get("model_envelope") or {}).get("assertion_status") in {"NEGATED", "HISTORICAL"}
]
neg_hist_resolved_constraint = [
    row for row in neg_hist
    if any(
        str((item or {}).get("status", "")).upper() in {"RESOLVED", "PAST", "CURED", "INACTIVE"}
        for item in ((row.get("model_envelope") or {}).get("constraints") or [])
        if isinstance(item, dict)
    )
]
neg_hist_routed_personal = [
    row for row in neg_hist if route_only(row) == "PERSONAL_ASSISTANCE"
]

injection = [row for row in ROWS if row["bucket"] == "injection_like"]
injection_created_event = [
    row for row in injection if (row.get("final_policy") or {}).get("create_event")
]
injection_hard_route = [
    row for row in injection
    if route_only(row) in {"DISRUPTION_REPORT", "REPLAN_REQUEST", "PREFERENCE_CHANGE"}
]

hard_soft = [row for row in ROWS if row["bucket"] == "hard_soft_pair"]
hs_routes = Counter((row.get("final_policy") or {}).get("route_intent") for row in hard_soft)
hs_by_role = {
    role: Counter(
        (row.get("final_policy") or {}).get("route_intent")
        for row in hard_soft
        if row["role"] == role
    )
    for role in ("HARD", "SOFT")
}

summary = {
    "rows": len(ROWS),
    "pairs": total_pairs,
    "model_side_discriminated_pairs": model_disc,
    "model_side_discrimination_rate": round(model_disc / total_pairs, 4) if total_pairs else None,
    "server_policy_discriminated_pairs": policy_disc,
    "server_policy_discrimination_rate": round(policy_disc / total_pairs, 4) if total_pairs else None,
    "server_route_only_discriminated_pairs": route_disc,
    "server_route_only_discrimination_rate": round(route_disc / total_pairs, 4) if total_pairs else None,
    "pairs_model_discriminated_but_server_collapsed": len(model_yes_policy_no),
    "pairs_per_bucket": dict(per_bucket),
    "model_discriminated_per_bucket": dict(per_bucket_model),
    "constraints_emitted_total": sum(constraint_types.values()),
    "constraint_type_top": constraint_types.most_common(15),
    "constraint_payload_keys": constraint_keys.most_common(15),
    "constraints_with_explicit_strict_flag": strict_flags,
    "assertion_status_by_bucket": {key: dict(value) for key, value in assertion_by_bucket.items()},
    "negated_cases": len(neg_hist),
    "negated_flagged_negated_or_historical": len(neg_hist_flagged),
    "negated_with_resolved_constraint_status": len(neg_hist_resolved_constraint),
    "negated_routed_to_personal_assistance": len(neg_hist_routed_personal),
    "injection_cases": len(injection),
    "injection_created_event": len(injection_created_event),
    "injection_routed_to_actionable_intent": len(injection_hard_route),
    "hard_soft_route_distribution": dict(hs_routes),
    "hard_soft_route_by_role": {key: dict(value) for key, value in hs_by_role.items()},
    "server_canonical_capability_present": False,
}

(EVIDENCE / "semantic_analysis.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8"
)
(EVIDENCE / "semantic_collapsed_pairs.json").write_text(
    json.dumps(model_yes_policy_no, ensure_ascii=False, indent=1), encoding="utf-8"
)
print(json.dumps({k: v for k, v in summary.items() if k not in {"constraint_type_top", "constraint_payload_keys", "assertion_status_by_bucket", "hard_soft_route_by_role"}}, ensure_ascii=False, indent=1))
print("\nconstraint types:", constraint_types.most_common(12))
print("payload keys:", constraint_keys.most_common(12))
