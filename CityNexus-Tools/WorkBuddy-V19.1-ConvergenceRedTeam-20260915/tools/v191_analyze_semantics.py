"""V19.1: analyse the live hard-pair results.

Answers the seven delta-target questions from the recorded evidence, without
re-running anything.

Usage:  python tools/v191_analyze_semantics.py [A|B]
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915")
LABEL = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
EVID = LAB / "evidence"

_PER_SNAPSHOT = EVID / f"hardpairs_{LABEL.lower()}.jsonl"
_SOURCE = _PER_SNAPSHOT if _PER_SNAPSHOT.exists() else EVID / "hardpairs.jsonl"
ROWS = [
    json.loads(line)
    for line in _SOURCE.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

ACCESSIBILITY = {"STEP_FREE_REQUIRED", "AVOID_STAIRS"}
WALKING = {"MAX_WALKING_PER_LEG_M", "MAX_CONTINUOUS_WALKING_MIN", "MAX_DAILY_WALKING_M"}
WINDOWS = {"MIDDAY_REST_WINDOW", "INFANT_NAP_WINDOW"}
GEAR = {"STROLLER", "LARGE_LUGGAGE"}
BREAKS = {"REST_EVERY_MIN", "TOILET_BREAK_EVERY_MIN"}


def codes(row: dict, key: str) -> set[str]:
    return {c["code"] for c in (row.get(key) or []) if c.get("code")}


def hard_codes(row: dict, key: str) -> set[str]:
    return {
        c["code"]
        for c in (row.get(key) or [])
        if c.get("code") and c.get("severity") == "HARD"
    }


def by_bucket() -> dict:
    out: dict[str, list[dict]] = defaultdict(list)
    for row in ROWS:
        out[row["bucket"]].append(row)
    return dict(out)


def duplicate_codes(row: dict, key: str = "merged_capabilities") -> dict[str, int]:
    counter = Counter(c["code"] for c in (row.get(key) or []) if c.get("code"))
    return {code: n for code, n in counter.items() if n > 1}


def both_severities(row: dict, key: str = "merged_capabilities") -> list[str]:
    seen: dict[str, set[str]] = defaultdict(set)
    for item in row.get(key) or []:
        if item.get("code"):
            seen[item["code"]].add(item.get("severity"))
    return sorted(code for code, sevs in seen.items() if len(sevs) > 1)


def analysis() -> dict:
    buckets = by_bucket()
    out: dict = {"snapshot": LABEL, "totals": {"cases": len(ROWS)}}

    # ---- global shape --------------------------------------------------
    out["totals"].update(
        {
            "live_ok": sum(1 for r in ROWS if r.get("live_status") == "OK"),
            "model_emitted_capability": sum(1 for r in ROWS if r.get("model_raw_capabilities")),
            "model_capability_survived_canonicalization": sum(
                1 for r in ROWS if r.get("model_raw_capabilities") and r.get("model_canonical")
            ),
            "model_capability_dropped_by_canonicalization": sum(
                1
                for r in ROWS
                if r.get("model_raw_capabilities") and not r.get("model_canonical")
            ),
            "merged_has_capability": sum(1 for r in ROWS if r.get("merged_capabilities")),
            "merged_has_duplicate_code": sum(1 for r in ROWS if duplicate_codes(r)),
            "merged_has_code_in_two_severities": sum(1 for r in ROWS if both_severities(r)),
            "merged_has_hard": sum(1 for r in ROWS if hard_codes(r, "merged_capabilities")),
        }
    )

    # ---- model codes that the server refused to recognise --------------
    unknown: Counter = Counter()
    for row in ROWS:
        for item in row.get("model_raw_capabilities") or []:
            code = item.get("code")
            if code and not row.get("model_canonical"):
                unknown[code] += 1
    out["model_codes_rejected_by_canonicalization"] = dict(unknown.most_common())

    # ---- per bucket ----------------------------------------------------
    per_bucket: dict[str, dict] = {}
    for name, rows in sorted(buckets.items()):
        entry = {
            "cases": len(rows),
            "with_any_capability": sum(1 for r in rows if r.get("merged_capabilities")),
            "with_hard_capability": sum(1 for r in rows if hard_codes(r, "merged_capabilities")),
            "duplicate_code": sum(1 for r in rows if duplicate_codes(r)),
            "both_severities": sum(1 for r in rows if both_severities(r)),
        }
        per_bucket[name] = entry
    out["per_bucket"] = per_bucket

    # ---- D2: clause-local negation -------------------------------------
    neg = {}
    for pid, rows in _pairs(buckets.get("clause_negation", []), "clause_negation").items():
        live = next((r for r in rows if r["role"] == "live_need"), None)
        control = next((r for r in rows if r["role"] == "control"), None)
        if not live or not control:
            continue
        neg[pid] = {
            "live_need_text": live["raw_text"],
            "control_text": control["raw_text"],
            "live_need_codes": sorted(codes(live, "merged_capabilities")),
            "control_codes": sorted(codes(control, "merged_capabilities")),
            "live_need_hard": sorted(hard_codes(live, "merged_capabilities")),
            "control_hard": sorted(hard_codes(control, "merged_capabilities")),
            "need_erased_by_negation_elsewhere": bool(codes(control, "merged_capabilities"))
            and not codes(live, "merged_capabilities"),
        }
    out["clause_negation"] = neg
    out["clause_negation_summary"] = {
        "pairs": len(neg),
        "need_erased": sum(1 for v in neg.values() if v["need_erased_by_negation_elsewhere"]),
    }

    # ---- D2b: denial / hearsay / hypothetical --------------------------
    denial = {}
    for pid, rows in _pairs(buckets.get("denial_vs_need", []), "denial_vs_need").items():
        bad = next((r for r in rows if r["role"] == "must_not_create"), None)
        control = next((r for r in rows if r["role"] == "control"), None)
        if not bad:
            continue
        denial[pid] = {
            "must_not_create_text": bad["raw_text"],
            "manufactured_codes": sorted(codes(bad, "merged_capabilities")),
            "manufactured_hard": sorted(hard_codes(bad, "merged_capabilities")),
            "manufactured_hard_need": bool(hard_codes(bad, "merged_capabilities")),
            "control_codes": sorted(codes(control, "merged_capabilities")) if control else [],
        }
    out["denial_vs_need"] = denial
    out["denial_vs_need_summary"] = {
        "pairs": len(denial),
        "manufactured_a_hard_need": sum(
            1 for v in denial.values() if v["manufactured_hard_need"]
        ),
        "manufactured_any_capability": sum(
            1 for v in denial.values() if v["manufactured_codes"]
        ),
    }

    # ---- D1: hard vs soft ----------------------------------------------
    hs = {}
    for pid, rows in _pairs(buckets.get("hard_vs_soft", []), "hard_vs_soft").items():
        hard = next((r for r in rows if r["role"] == "hard"), None)
        soft = next((r for r in rows if r["role"] == "soft"), None)
        if not hard or not soft:
            continue
        hs[pid] = {
            "hard_text": hard["raw_text"],
            "soft_text": soft["raw_text"],
            "hard_codes": sorted(hard_codes(hard, "merged_capabilities")),
            "soft_codes": sorted(hard_codes(soft, "merged_capabilities")),
            "soft_became_hard": bool(hard_codes(soft, "merged_capabilities")),
            "hard_lost": not hard_codes(hard, "merged_capabilities"),
        }
    out["hard_vs_soft"] = hs
    out["hard_vs_soft_summary"] = {
        "pairs": len(hs),
        "soft_phrasing_became_hard": sum(1 for v in hs.values() if v["soft_became_hard"]),
        "hard_phrasing_lost_hardness": sum(1 for v in hs.values() if v["hard_lost"]),
    }

    # ---- D4: walking numerics ------------------------------------------
    walk = []
    for row in buckets.get("walking_numeric", []):
        params = [
            (c.get("code"), (c.get("params") or {}))
            for c in (row.get("merged_capabilities") or [])
        ]
        walk.append(
            {
                "text": row["raw_text"],
                "expected": row.get("expected"),
                "codes": sorted(codes(row, "merged_capabilities")),
                "params": params,
                "extracted_a_number": any(
                    isinstance((p or {}).get("max_m"), int)
                    or isinstance((p or {}).get("max_min"), int)
                    for _c, p in params
                ),
            }
        )
    out["walking_numeric"] = walk
    out["walking_numeric_summary"] = {
        "cases": len(walk),
        "extracted_a_number": sum(1 for w in walk if w["extracted_a_number"]),
        "no_capability_at_all": sum(1 for w in walk if not w["codes"]),
    }

    # ---- D5: rest / nap windows ----------------------------------------
    windows = []
    for row in buckets.get("rest_nap_window", []):
        params = [
            (c.get("code"), (c.get("params") or {}))
            for c in (row.get("merged_capabilities") or [])
        ]
        windows.append(
            {
                "text": row["raw_text"],
                "expected": row.get("expected"),
                "codes": sorted(codes(row, "merged_capabilities")),
                "params": params,
                "has_start_and_end": any(
                    (p or {}).get("start") and (p or {}).get("end") for _c, p in params
                ),
            }
        )
    out["rest_nap_window"] = windows
    out["rest_nap_window_summary"] = {
        "cases": len(windows),
        "has_window": sum(1 for w in windows if w["codes"]),
        "has_start_and_end": sum(1 for w in windows if w["has_start_and_end"]),
    }

    # ---- D7: scope -----------------------------------------------------
    scope = []
    for pid, rows in _pairs(buckets.get("scope_permanence", []), "scope_permanence").items():
        trav = next((r for r in rows if r["role"] == "traveler"), None)
        jour = next((r for r in rows if r["role"] == "journey"), None)
        if not trav or not jour:
            continue
        scope.append(
            {
                "pair": pid,
                "traveler_text": trav["raw_text"],
                "traveler_scopes": sorted(
                    {c.get("scope") for c in (trav.get("merged_capabilities") or [])}
                ),
                "journey_text": jour["raw_text"],
                "journey_scopes": sorted(
                    {c.get("scope") for c in (jour.get("merged_capabilities") or [])}
                ),
            }
        )
    out["scope_permanence"] = scope
    out["scope_permanence_summary"] = {
        "pairs": len(scope),
        "any_traveler_scope_emitted": sum(
            1 for s in scope if "TRAVELER" in (s["traveler_scopes"] or [])
        ),
    }

    # ---- duplicates on the live path -----------------------------------
    dupes = [
        {
            "id": r["id"],
            "text": r["raw_text"],
            "merged": r.get("merged_capabilities"),
            "duplicates": duplicate_codes(r),
            "both_severities": both_severities(r),
        }
        for r in ROWS
        if duplicate_codes(r) or both_severities(r)
    ]
    out["duplicates"] = dupes

    # ---- cases that would block planning --------------------------------
    out["gate_would_block"] = sum(1 for r in ROWS if r.get("gate_would_block"))
    return out


def _pairs(rows: list[dict], _bucket: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row.get("pair_id"):
            out[row["pair_id"]].append(row)
    return dict(out)


def main() -> int:
    result = analysis()
    out = EVID / f"semantic_analysis_{LABEL.lower()}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    t = result["totals"]
    print("=== totals ===")
    for key, value in t.items():
        print(f"  {key:<48} {value}")
    print("\n=== per bucket ===")
    for name, entry in result["per_bucket"].items():
        print(
            f"  {name:<20} cases={entry['cases']:<4} any={entry['with_any_capability']:<4} "
            f"hard={entry['with_hard_capability']:<4} dup={entry['duplicate_code']:<3} "
            f"two_sev={entry['both_severities']}"
        )
    print("\n=== delta-target summaries ===")
    for key in (
        "clause_negation_summary",
        "denial_vs_need_summary",
        "hard_vs_soft_summary",
        "walking_numeric_summary",
        "rest_nap_window_summary",
        "scope_permanence_summary",
    ):
        print(f"  {key:<28} {json.dumps(result[key], ensure_ascii=False)}")
    print(f"\n  model codes rejected by canonicalization: {json.dumps(result['model_codes_rejected_by_canonicalization'], ensure_ascii=False)}")
    print(f"  merged rows with duplicate code: {t['merged_has_duplicate_code']}")
    print(f"  merged rows with one code in two severities: {t['merged_has_code_in_two_severities']}")
    print(f"  cases whose merged capability would block planning: {result['gate_would_block']}")
    print(f"\nwritten -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
