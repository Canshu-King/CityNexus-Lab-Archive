"""V19.1 delta: Codex V19.1 provider-evidence scope, measured on Snapshot C.

The EAC-aware brief demands the implementation satisfy:

    toilets:wheelchair=yes        MUST NOT satisfy STEP_FREE_REQUIRED
    ramp=yes / elevator=yes       MUST NOT prove step-free
    wheelchair=yes + step_count=5 MUST be CONFLICT
    list/tuple tag forms          MUST NOT be silently dropped
    route-level step-free         MUST stay unknown without route evidence
    generic overall_state         MUST NOT propagate across subject/code

Snapshot C (Codex V19.1) replaced the generic `accessibility_state(metadata)`
call with a per-requirement `evaluate_accessibility_requirement(code, facts)`.
This probe drives that function directly, plus the real `_accessibility_metadata`
projection, and reports which of the six demands hold.

Read-only.  Loads snapshot C's modules by file path; never touches the main tree.

Output: evidence/codex_v19_1_evidence.json
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
LAB = HERE.parents[1]
SNAP_C = LAB / "snapshot_c" / "backend"
OUT = LAB / "evidence" / "codex_v19_1_evidence.json"

HARD_CODES = ("STEP_FREE_REQUIRED", "AVOID_STAIRS")


def load(path: Path, name: str):
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def load_package_module(dotted: str):
    """Import a real package module from Snapshot C (feasibility.py does
    `from app.capabilities import ...`, so a bare file load cannot work)."""
    try:
        sys.path.insert(0, str(SNAP_C))
        import importlib as _il

        return _il.import_module(dotted)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! could not import {dotted}: {type(exc).__name__}: {exc}")
        return None
    finally:
        try:
            sys.path.remove(str(SNAP_C))
        except ValueError:
            pass


C_CAPS = load_package_module("app.capabilities")

# Same matrix the EAC probe uses, so the two columns are directly comparable.
TAG_CASES: list[tuple[str, object, str]] = [
    ("toilet_only", {"toilets:wheelchair": "yes"}, "not_step_free"),
    ("toilet_no", {"toilets:wheelchair": "no"}, "not_step_free_or_conflict"),
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
    ("wheelchair_yes_stairs_yes", {"wheelchair": "yes", "stairs": "yes"},
     "conflict"),
    ("wheelchair_yes_only", {"wheelchair": "yes"}, "not_step_free_or_verified"),
    ("wheelchair_designated_only", {"wheelchair": "designated"},
     "not_step_free_or_verified"),
    ("wheelchair_no_only", {"wheelchair": "no"}, "not_step_free"),
    ("wheelchair_limited", {"wheelchair": "limited"}, "not_step_free"),
    ("entrance_wheelchair_only", {"entrance:wheelchair": "yes"},
     "not_step_free_or_verified"),
    ("kerb_only", {"kerb": "lowered"}, "not_step_free"),
    ("tactile_only", {"tactile_paving": "yes"}, "not_step_free"),
    ("empty_tags", {}, "unknown"),
    ("toilet_plus_ramp", {"toilets:wheelchair": "yes", "ramp": "yes"},
     "not_step_free"),
    ("toilet_plus_wheelchair_no",
     {"toilets:wheelchair": "yes", "wheelchair": "no"}, "not_step_free"),
    # ---- explicit step-free assertions (these SHOULD verify) ----
    ("step_free_yes", {"step_free": "yes"}, "step_free_ok"),
    ("step_free_verified_yes", {"step_free_verified": "yes"}, "step_free_ok"),
    # ---- list / tuple forms must not be silently dropped ----
    ("list_value_wheelchair", {"wheelchair": ["yes"]}, "no_silent_drop"),
    ("tuple_value_ramp", {"ramp": ("yes",)}, "no_silent_drop"),
    ("list_value_step_count", {"step_count": [5]}, "no_silent_drop"),
    ("list_value_toilets", {"toilets:wheelchair": ["yes"]}, "no_silent_drop"),
    ("sequence_of_kv_strings", ["wheelchair=yes", "ramp=yes"], "no_silent_drop"),
    ("tags_nested_under_key", {"tags": {"wheelchair": "yes"}}, "no_silent_drop"),
    ("tags_nested_kv_sequence", {"tags": ["wheelchair=yes"]}, "no_silent_drop"),
    ("osm_tags_nested", {"osm_tags": {"wheelchair": "yes"}}, "no_silent_drop"),
]

# Route-level: no real route evidence must stay unknown, not verified.
ROUTE_CASES: list[tuple[str, object]] = [
    ("route_no_evidence", {"subject": "ROUTE"}),
    ("route_step_free_yes", {"subject": "ROUTE", "route_step_free": "yes"}),
    ("route_with_place_wheelchair_yes",
     {"subject": "ROUTE", "wheelchair": "yes"}),
    ("route_with_place_step_free_yes", {"subject": "ROUTE", "step_free": "yes"}),
]

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


def normalize(tags: object) -> dict:
    try:
        return dict(C_CAPS.normalize_osm_tags(tags))
    except Exception as exc:  # noqa: BLE001
        return {"__error__": f"{type(exc).__name__}: {exc}"}


def resolve(tags: object) -> dict:
    """Reproduce exactly what evaluate_accessibility_requirement sees:
    normalize_osm_tags(facts.get("osm_tags") or facts.get("tags") or facts)."""
    try:
        if isinstance(tags, dict):
            inner = tags.get("osm_tags") or tags.get("tags") or tags
        else:
            inner = tags
        return dict(C_CAPS.normalize_osm_tags(inner))
    except Exception as exc:  # noqa: BLE001
        return {"__error__": f"{type(exc).__name__}: {exc}"}


def states_for(tags: object, *, wrap: str | None = None) -> dict:
    """Run one tag set through the per-requirement evaluator.

    `wrap` decides how the tags reach the function:
      None          -> passed as the facts mapping itself
      "osm_tags"    -> {"osm_tags": tags}
      "tags"        -> {"tags": tags}
    """
    facts = tags if wrap is None else {wrap: tags}
    out = {}
    for code in HARD_CODES:
        try:
            out[code] = C_CAPS.evaluate_accessibility_requirement(code, facts)
        except Exception as exc:  # noqa: BLE001
            out[code] = f"ERROR:{type(exc).__name__}: {exc}"
    return out


def verdict_for(expectation: str, states: dict) -> str:
    step = states.get("STEP_FREE_REQUIRED")
    verified = step == "ACCESSIBILITY_VERIFIED"
    conflict = step == "ACCESSIBILITY_CONFLICT"
    if expectation == "step_free_ok":
        return "PASS" if verified else "FAIL"
    if expectation == "conflict":
        return "PASS" if conflict else "FAIL"
    if expectation == "unknown":
        return "PASS" if step in ("NEEDS_LIVE_EVIDENCE",
                                  "ACCESSIBILITY_UNVERIFIED") else "FAIL"
    if expectation == "not_step_free_or_conflict":
        return "PASS" if (not verified) or conflict else "FAIL"
    if expectation == "not_step_free_or_verified":
        return "PASS" if not verified else "FAIL"
    if expectation == "not_step_free":
        return "PASS" if not verified else "FAIL"
    return "INCONCLUSIVE"


def run_extractor(text: str) -> dict:
    if C_CAPS is None:
        return {"error": "module missing"}
    fn = C_CAPS.extract_capabilities_from_text
    kwargs = {"scope": "JOURNEY"} if "scope" in inspect.signature(fn).parameters else {}
    try:
        items = fn(text, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}
    rows = []
    for item in items:
        if hasattr(item, "code"):
            rows.append({"code": item.code, "severity": item.severity,
                         "scope": item.scope,
                         "params": dict(item.params) if item.params else {}})
        elif isinstance(item, dict):
            rows.append(dict(item))
    return {
        "count": len(rows),
        "items": rows,
        "codes": sorted({str(r.get("code")) for r in rows if r.get("code")}),
        "hard_codes": sorted({str(r.get("code")) for r in rows
                              if r.get("code") in HARD_CODES}),
        "has_hard_accessibility": any(r.get("code") in HARD_CODES for r in rows),
    }


def main() -> int:
    result: dict = {
        "snapshot_c_capabilities_loaded": C_CAPS is not None,
        "has_normalize_osm_tags": hasattr(C_CAPS, "normalize_osm_tags"),
        "has_evaluate_accessibility_requirement": hasattr(
            C_CAPS, "evaluate_accessibility_requirement"),
        "has_generic_accessibility_state": hasattr(C_CAPS, "accessibility_state"),
    }

    # ---- 1. tag matrix, tags passed straight in -------------------------
    direct = []
    for cid, tags, expectation in TAG_CASES:
        states = states_for(tags)
        resolved = resolve(tags)
        row = {
            "case_id": cid, "expectation": expectation,
            "tags": tags,
            "normalized": normalize(tags),
            "resolved": resolved,
            "states": states,
            "verdict": verdict_for(expectation, states),
        }
        # Silent-drop check on the RESOLVED tag view -- the same view the
        # evaluator uses.  A non-empty provider input that resolves to nothing
        # usable has been silently discarded.
        if expectation == "no_silent_drop":
            usable = any(
                str(v).lower() in {"yes", "true", "1", "no", "false", "0", "5"}
                for v in resolved.values()
            )
            row["verdict"] = "PASS" if usable else "FAIL"
            row["silently_dropped"] = not usable
        else:
            row["silently_dropped"] = bool(tags) and not resolved
        direct.append(row)
    result["tag_matrix_direct"] = direct

    # ---- 2. tag matrix, tags nested under the keys the gate reads -------
    nested = []
    for cid, tags, expectation in TAG_CASES:
        for wrap in ("osm_tags", "tags"):
            states = states_for(tags, wrap=wrap)
            nested.append({
                "case_id": f"{cid}@{wrap}", "expectation": expectation,
                "tags": tags, "wrap": wrap,
                "normalized": normalize(tags),
                "states": states,
                "verdict": verdict_for(expectation, states),
            })
    result["tag_matrix_nested"] = nested

    # ---- 3. route-level evidence ----------------------------------------
    route = []
    for cid, facts in ROUTE_CASES:
        states = states_for(facts)
        route.append({"case_id": cid, "facts": facts, "states": states,
                      "step_free_verified":
                          states.get("STEP_FREE_REQUIRED") == "ACCESSIBILITY_VERIFIED"})
    result["route_level"] = route

    # ---- 4. the real _accessibility_metadata projection -----------------
    feas = load_package_module("app.replanning.feasibility")
    projection = []
    if feas is not None and hasattr(feas, "_accessibility_metadata"):
        class _Rec:
            def __init__(self, metadata):
                self.metadata_json = json.dumps(metadata)

        for cid, tags, expectation in TAG_CASES:
            for shape, metadata in (
                ("top_level", dict(tags) if isinstance(tags, dict) else {}),
                ("osm_tags", {"osm_tags": tags}),
                ("tags", {"tags": tags}),
            ):
                if not metadata:
                    continue
                try:
                    projected = feas._accessibility_metadata(_Rec(metadata))
                    failures = feas._capability_failure_for_record(
                        "STEP_FREE_REQUIRED", _Rec(metadata), "loc")
                    state = feas.evaluate_accessibility_requirement(
                        "STEP_FREE_REQUIRED", projected or {})
                except Exception as exc:  # noqa: BLE001
                    projection.append({"case_id": f"{cid}@{shape}",
                                       "error": f"{type(exc).__name__}: {exc}"})
                    continue
                projection.append({
                    "case_id": f"{cid}@{shape}", "expectation": expectation,
                    "metadata": metadata,
                    "projected": dict(projected) if projected else None,
                    "gate_state": state,
                    "gate_failures": failures,
                    "gate_blocks": bool(failures),
                    "verdict": verdict_for(expectation, {
                        "STEP_FREE_REQUIRED": state}),
                })
    result["gate_projection"] = projection

    # ---- 5. sentence replay on Codex V19.1 ------------------------------
    sentences = []
    for sid, text in SENTENCES:
        ext = run_extractor(text)
        sentences.append({"case_id": sid, "text": text, "codex_v19_1": ext})
    result["sentences"] = sentences
    result["mandated_false_hard"] = {
        r["case_id"]: bool(r["codex_v19_1"].get("has_hard_accessibility"))
        for r in sentences
        if r["case_id"].startswith("mandated_false_hard")
    }

    # ---- summary ---------------------------------------------------------
    def tally(rows: list[dict]) -> dict:
        return {
            "total": len(rows),
            "pass": sum(1 for r in rows if r.get("verdict") == "PASS"),
            "fail": sum(1 for r in rows if r.get("verdict") == "FAIL"),
            "inconclusive": sum(1 for r in rows if r.get("verdict") == "INCONCLUSIVE"),
            "failing": [r["case_id"] for r in rows if r.get("verdict") == "FAIL"],
        }

    result["summary"] = {
        "tag_matrix_direct": tally(direct),
        "tag_matrix_nested": tally(nested),
        "gate_projection": tally(projection),
        "silently_dropped": [r["case_id"] for r in direct
                             if r.get("silently_dropped")],
        "route_level_step_free_verified": [
            r["case_id"] for r in route if r["step_free_verified"]],
        "step_count_conflict_verdict": next(
            (r["verdict"] for r in direct
             if r["case_id"] == "wheelchair_yes_step_count_5"), None),
        "step_count_state": next(
            (r["states"].get("STEP_FREE_REQUIRED") for r in direct
             if r["case_id"] == "wheelchair_yes_step_count_5"), None),
        "toilet_only_state": next(
            (r["states"].get("STEP_FREE_REQUIRED") for r in direct
             if r["case_id"] == "toilet_only"), None),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote {OUT}")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print("\n--- failing tag cases (direct) ---")
    for r in direct:
        if r["verdict"] == "FAIL":
            print(f"  {r['case_id']:32s} tags={r['tags']} -> "
                  f"{r['states'].get('STEP_FREE_REQUIRED')} "
                  f"(want {r['expectation']})")
    print("\n--- gate projection failures ---")
    for r in projection:
        if r.get("verdict") == "FAIL" or "error" in r:
            print(f"  {r['case_id']:40s} state={r.get('gate_state')} "
                  f"blocks={r.get('gate_blocks')} {r.get('error','')}")
    print("\n--- route level ---")
    for r in route:
        print(f"  {r['case_id']:36s} {r['states']}")
    print("\n--- mandated false HARD ---")
    print(json.dumps(result["mandated_false_hard"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
