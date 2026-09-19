"""Measure the delta introduced by the new ``app.capabilities`` module.

The V19 findings were measured against the 10:23 snapshot.  Codex landed
``backend/app/capabilities.py`` at 10:53 during the run, so this script
re-measures the *same* 494-case corpus against the new deterministic extractor
in ``repo_copy_current`` and reports the before/after numbers.

It imports ``app.capabilities`` **standalone** - the main tree was mid-write at
snapshot time (``app/main.py`` imports ``capability_payload``, which the module
does not yet define), so ``app.main`` cannot be imported at all.

Usage:
    python tools/v19_verify_current_capabilities.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
CURRENT = LAB / "repo_copy_current"
EVID = LAB / "evidence"

sys.path.insert(0, str(CURRENT / "backend"))

from app.capabilities import (  # noqa: E402
    ACCESSIBILITY_STATES,
    CAPABILITY_CODES,
    CAPABILITY_CLASSES,
    CAPABILITY_SEVERITIES,
    HARD_ACCESSIBILITY_CODES,
    accessibility_state,
    canonicalize_capabilities,
    capability_constraints,
    default_severity,
    extract_capabilities_from_text,
    summarize_capabilities,
)


def load_cases() -> list[dict]:
    with (EVID / "semantic_cases.jsonl").open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def text_of(case: dict) -> str:
    """The corpus uses ``text``; the live-run file uses ``raw_text``."""
    return case.get("raw_text") or case.get("text") or ""


def sig(caps) -> str:
    return json.dumps(sorted((c["code"], c["severity"]) for c in caps), ensure_ascii=False)


def main() -> int:
    cases = load_cases()
    out: dict = {
        "module": "repo_copy_current/backend/app/capabilities.py",
        "cases": len(cases),
        "vocabulary": {
            "capability_codes": list(CAPABILITY_CODES),
            "capability_classes": list(CAPABILITY_CLASSES),
            "severities": list(CAPABILITY_SEVERITIES),
            "accessibility_states": list(ACCESSIBILITY_STATES),
            "hard_accessibility_codes": sorted(HARD_ACCESSIBILITY_CODES),
        },
    }

    per_case: dict[str, tuple] = {}
    for case in cases:
        per_case[case["id"]] = extract_capabilities_from_text(text_of(case))

    covered = sum(1 for v in per_case.values() if v)
    out["coverage"] = {
        "cases_with_any_capability": covered,
        "rate": round(covered / len(cases), 4),
        "severity_distribution": dict(
            Counter(c["severity"] for v in per_case.values() for c in v)
        ),
        "code_distribution": dict(
            Counter(c["code"] for v in per_case.values() for c in v).most_common(30)
        ),
        "scope_distribution": dict(
            Counter(c["scope"] for v in per_case.values() for c in v)
        ),
    }
    out["coverage_by_bucket"] = {
        bucket: {
            "cases": len(rows),
            "covered": sum(1 for r in rows if per_case[r["id"]]),
            "rate": round(sum(1 for r in rows if per_case[r["id"]]) / len(rows), 4),
        }
        for bucket, rows in sorted(
            (
                (b, [c for c in cases if c["bucket"] == b])
                for b in {c["bucket"] for c in cases}
            ),
            key=lambda kv: kv[0],
        )
    }

    # ---- pair discrimination (same 167 hard/soft + negation + ambiguous pairs) --
    pairs: dict[str, dict[str, str]] = defaultdict(dict)
    pair_bucket: dict[str, str] = {}
    for case in cases:
        if not case.get("pair_id"):
            continue
        pair_bucket[case["pair_id"]] = case["bucket"]
        pairs[case["pair_id"]][case["role"]] = sig(per_case[case["id"]])
    by_bucket: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "discriminated": 0})
    for pair_id, roles in pairs.items():
        if len(roles) < 2:
            continue
        counts = by_bucket[pair_bucket[pair_id]]
        counts["total"] += 1
        if len(set(roles.values())) > 1:
            counts["discriminated"] += 1
    out["pair_discrimination"] = {
        bucket: {
            **counts,
            "rate": round(counts["discriminated"] / counts["total"], 4) if counts["total"] else None,
        }
        for bucket, counts in sorted(by_bucket.items())
    }
    total_pairs = sum(v["total"] for v in by_bucket.values())
    total_disc = sum(v["discriminated"] for v in by_bucket.values())
    out["pair_discrimination_total"] = {
        "total": total_pairs,
        "discriminated": total_disc,
        "rate": round(total_disc / total_pairs, 4) if total_pairs else None,
    }

    # ---- negation: the extractor must stay silent on NEGATED, speak on POSITIVE
    neg_rows = [c for c in cases if c["bucket"] == "negation_historical"]
    neg_only = [c for c in neg_rows if c["role"] == "NEGATED"]
    pos_only = [c for c in neg_rows if c["role"] == "POSITIVE"]
    out["negation"] = {
        "negated_cases": len(neg_only),
        "negated_returning_nothing": sum(1 for c in neg_only if not per_case[c["id"]]),
        "positive_cases": len(pos_only),
        "positive_returning_something": sum(1 for c in pos_only if per_case[c["id"]]),
        "positive_false_negatives": [
            {
                "id": c["id"],
                "topic": c["topic"],
                "text": text_of(c),
                "expected": c.get("expected"),
            }
            for c in pos_only
            if not per_case[c["id"]]
        ],
    }

    # ---- the text-global negation guard (new risk introduced by the module) ----
    mixed = [
        "我以前不用轮椅，但现在必须全程 step-free",
        "I used to walk fine but now I use a wheelchair and need every leg step-free",
        "我没有过敏，但我用轮椅，必须全程无障碍",
        "过去我坐轮椅，现在不需要了",
        "不是楼梯的问题，我用轮椅，必须全程无障碍",
    ]
    out["text_global_negation_guard"] = [
        {"text": t, "caps": [c["code"] for c in extract_capabilities_from_text(t)]} for t in mixed
    ]

    # ---- value reading -------------------------------------------------------
    def read(text: str) -> list[dict]:
        return [
            {"code": c["code"], "severity": c["severity"], "params": c["params"]}
            for c in extract_capabilities_from_text(text)
        ]

    out["value_reading"] = {
        "walking": [
            {"text": t, "caps": read(t)}
            for t in (
                "走路不能超过 500m，这是硬性要求",
                "walking 最好别超过 500m",
                "我带 78 岁母亲，最多走 500 米，每 60 分钟要休息",
                "少走点路，最好每段不超过 300 米",
                "avoid long walks, under 400 m per leg",
            )
        ],
        "windows": [
            {"text": t, "caps": read(t)}
            for t in (
                "宝宝下午 1 点到 3 点必须睡午觉，不能安排活动",
                "I must rest at the hotel between 12:00 and 14:00",
                "老人中午必须休息",
            )
        ],
        "accessibility": [
            {"text": t, "caps": read(t)}
            for t in (
                "我用轮椅，必须全程 step-free，一步楼梯都不能走",
                "必须全程无障碍，一步楼梯都不能走",
                "最好少走点楼梯，能坐电梯就坐电梯",
                "I use a wheelchair, every leg must be step-free",
                "no stairs please",
            )
        ],
    }

    # ---- canonicalization: the hard-downgrade attack --------------------------
    attacks = {}
    for label, payload in {
        "model_says_HARD": {"code": "STEP_FREE_REQUIRED", "severity": "HARD", "class": "HARD_ACCESSIBILITY_NEED"},
        "model_says_STRONG": {"code": "STEP_FREE_REQUIRED", "severity": "STRONG", "class": "HARD_ACCESSIBILITY_NEED"},
        "model_says_SOFT": {"code": "STEP_FREE_REQUIRED", "severity": "SOFT", "class": "SOFT_PREFERENCE"},
        "model_says_SOFT_class_ok": {"code": "STEP_FREE_REQUIRED", "severity": "SOFT", "class": "HARD_ACCESSIBILITY_NEED"},
        "model_omits_severity": {"code": "STEP_FREE_REQUIRED"},
        "avoid_stairs_says_SOFT": {"code": "AVOID_STAIRS", "severity": "SOFT", "class": "SOFT_PREFERENCE"},
        "walking_limit_says_SOFT": {"code": "MAX_WALKING_PER_LEG_M", "severity": "SOFT", "params": {"max_m": 500}},
        "unknown_code": {"code": "NOT_A_REAL_CODE", "severity": "HARD"},
    }.items():
        canon = canonicalize_capabilities([payload])
        gates = capability_constraints(canon)
        attacks[label] = {
            "input": payload,
            "canonical_severity": canon[0]["severity"] if canon else None,
            "canonical_class": canon[0]["class"] if canon else None,
            "kept": bool(canon),
            "produces_hard_gate": bool(gates),
            "gate_codes": [g["rule_code"] for g in gates],
        }
    out["hard_downgrade_attack_matrix"] = attacks
    out["hard_downgrade_defeated"] = {
        label: (row["canonical_severity"] == "HARD")
        for label, row in attacks.items()
        if label.endswith("says_SOFT") or label == "avoid_stairs_says_SOFT"
    }

    # ---- accessibility evidence state ---------------------------------------
    out["accessibility_state"] = {
        "missing": accessibility_state(None),
        "empty": accessibility_state({}),
        "verified": accessibility_state({"evidence_status": "VERIFIED"}),
        "unknown_status": accessibility_state({"evidence_status": "UNKNOWN"}),
        "stairs": accessibility_state({"stairs": True}),
        "step_free_true": accessibility_state({"step_free": True}),
        "step_free_false": accessibility_state({"step_free": False}),
        "guessed_from_name": accessibility_state({"name": "Wheelchair ramp entrance"}),
        "unknown_treated_as_accessible": accessibility_state({}) == "ACCESSIBILITY_VERIFIED",
    }

    # ---- gate translation ----------------------------------------------------
    sample_caps = extract_capabilities_from_text("我用轮椅，必须全程 step-free，一步楼梯都不能走")
    out["gate_translation_sample"] = {
        "caps": list(sample_caps),
        "constraints": capability_constraints(sample_caps),
    }
    soft_caps = extract_capabilities_from_text("最好少走点楼梯，能坐电梯就坐电梯")
    out["gate_translation_soft_sample"] = {
        "caps": list(soft_caps),
        "constraints": capability_constraints(soft_caps),
        "note": "SOFT/STRONG must never reach the gate",
    }

    # ---- the exact V19 attack sentence, end to end ---------------------------
    hard_sentence = "必须全程无障碍，一步楼梯都不能走"
    soft_sentence = "最好少走点楼梯，能坐电梯就坐电梯"
    h, s = extract_capabilities_from_text(hard_sentence), extract_capabilities_from_text(soft_sentence)
    out["v19_attack_sentences"] = {
        "hard": {
            "text": hard_sentence,
            "caps": list(h),
            "gate": capability_constraints(h),
            "summary": summarize_capabilities(h),
        },
        "soft": {
            "text": soft_sentence,
            "caps": list(s),
            "gate": capability_constraints(s),
            "summary": summarize_capabilities(s),
        },
        "still_indistinguishable_at_gate": bool(capability_constraints(h))
        == bool(capability_constraints(s)),
    }

    # ---- severity defaults ---------------------------------------------------
    out["default_severity"] = {
        code: {
            "plain": default_severity(code, hard_asserted=False),
            "hard_asserted": default_severity(code, hard_asserted=True),
        }
        for code in CAPABILITY_CODES
    }

    (EVID / "capability_fix_delta.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
