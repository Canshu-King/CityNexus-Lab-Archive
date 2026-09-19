"""V19.1 probe: canonicalization, negation, dedupe, numeric and time boundaries.

Pure module-level. Reads ``snapshot_<label>/backend`` (default snapshot_a) and
never touches the main worktree.

Usage:
    python tools/v191_probe_canonicalization.py [A|B]
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915")
EVID = LAB / "evidence"
LABEL = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
SNAP = LAB / f"snapshot_{LABEL.lower()}"

sys.path.insert(0, str(SNAP / "backend"))

from app.capabilities import (  # noqa: E402
    CAPABILITY_CODES,
    CAPABILITY_SEVERITIES,
    HARD_ACCESSIBILITY_CODES,
    accessibility_state,
    canonicalize_capabilities,
    capability_constraints,
    default_severity,
    extract_capabilities_from_text,
    summarize_capabilities,
)

HARD_CODES = sorted(HARD_ACCESSIBILITY_CODES)


def canon(items):
    return [dict(x) for x in canonicalize_capabilities(items)]


def gate(items):
    return [g["rule_code"] for g in capability_constraints(items)]


# ---------------------------------------------------------------------------
# 1. downgrade matrix
# ---------------------------------------------------------------------------
def downgrade_matrix() -> dict:
    cells = {}
    for code in HARD_CODES:
        for severity in ("HARD", "STRONG", "SOFT", None):
            for klass in ("HARD_ACCESSIBILITY_NEED", "SOFT_PREFERENCE", None):
                payload: dict = {"code": code}
                if severity:
                    payload["severity"] = severity
                if klass:
                    payload["class"] = klass
                out = canon([payload])
                cells[f"{code}|{severity}|{klass}"] = {
                    "in": payload,
                    "out_severity": out[0]["severity"] if out else None,
                    "out_class": out[0]["class"] if out else None,
                    "hard_gate": bool(gate(out)),
                    "downgraded": bool(out) and out[0]["severity"] != "HARD",
                }
    downgraded = [k for k, v in cells.items() if v["downgraded"]]
    return {
        "cells": cells,
        "total": len(cells),
        "downgraded": len(downgraded),
        "downgraded_keys": downgraded,
        "class_always_forced": all(
            v["out_class"] == "HARD_ACCESSIBILITY_NEED" for v in cells.values()
        ),
    }


# ---------------------------------------------------------------------------
# 2. dedupe
# ---------------------------------------------------------------------------
def dedupe() -> dict:
    cases = {
        "HARD_then_SOFT": [{"code": "STEP_FREE_REQUIRED", "severity": "HARD"},
                           {"code": "STEP_FREE_REQUIRED", "severity": "SOFT"}],
        "SOFT_then_HARD": [{"code": "STEP_FREE_REQUIRED", "severity": "SOFT"},
                           {"code": "STEP_FREE_REQUIRED", "severity": "HARD"}],
        "same_twice": [{"code": "AVOID_STAIRS", "severity": "HARD"},
                       {"code": "AVOID_STAIRS", "severity": "HARD"}],
        "STRONG_then_HARD": [{"code": "AVOID_STAIRS", "severity": "STRONG"},
                             {"code": "AVOID_STAIRS", "severity": "HARD"}],
        "three_way": [{"code": "AVOID_STAIRS", "severity": "SOFT"},
                      {"code": "AVOID_STAIRS", "severity": "HARD"},
                      {"code": "AVOID_STAIRS", "severity": "STRONG"}],
    }
    out = {}
    for label, items in cases.items():
        merged = canon(items)
        summary = summarize_capabilities(merged)
        codes = [m["code"] for m in merged]
        out[label] = {
            "input_severities": [i["severity"] for i in items],
            "rows": len(merged),
            "codes": codes,
            "distinct_codes": len(set(codes)),
            "severities": [m["severity"] for m in merged],
            "collapsed": len(merged) == len(set(codes)),
            "in_both_hard_and_soft": sorted(
                {c["code"] for c in summary["hard"]} & {c["code"] for c in summary["soft"]}
            ),
            "gate": gate(merged),
        }
    return out


# ---------------------------------------------------------------------------
# 3. negation / history: clause-local or global?
# ---------------------------------------------------------------------------
NEGATION_CASES = [
    ("no_exceptions_hard_need", "wheelchair 必须 step-free，没有例外", ["STEP_FREE_REQUIRED"]),
    ("dont_need_wheelchair", "I don't need a wheelchair, I can walk", []),
    ("used_not_wheelchair_now_hard", "我以前不用轮椅，但现在必须无障碍", ["STEP_FREE_REQUIRED"]),
    ("friend_hearsay_disagreed", "朋友说我可能需要轮椅，但我不这么认为", []),
    ("not_metro_need_taxi", "不是地铁，我需要出租车因为行李很多", ["LARGE_LUGGAGE"]),
    ("no_allergy_but_wheelchair", "我没有过敏，但我用轮椅，必须全程无障碍", ["STEP_FREE_REQUIRED"]),
    ("past_wheelchair_now_hard", "过去我坐轮椅，现在必须全程无障碍", ["STEP_FREE_REQUIRED"]),
    ("maybe_wheelchair_later", "说不定到时候我需要轮椅", []),
    ("if_wheelchair_then_tell", "if I end up in a wheelchair I'll tell you", []),
    ("historical_only", "我以前坐轮椅，现在好了", []),
    ("clean_hard_zh", "必须全程无障碍，一步楼梯都不能走", ["STEP_FREE_REQUIRED", "AVOID_STAIRS"]),
    ("clean_hard_en", "I use a wheelchair, every leg must be step-free", ["STEP_FREE_REQUIRED"]),
    ("no_stroller_this_time", "no stroller this time, ignore that", []),
    ("clean_stroller", "这次带婴儿车，需要坡道", ["STROLLER"]),
]


def negation() -> dict:
    out = {}
    for label, text, expected in NEGATION_CASES:
        caps = [dict(c) for c in extract_capabilities_from_text(text)]
        codes = [c["code"] for c in caps]
        missing = [e for e in expected if e not in codes]
        unexpected = [c for c in codes if c not in expected]
        out[label] = {
            "text": text,
            "expected_codes": expected,
            "actual": [{"code": c["code"], "severity": c["severity"]} for c in caps],
            "missing": missing,
            "unexpected": unexpected,
            "verdict": "ok" if not missing and not unexpected else "wrong",
        }
    wrong = [k for k, v in out.items() if v["verdict"] == "wrong"]
    return {"cases": out, "wrong": wrong, "wrong_count": len(wrong), "total": len(out)}


# ---------------------------------------------------------------------------
# 4. walking numeric boundaries
# ---------------------------------------------------------------------------
WALKING_VALUES = [
    ("zero", "走路不能超过 0 米"),
    ("one", "走路不能超过 1 米"),
    ("hundred", "走路不能超过 100 米"),
    ("four99", "走路不能超过 499 米"),
    ("five00", "走路不能超过 500 米"),
    ("five01", "走路不能超过 501 米"),
    ("thousand", "走路不能超过 1000 米"),
    ("tenk", "走路不能超过 10000 米"),
    ("negative", "走路不能超过 -500 米"),
    ("huge", "走路不能超过 99999999 米"),
    ("quoted", '走路不能超过 "500" 米'),
    ("unit_m", "走路不能超过 500m"),
    ("unit_km", "走路不能超过 0.5 公里"),
    ("km_word", "走路不能超过 1 公里"),
    ("null_word", "走路不能超过 null 米"),
    ("missing_number", "走路不能超过 米"),
    ("chinese_numeral", "走路不能超过五百米"),
    ("en_must", "I cannot walk more than 500 metres per leg"),
    ("en_under", "avoid long walks, under 400 m per leg"),
    ("max_walk_zh", "我最多走 500 米，超过就走不动了"),
    ("hard_zh", "走路不能超过 500m，这是硬性要求"),
]


def walking() -> dict:
    out = {}
    for label, text in WALKING_VALUES:
        caps = [dict(c) for c in extract_capabilities_from_text(text)]
        walk = [c for c in caps if c["code"].startswith("MAX_")]
        out[label] = {
            "text": text,
            "codes": [c["code"] for c in caps],
            "walking_params": [c["params"] for c in walk],
            "extracted": bool(walk),
            "max_m": (walk[0]["params"].get("max_m") if walk else None),
        }
    values = sorted({v["max_m"] for v in out.values() if v["max_m"] is not None})
    return {
        "cases": out,
        "distinct_max_m": values,
        "extracted_count": sum(1 for v in out.values() if v["extracted"]),
        "total": len(out),
        "all_same_outcome": len(values) <= 1,
    }


# ---------------------------------------------------------------------------
# 5. rest / nap windows
# ---------------------------------------------------------------------------
WINDOW_CASES = [
    ("midday_12_14", "老人中午 12 点到 14 点必须回酒店休息"),
    ("midday_colon", "中午 12:00-14:00 必须回酒店休息"),
    ("nap_1_3", "宝宝下午 1 点到 3 点必须睡午觉，不能安排活动"),
    ("nap_naptime", "the baby needs naptime at 13:00-15:00"),
    ("en_rest_between", "I must rest at the hotel between 12:00 and 14:00"),
    ("invalid_end_before_start", "中午 14:00 到 12:00 必须回酒店休息"),
    ("cross_midnight", "必须从 23:00 休息到 01:00"),
    ("outside_journey", "凌晨 03:00 到 04:00 必须休息"),
    ("no_times", "老人中午必须休息"),
    ("pm_form", "rest from 1pm to 3pm"),
]


def windows() -> dict:
    out = {}
    for label, text in WINDOW_CASES:
        caps = [dict(c) for c in extract_capabilities_from_text(text)]
        win = [c for c in caps if c["code"] in {"MIDDAY_REST_WINDOW", "INFANT_NAP_WINDOW"}]
        out[label] = {
            "text": text,
            "codes": [c["code"] for c in caps],
            "params": [c["params"] for c in win],
            "extracted": bool(win),
        }
    return {
        "cases": out,
        "extracted_count": sum(1 for v in out.values() if v["extracted"]),
        "total": len(out),
    }


# ---------------------------------------------------------------------------
# 6. scope from language
# ---------------------------------------------------------------------------
SCOPE_CASES = [
    ("this_trip_only", "这次旅行我不能走太多路"),
    ("every_trip", "以后每次旅行我都不能走太多路"),
    ("permanent", "我用轮椅，这是永久情况，不只是这次旅行"),
    ("today_only", "今天临时腿疼，少走点"),
    ("not_this_trip", "不只是这次，我一直用轮椅"),
]


def scope() -> dict:
    out = {}
    for label, text in SCOPE_CASES:
        caps = [dict(c) for c in extract_capabilities_from_text(text)]
        out[label] = {
            "text": text,
            "scopes": [c["scope"] for c in caps],
            "codes": [c["code"] for c in caps],
        }
    dist = Counter(s for v in out.values() for s in v["scopes"])
    return {"cases": out, "scope_distribution": dict(dist)}


def main() -> int:
    result = {
        "snapshot": LABEL,
        "capability_codes": list(CAPABILITY_CODES),
        "severities": list(CAPABILITY_SEVERITIES),
        "hard_accessibility_codes": HARD_CODES,
        "default_severity": {
            code: {
                "plain": default_severity(code, hard_asserted=False),
                "hard_asserted": default_severity(code, hard_asserted=True),
            }
            for code in CAPABILITY_CODES
        },
        "downgrade_matrix": downgrade_matrix(),
        "dedupe": dedupe(),
        "negation": negation(),
        "walking": walking(),
        "windows": windows(),
        "scope": scope(),
        "accessibility_state": {
            "missing": accessibility_state(None),
            "empty": accessibility_state({}),
            "verified": accessibility_state({"evidence_status": "VERIFIED"}),
            "unknown": accessibility_state({"evidence_status": "UNKNOWN"}),
            "stairs": accessibility_state({"stairs": True}),
            "step_free_true": accessibility_state({"step_free": True}),
            "step_free_false": accessibility_state({"step_free": False}),
            "name_only": accessibility_state({"name": "Wheelchair ramp entrance"}),
            "unknown_treated_as_accessible": accessibility_state({}) == "ACCESSIBILITY_VERIFIED",
        },
    }
    out = EVID / f"canonicalization_{LABEL.lower()}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps({
        "snapshot": LABEL,
        "downgrade": {
            "total": result["downgrade_matrix"]["total"],
            "downgraded": result["downgrade_matrix"]["downgraded"],
        },
        "dedupe": {k: {"rows": v["rows"], "collapsed": v["collapsed"],
                       "in_both": v["in_both_hard_and_soft"]} for k, v in result["dedupe"].items()},
        "negation": {"wrong": result["negation"]["wrong_count"], "total": result["negation"]["total"],
                     "wrong_keys": result["negation"]["wrong"]},
        "walking": {"extracted": result["walking"]["extracted_count"],
                    "total": result["walking"]["total"],
                    "distinct_values": result["walking"]["distinct_max_m"]},
        "windows": {"extracted": result["windows"]["extracted_count"],
                    "total": result["windows"]["total"]},
        "scope": result["scope"]["scope_distribution"],
        "accessibility_state": result["accessibility_state"],
        "written": str(out),
    }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
