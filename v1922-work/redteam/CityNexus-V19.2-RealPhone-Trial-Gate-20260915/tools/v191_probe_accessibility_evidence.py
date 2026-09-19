"""V19.1 EAC provider-evidence scope attack + EAC patch validation.

Read-only.  Loads the EAC reference implementation by *file path* (never
importing the EAC package tree, never touching the main tree) and runs the tag
matrix the task brief mandates:

    toilets:wheelchair=yes        MUST NOT satisfy STEP_FREE_REQUIRED
    ramp=yes / elevator=yes       MUST NOT prove step-free
    wheelchair=yes + step_count=5 MUST be CONFLICT
    list/tuple tag forms          MUST NOT be silently dropped
    route-level step-free         MUST stay unknown without route evidence
    generic overall_state         MUST NOT propagate across subject/code

Then replays the two mandated false-HARD sentences plus the clause/history
corpus through the EAC extractor and the current snapshot extractor so the
report can compare EAC_REFERENCE vs FINAL_V19 directly.

Output: evidence/accessibility_evidence_scope.json
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
LAB = HERE.parents[1]
EAC = Path(r"D:\moodle\CityNexus-Tools\DSH-EAC-V19.1-AutonomousProductLab-20260915")
SNAP_B = LAB / "snapshot_b" / "backend"
SNAP_A = LAB / "snapshot_a" / "backend"
SNAP_C = LAB / "snapshot_c" / "backend"
OUT = LAB / "evidence" / "accessibility_evidence_scope.json"


def load(path: Path, name: str):
    """Load a module from an explicit file path under a private name."""
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


EAC_OSM = load(EAC / "lab" / "runtime" / "backend" / "app" / "integrations"
               / "accessibility" / "osm.py", "_eac_osm")
EAC_CAPS = load(EAC / "lab" / "runtime" / "backend" / "app" / "capabilities.py",
                "_eac_caps")
B_CAPS = load(SNAP_B / "app" / "capabilities.py", "_b_caps")
A_CAPS = load(SNAP_A / "app" / "capabilities.py", "_a_caps")
C_CAPS = load(SNAP_C / "app" / "capabilities.py", "_c_caps")


# --------------------------------------------------------------------------
# A. provider evidence tag matrix
# --------------------------------------------------------------------------
# (case_id, tags, expectation)
#   expectation is what the brief demands the implementation do.
TAG_CASES: list[tuple[str, object, str]] = [
    ("toilet_only", {"toilets:wheelchair": "yes"}, "not_step_free"),
    ("toilet_no", {"toilets:wheelchair": "no"}, "conflict"),
    ("ramp_only", {"ramp": "yes"}, "not_step_free"),
    ("ramp_wheelchair_only", {"ramp:wheelchair": "yes"}, "not_step_free"),
    ("elevator_only", {"elevator": "yes"}, "not_step_free"),
    ("highway_elevator_only", {"highway:elevator": "yes"}, "not_step_free"),
    ("wheelchair_yes_step_count_5", {"wheelchair": "yes", "step_count": 5},
     "conflict"),
    ("wheelchair_yes_steps_yes", {"wheelchair": "yes", "steps": "yes"},
     "conflict"),
    ("wheelchair_yes_highway_steps", {"wheelchair": "yes", "highway": "steps"},
     "conflict"),
    ("wheelchair_yes_only", {"wheelchair": "yes"}, "step_free_ok"),
    ("wheelchair_designated_only", {"wheelchair": "designated"}, "step_free_ok"),
    ("wheelchair_no_only", {"wheelchair": "no"}, "conflict"),
    ("wheelchair_limited", {"wheelchair": "limited"}, "not_step_free"),
    ("entrance_wheelchair_only", {"entrance:wheelchair": "yes"},
     "not_step_free_or_verified"),
    ("kerb_only", {"kerb": "lowered"}, "not_step_free"),
    ("tactile_only", {"tactile_paving": "yes"}, "not_step_free"),
    ("empty_tags", {}, "unknown"),
    ("toilet_plus_ramp", {"toilets:wheelchair": "yes", "ramp": "yes"},
     "not_step_free"),
    ("toilet_plus_wheelchair_no",
     {"toilets:wheelchair": "yes", "wheelchair": "no"}, "conflict"),
    ("toilet_plus_ramp_plus_wheelchair_yes",
     {"toilets:wheelchair": "yes", "ramp": "yes", "wheelchair": "yes"},
     "step_free_ok"),
    # ---- list / tuple forms must not be silently dropped ----
    ("list_value_wheelchair", {"wheelchair": ["yes"]}, "no_silent_drop"),
    ("tuple_value_ramp", {"ramp": ("yes",)}, "no_silent_drop"),
    ("list_value_step_count", {"step_count": [5]}, "no_silent_drop"),
    ("list_value_toilets", {"toilets:wheelchair": ["yes"]}, "no_silent_drop"),
    ("sequence_of_kv_strings", ["wheelchair=yes", "ramp=yes"], "no_silent_drop"),
    ("tags_nested_under_key", {"tags": {"wheelchair": "yes"}}, "no_silent_drop"),
]

STEP_FREE_VERIFIED = "ACCESSIBILITY_VERIFIED"


def evaluate(case_id: str, tags: object, expectation: str) -> dict:
    row: dict = {"case_id": case_id, "expectation": expectation}
    if EAC_OSM is None:
        row["error"] = "eac osm.py missing"
        return row
    try:
        facts = EAC_OSM.evidence_from_osm_tags(tags)
    except Exception as exc:  # noqa: BLE001 - record, never raise
        row["error"] = f"{type(exc).__name__}: {exc}"
        return row
    items = [f.as_dict() for f in facts]
    overall = EAC_OSM.overall_accessibility_state(facts)
    # What the feasibility gate would conclude (EAC accessibility_state reads
    # the aggregate `evidence_status` string).
    state = EAC_CAPS.accessibility_state({"evidence_status": overall})
    non_empty_tags = bool(tags) if not isinstance(tags, (list, tuple)) else bool(tags)
    row.update(
        {
            "fact_count": len(items),
            "facts": [
                {"state": i["state"], "code": i["code"], "subject": i["subject"],
                 "confidence_type": i["confidence_type"]}
                for i in items
            ],
            "overall_state": overall,
            "gate_state_for_step_free": state,
            "step_free_satisfied": state == STEP_FREE_VERIFIED,
            "subjects": sorted({i["subject"] for i in items}),
            "codes": sorted({i["code"] for i in items}),
            "silently_dropped": non_empty_tags and not items,
        }
    )
    # Was step-free satisfied by a fact that is not a PLACE/ROUTE step-free fact?
    if row["step_free_satisfied"]:
        offending = [
            i for i in items
            if i["state"] == "ACCESSIBILITY_VERIFIED"
            and not (i["subject"] == "PLACE" and i["code"] == "WHEELCHAIR_ACCESS")
        ]
        row["verified_by_non_step_free_fact"] = [
            {"code": i["code"], "subject": i["subject"]} for i in offending
        ]
        row["leak"] = bool(offending)
    else:
        row["verified_by_non_step_free_fact"] = []
        row["leak"] = False
    # expectation verdict
    if expectation == "step_free_ok":
        row["verdict"] = "PASS" if row["step_free_satisfied"] else "FAIL"
    elif expectation == "conflict":
        row["verdict"] = "PASS" if state == "ACCESSIBILITY_CONFLICT" else "FAIL"
    elif expectation == "unknown":
        row["verdict"] = (
            "PASS" if state in ("NEEDS_LIVE_EVIDENCE", "ACCESSIBILITY_UNVERIFIED")
            else "FAIL"
        )
    elif expectation == "not_step_free_or_verified":
        row["verdict"] = "PASS" if not row["step_free_satisfied"] else "FAIL"
    elif expectation == "not_step_free":
        row["verdict"] = "PASS" if not row["step_free_satisfied"] else "FAIL"
    elif expectation == "no_silent_drop":
        row["verdict"] = "PASS" if not row["silently_dropped"] else "FAIL"
    else:
        row["verdict"] = "INCONCLUSIVE"
    return row


# --------------------------------------------------------------------------
# B. EAC patch validation: the mandated false-HARD sentences
# --------------------------------------------------------------------------
SENTENCES: list[tuple[str, str]] = [
    ("mandated_false_hard_en", "I don't need a wheelchair, I can walk"),
    ("mandated_false_hard_zh", "朋友说我可能需要轮椅，但我不这么认为"),
    ("clause_negation_no_exception", "轮椅必须全程无障碍，没有例外"),
    ("history_then_now", "我以前不用轮椅，但现在必须无障碍"),
    ("allergy_then_wheelchair", "我没有过敏，但我用轮椅，必须全程无障碍"),
    ("past_wheelchair_now", "过去我坐轮椅，现在必须全程无障碍"),
    ("not_metro_taxi_luggage", "不是地铁，我需要出租车因为行李很多"),
    ("no_helper_but_wheelchair", "不需要人扶，但我坐轮椅，必须全程无障碍"),
    ("control_step_free", "我必须全程无障碍"),
    ("control_wheelchair", "我需要轮椅，必须全程无障碍"),
    ("denial_control", "我不需要轮椅"),
    ("hearsay_control", "朋友说我可能需要轮椅"),
]

HARD_CODES = {"STEP_FREE_REQUIRED", "AVOID_STAIRS"}


def run_extractor(mod, text: str) -> dict:
    if mod is None:
        return {"error": "module missing"}
    fn = mod.extract_capabilities_from_text
    sig = inspect.signature(fn)
    kwargs = {}
    if "scope" in sig.parameters:
        kwargs["scope"] = "JOURNEY"
    try:
        items = fn(text, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}
    rows = []
    for item in items:
        if hasattr(item, "code"):
            rows.append(
                {
                    "code": item.code,
                    "severity": item.severity,
                    "class": item.capability_class,
                    "scope": item.scope,
                    "params": dict(item.params) if item.params else {},
                }
            )
        elif isinstance(item, dict):
            rows.append(dict(item))
        else:
            rows.append({"repr": repr(item)})
    hard = [r for r in rows if r.get("code") in HARD_CODES]
    return {
        "count": len(rows),
        "items": rows,
        "codes": sorted({str(r.get("code")) for r in rows}),
        "has_hard_accessibility": bool(hard),
        "hard_codes": sorted({str(r.get("code")) for r in hard}),
    }


def run_canonicalizer(mod, items: list[dict]) -> dict:
    if mod is None or not items:
        return {"count": 0, "codes": []}
    try:
        out = mod.canonicalize_capabilities(items)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}
    rows = []
    for item in out:
        if hasattr(item, "code"):
            rows.append({"code": item.code, "severity": item.severity,
                         "class": item.capability_class, "scope": item.scope})
        elif isinstance(item, dict):
            rows.append(dict(item))
    return {"count": len(rows), "items": rows,
            "codes": sorted({str(r.get("code")) for r in rows})}


def main() -> int:
    result: dict = {
        "eac_package": str(EAC),
        "eac_osm_loaded": EAC_OSM is not None,
        "eac_capabilities_loaded": EAC_CAPS is not None,
        "snapshot_b_capabilities_loaded": B_CAPS is not None,
        "snapshot_a_capabilities_loaded": A_CAPS is not None,
        "eac_has_split_clauses": hasattr(EAC_CAPS, "_split_clauses"),
        "b_has_split_clauses": hasattr(B_CAPS, "_split_clauses"),
        "eac_negated_markers": list(getattr(EAC_CAPS, "_NEGATED_MARKERS", ())),
        "b_negated_markers": list(getattr(B_CAPS, "_NEGATED_MARKERS", ())),
    }

    # --- A. tag matrix ---
    matrix = [evaluate(cid, tags, exp) for cid, tags, exp in TAG_CASES]
    result["tag_matrix"] = matrix
    result["tag_matrix_summary"] = {
        "total": len(matrix),
        "pass": sum(1 for r in matrix if r.get("verdict") == "PASS"),
        "fail": sum(1 for r in matrix if r.get("verdict") == "FAIL"),
        "error": sum(1 for r in matrix if "error" in r),
        "leaks": [r["case_id"] for r in matrix if r.get("leak")],
        "silently_dropped": [r["case_id"] for r in matrix
                             if r.get("silently_dropped")],
        "failing": [r["case_id"] for r in matrix if r.get("verdict") == "FAIL"],
    }

    # --- B. sentence replay ---
    sentences = []
    for sid, text in SENTENCES:
        row = {"case_id": sid, "text": text}
        for label, mod in (("eac", EAC_CAPS), ("snapshot_b", B_CAPS),
                           ("snapshot_a", A_CAPS), ("snapshot_c", C_CAPS)):
            ext = run_extractor(mod, text)
            row[label] = ext
            row[f"{label}_canonical"] = run_canonicalizer(mod, ext.get("items", []))
        row["eac_false_hard"] = bool(row["eac"].get("has_hard_accessibility"))
        row["b_false_hard"] = bool(row["snapshot_b"].get("has_hard_accessibility"))
        row["c_false_hard"] = bool(row["snapshot_c"].get("has_hard_accessibility"))
        row["eac_b_differ"] = row["eac"].get("codes") != row["snapshot_b"].get("codes")
        row["b_c_differ"] = row["snapshot_b"].get("codes") != row["snapshot_c"].get("codes")
        sentences.append(row)
    result["sentences"] = sentences
    result["mandated_false_hard"] = {
        sid: {"eac": bool(next(r for r in sentences if r["case_id"] == sid)["eac"]
                         .get("has_hard_accessibility")),
              "snapshot_b": bool(next(r for r in sentences if r["case_id"] == sid)
                                 ["snapshot_b"].get("has_hard_accessibility")),
              "snapshot_c": bool(next(r for r in sentences if r["case_id"] == sid)
                                 ["snapshot_c"].get("has_hard_accessibility"))}
        for sid in ("mandated_false_hard_en", "mandated_false_hard_zh")
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote {OUT}")
    print(json.dumps(result["tag_matrix_summary"], ensure_ascii=False, indent=2))
    print("--- mandated false-HARD ---")
    print(json.dumps(result["mandated_false_hard"], ensure_ascii=False, indent=2))
    for r in matrix:
        if r.get("verdict") == "FAIL" or r.get("leak") or r.get("silently_dropped"):
            print(
                f"  [{r.get('verdict')}] {r['case_id']} overall={r.get('overall_state')} "
                f"subjects={r.get('subjects')} codes={r.get('codes')} "
                f"leak={r.get('leak')} dropped={r.get('silently_dropped')}"
            )
    print("--- sentence deltas (EAC vs snapshot_b) ---")
    for r in sentences:
        if r["eac_b_differ"]:
            print(f"  {r['case_id']}: EAC={r['eac'].get('codes')} "
                  f"B={r['snapshot_b'].get('codes')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
