"""V19.1: classify the focused contract assertions across three snapshots.

Snapshot A = FINAL_V19 at task start (12:38)
Snapshot B = FINAL_V19 mid-task   (13:06)
Snapshot C = Codex V19.1          (13:47)

Two comparisons are produced:

  A -> B   the moving-baseline drift  (tag FINAL_V19)
  B -> C   the Codex V19.1 delta      (tag CODEX_V19_1_IF_AVAILABLE)

Usage:  python tools/v191_classify_postfix.py
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915")
EVID = LAB / "evidence"

LABELS = ("a", "b", "c")
TAG = {"a": "FINAL_V19", "b": "FINAL_V19", "c": "CODEX_V19_1_IF_AVAILABLE"}

# A raw B->C verdict of REGRESSED is not automatically a defect: several of these
# assertions are *source-text greps* that pin an implementation detail rather than
# a behaviour.  Each override below was verified by hand against the three
# snapshots; see CODEX_V19_1_DELTA_RESULTS.md.
OVERRIDE = {
    "test_v19_char_d6c_gate_consults_accessibility_evidence": {
        "bc_verdict": "STALE_TEST",
        "why": ("the assertion greps feasibility.py for the literal 'accessibility_state('; "
                "Codex V19.1 replaced that generic call with the scoped "
                "'evaluate_accessibility_requirement(code, metadata)' at line 286, which is a "
                "stronger form of the same behaviour, so the pinned spelling no longer matches "
                "while the behaviour it guards is still present and improved."),
    },
}

# Which delta target each assertion belongs to, and whether it is a guard
# (must pass) or a defect probe (fails while the defect is live).
TARGET = {
    "d1": "D1 hard-downgrade guard",
    "d2": "D2 clause-local negation / history",
    "d3": "D3 duplicate capability codes",
    "d4": "D4 walking / rest numerics",
    "d5": "D5 rest and nap windows",
    "d6": "D6 gate interprets capability",
    "d7": "D7 TRAVELER scope reachable",
}


def read_status(label: str) -> dict[str, str]:
    path = EVID / f"_junit_{label}.xml"
    if not path.exists():
        return {}
    root = ET.parse(path).getroot()
    suite = root if root.tag == "testsuite" else root[0]
    out: dict[str, str] = {}
    for case in suite.findall("testcase"):
        name = case.get("name") or ""
        out[name] = (
            "FAILED"
            if case.find("failure") is not None
            else "ERROR"
            if case.find("error") is not None
            else "SKIPPED"
            if case.find("skipped") is not None
            else "PASSED"
        )
    return out


def verdict_for(older: str | None, newer: str | None, is_defect: bool) -> str:
    if older is None or newer is None:
        return "INCONCLUSIVE"
    if older == "SKIPPED" and newer == "SKIPPED":
        return "NOT_COVERED"
    if older == "SKIPPED" and newer == "PASSED":
        return "NEW_COVERAGE_HOLDS"
    if older == "SKIPPED" and newer == "FAILED":
        return "NEW_COVERAGE_DEFECT"
    if older == "PASSED" and newer == "PASSED":
        return "FIXED_IN_CURRENT" if is_defect else "GUARD_HOLDS"
    if older == "FAILED" and newer == "FAILED":
        return "STILL_REPRODUCIBLE"
    if older == "PASSED" and newer == "FAILED":
        return "REGRESSED"
    if older == "FAILED" and newer == "PASSED":
        return "FIXED_IN_CURRENT"
    return "INCONCLUSIVE"


def classify() -> dict:
    status = {label: read_status(label) for label in LABELS}
    names = sorted(set().union(*(set(status[l]) for l in LABELS if status[l])))

    rows: list[dict] = []
    for name in names:
        lower = name.lower()
        target = "EAC / provider-evidence scope"
        for key, label in TARGET.items():
            if f"_{key}" in lower:
                target = label
                break
        if "eac_guard" in lower or "eac_defect" in lower:
            target = "EAC / provider-evidence scope"
        elif "guard" in lower:
            target = "guard (must not regress)"
        is_defect = "defect" in lower or "char_d" in lower

        sa, sb, sc = (status[l].get(name) for l in LABELS)
        row = {
            "name": name,
            "target": target,
            "kind": "defect_probe" if is_defect else "guard",
            "snapshot_a": sa,
            "snapshot_b": sb,
            "snapshot_c": sc,
            "ab_verdict": verdict_for(sa, sb, is_defect),
            "bc_verdict": verdict_for(sb, sc, is_defect),
            "tag": "CODEX_V19_1_IF_AVAILABLE" if sc is not None else "FINAL_V19",
        }
        if name in OVERRIDE:
            row.update(OVERRIDE[name])
        rows.append(row)

    def tally(key: str) -> dict:
        out: dict[str, dict[str, int]] = {}
        for row in rows:
            out.setdefault(row["target"], {})
            out[row["target"]][row[key]] = out[row["target"]].get(row[key], 0) + 1
        return out

    return {
        "totals": {l: {
            "passed": sum(1 for v in status[l].values() if v == "PASSED"),
            "failed": sum(1 for v in status[l].values() if v == "FAILED"),
            "skipped": sum(1 for v in status[l].values() if v == "SKIPPED"),
            "cases": len(status[l]),
        } for l in LABELS},
        "by_target_ab": tally("ab_verdict"),
        "by_target_bc": tally("bc_verdict"),
        "rows": rows,
    }


def main() -> int:
    result = classify()
    rows = result["rows"]
    (EVID / "postfix_classification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print("=== totals ===")
    for label, t in result["totals"].items():
        print(f"  {label}: {t['passed']} passed / {t['failed']} failed / "
              f"{t['skipped']} skipped  (n={t['cases']})")

    print("\n=== A -> B (FINAL_V19 drift) ===")
    for target, counts in sorted(result["by_target_ab"].items()):
        print(f"  {target:<40} {counts}")

    print("\n=== B -> C (Codex V19.1) ===")
    for target, counts in sorted(result["by_target_bc"].items()):
        print(f"  {target:<40} {counts}")

    print("\n=== defect probes FIXED by Codex V19.1 ===")
    for row in rows:
        if row["kind"] == "defect_probe" and row["bc_verdict"] == "FIXED_IN_CURRENT":
            print(f"  {row['name']}")

    print("\n=== guards that do NOT hold on C ===")
    broken = [r for r in rows if r["kind"] == "guard" and r["snapshot_c"] not in (None, "PASSED")]
    for row in broken:
        print(f"  {row['snapshot_c']:<8} {row['name']}")
    print(f"  total: {len(broken)}")

    regressions = [r for r in rows if r["bc_verdict"] == "REGRESSED"]
    print(f"\n=== REGRESSED by Codex V19.1: {len(regressions)} ===")
    for row in regressions:
        print(f"  {row['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
