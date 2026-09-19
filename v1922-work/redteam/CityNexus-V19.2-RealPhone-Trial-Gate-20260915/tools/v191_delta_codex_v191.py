"""V19.1 targeted read-only delta check: Codex V19.1 (current main tree).

The brief allows exactly one targeted delta check once Codex V19.1 lands in the
back half of the round.  It landed at 13:14-13:20 (main.py, feasibility.py,
capabilities.py) — after Snapshot B at 13:05:57 — so this probe re-measures only
the highest-value assertions against the live tree and diffs them against
Snapshot B (FINAL_V19) and the EAC reference.

Read-only: modules are loaded by file path, PYTHONDONTWRITEBYTECODE is set, and
no database is opened.

Output: evidence/codex_v19_1_delta.json
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
LAB = HERE.parents[1]
EAC = Path(r"D:\moodle\CityNexus-Tools\DSH-EAC-V19.1-AutonomousProductLab-20260915")
LIVE = Path(r"D:\moodle\CityNexus\backend")
OUT = LAB / "evidence" / "codex_v19_1_delta.json"

HARD_CODES = {"STEP_FREE_REQUIRED", "AVOID_STAIRS"}


def load(path: Path, name: str):
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


C = {
    "FINAL_V19": load(LAB / "snapshot_b" / "backend" / "app" / "capabilities.py",
                      "_d_b"),
    "CODEX_V19_1": load(LIVE / "app" / "capabilities.py", "_d_live"),
    "EAC_REFERENCE": load(EAC / "lab" / "runtime" / "backend" / "app"
                          / "capabilities.py", "_d_eac"),
}

SENTENCES = [
    ("mandated_en", "I don't need a wheelchair, I can walk"),
    ("mandated_zh", "朋友说我可能需要轮椅，但我不这么认为"),
    ("denial_en", "I don't use a wheelchair"),
    ("denial_en2", "I am not a wheelchair user"),
    ("denial_zh", "我不用轮椅"),
    ("hearsay_en", "my friend needs a wheelchair, not me"),
    ("hearsay_zh", "我妈妈坐轮椅"),
    ("hypothetical_en", "if I get tired I might need a wheelchair"),
    ("facility_en", "the station has an accessible toilet"),
    ("facility_zh", "车站有无障碍厕所"),
    ("clause_no_exception", "轮椅必须全程无障碍，没有例外"),
    ("history", "我以前不用轮椅，但现在必须无障碍"),
    ("control_hard", "我需要轮椅，必须全程无障碍"),
    ("walk_500", "走路不能超过 500 米"),
    ("walk_zero", "走路不能超过 0 米"),
    ("walk_negative", "走路不能超过 -5 米"),
    ("permanent", "我长期需要无障碍通道"),
]

TAGS = [
    ("toilet_only", {"toilets:wheelchair": "yes"}, "not_step_free"),
    ("entrance_only", {"entrance:wheelchair": "yes"}, "not_step_free"),
    ("ramp_only", {"ramp": "yes"}, "not_step_free"),
    ("elevator_only", {"elevator": "yes"}, "not_step_free"),
    ("wheelchair_yes", {"wheelchair": "yes"}, "step_free_ok"),
    ("step_free_yes", {"step_free": "yes"}, "step_free_ok"),
    ("wheelchair_plus_step_count", {"wheelchair": "yes", "step_count": 5},
     "conflict"),
    ("wheelchair_plus_ramp", {"wheelchair": "yes", "ramp": "yes"},
     "step_free_ok"),
    ("kv_list", ["wheelchair=yes", "ramp=yes"], "step_free_ok"),
    ("empty", {}, "unknown"),
]

CANON_CASES = [
    ("hard_soft_downgrade", [{"code": "STEP_FREE_REQUIRED", "severity": "SOFT"}],
     "severity"),
    ("hard_strong_downgrade", [{"code": "STEP_FREE_REQUIRED", "severity": "STRONG"}],
     "severity"),
    ("duplicate", [{"code": "STEP_FREE_REQUIRED", "severity": "HARD"},
                   {"code": "STEP_FREE_REQUIRED", "severity": "HARD"}], "count"),
    ("cross_scope", [{"code": "AVOID_STAIRS", "severity": "HARD",
                      "scope": "TRAVELER", "params": {"note": "t"}},
                     {"code": "AVOID_STAIRS", "severity": "HARD",
                      "scope": "JOURNEY", "params": {"note": "j"}}], "scopes"),
    ("limit_collision", [{"code": "MAX_WALKING_PER_LEG_M", "severity": "HARD",
                          "params": {"max_m": 400}},
                         {"code": "MAX_WALKING_PER_LEG_M", "severity": "HARD",
                          "params": {"max_m": 800}}], "max_m"),
]


def rows_of(mod, text: str) -> list[dict]:
    if mod is None:
        return []
    fn = mod.extract_capabilities_from_text
    import inspect
    kwargs = {"scope": "JOURNEY"} if "scope" in inspect.signature(fn).parameters else {}
    try:
        items = fn(text, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return [{"error": f"{type(exc).__name__}: {exc}"}]
    out = []
    for item in items:
        if hasattr(item, "code"):
            out.append({"code": item.code, "severity": item.severity,
                        "scope": item.scope, "params": dict(item.params or {})})
        elif isinstance(item, dict):
            out.append(dict(item))
    return out


def canon(mod, items):
    if mod is None or not items:
        return []
    try:
        res = mod.canonicalize_capabilities(items)
    except Exception as exc:  # noqa: BLE001
        return [{"error": f"{type(exc).__name__}: {exc}"}]
    out = []
    for item in res:
        if hasattr(item, "code"):
            out.append({"code": item.code, "severity": item.severity,
                        "scope": item.scope, "params": dict(item.params or {})})
        elif isinstance(item, dict):
            out.append(dict(item))
    return out


def main() -> int:
    result: dict = {
        "live_capabilities_bytes": (LIVE / "app" / "capabilities.py").stat().st_size,
        "eac_capabilities_bytes": (EAC / "lab" / "runtime" / "backend" / "app"
                                   / "capabilities.py").stat().st_size,
        "snapshot_b_capabilities_bytes": (LAB / "snapshot_b" / "backend" / "app"
                                          / "capabilities.py").stat().st_size,
        "live_has_normalize_osm_tags": hasattr(C["CODEX_V19_1"], "normalize_osm_tags"),
        "live_has_evaluate_accessibility_requirement": hasattr(
            C["CODEX_V19_1"], "evaluate_accessibility_requirement"),
        "live_has_split_clauses": hasattr(C["CODEX_V19_1"], "_split_clauses"),
        "negated_markers_identical_to_b": (
            list(getattr(C["CODEX_V19_1"], "_NEGATED_MARKERS", ()))
            == list(getattr(C["FINAL_V19"], "_NEGATED_MARKERS", ()))
        ),
        "hard_markers_identical_to_b": (
            list(getattr(C["CODEX_V19_1"], "_HARD_MARKERS", ()))
            == list(getattr(C["FINAL_V19"], "_HARD_MARKERS", ()))
        ),
    }

    # ---- sentences
    sent = []
    for cid, text in SENTENCES:
        row = {"case_id": cid, "text": text}
        for label, mod in C.items():
            rs = rows_of(mod, text)
            row[label] = {
                "codes": sorted({r.get("code") for r in rs if r.get("code")}),
                "hard": sorted({r.get("code") for r in rs
                                if r.get("code") in HARD_CODES}),
                "scopes": sorted({r.get("scope") for r in rs if r.get("scope")}),
                "count": len(rs),
            }
        row["live_vs_b"] = (row["CODEX_V19_1"]["codes"] != row["FINAL_V19"]["codes"])
        row["live_false_hard"] = bool(row["CODEX_V19_1"]["hard"])
        sent.append(row)
    result["sentences"] = sent

    # ---- tag evaluation via the new projection
    tag_rows = []
    live_eval = getattr(C["CODEX_V19_1"], "evaluate_accessibility_requirement", None)
    for cid, tags, expectation in TAGS:
        row = {"case_id": cid, "tags": tags, "expectation": expectation}
        if live_eval is None:
            row["error"] = "evaluate_accessibility_requirement absent"
            tag_rows.append(row)
            continue
        for subject in ("PLACE", "ROUTE"):
            try:
                state = live_eval("STEP_FREE_REQUIRED",
                                  {"tags": tags, "subject": subject})
            except Exception as exc:  # noqa: BLE001
                state = f"ERROR {type(exc).__name__}: {exc}"
            row[f"step_free_{subject.lower()}"] = state
        row["step_free_satisfied_place"] = (
            row["step_free_place"] == "ACCESSIBILITY_VERIFIED")
        want_allow = expectation in {"step_free_ok"}
        if expectation == "unknown":
            row["verdict"] = "PASS" if row["step_free_place"] in {
                "NEEDS_LIVE_EVIDENCE", "ACCESSIBILITY_UNVERIFIED"} else "FAIL"
        elif expectation == "conflict":
            row["verdict"] = "PASS" if row["step_free_place"] == \
                "ACCESSIBILITY_CONFLICT" else "FAIL"
        else:
            row["verdict"] = "PASS" if row["step_free_satisfied_place"] == \
                want_allow else "FAIL"
        tag_rows.append(row)
    result["tag_matrix"] = tag_rows
    result["tag_matrix_summary"] = {
        "pass": sum(1 for r in tag_rows if r.get("verdict") == "PASS"),
        "fail": [r["case_id"] for r in tag_rows if r.get("verdict") == "FAIL"],
    }

    # ---- canonicalization
    canon_rows = []
    for cid, items, probe in CANON_CASES:
        row = {"case_id": cid, "probe": probe}
        for label, mod in C.items():
            out = canon(mod, items)
            if probe == "severity":
                row[label] = out[0].get("severity") if out else None
            elif probe == "count":
                row[label] = len(out)
            elif probe == "scopes":
                row[label] = sorted({o.get("scope") for o in out})
            elif probe == "max_m":
                row[label] = (out[0].get("params") or {}).get("max_m") if out else None
        canon_rows.append(row)
    result["canonicalization"] = canon_rows

    # ---- does _bounded_number guard the walking term now?
    for label, mod in C.items():
        rs = rows_of(mod, "走路不能超过 -5 米")
        result.setdefault("walk_negative", {})[label] = [
            {"code": r.get("code"), "params": r.get("params")} for r in rs]

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"wrote {OUT}")
    print(json.dumps({k: v for k, v in result.items()
                      if not isinstance(v, (list, dict))},
                     ensure_ascii=False, indent=2))
    print("\n--- sentences (FINAL_V19 vs CODEX_V19_1) ---")
    for r in sent:
        flag = " *CHANGED*" if r["live_vs_b"] else ""
        print(f"  {r['case_id']:20s} B={r['FINAL_V19']['codes']!s:34s} "
              f"LIVE={r['CODEX_V19_1']['codes']!s:34s}{flag}")
    print("\n--- tag matrix (new projection) ---")
    for r in tag_rows:
        print(f"  {r.get('verdict')} {r['case_id']:24s} "
              f"place={r.get('step_free_place')} route={r.get('step_free_route')}")
    print(f"  summary: {result['tag_matrix_summary']}")
    print("\n--- canonicalization ---")
    for r in canon_rows:
        print(f"  {r['case_id']:24s} B={r['FINAL_V19']!s:16s} "
              f"LIVE={r['CODEX_V19_1']!s:20s} EAC={r['EAC_REFERENCE']!s}")
    print("\n--- walk negative ---")
    print(json.dumps(result["walk_negative"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
