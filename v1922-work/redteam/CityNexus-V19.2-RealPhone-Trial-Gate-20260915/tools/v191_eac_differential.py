"""V19.1 EAC differential: FINAL_V19 vs EAC_REFERENCE on raw-language hard cases.

Runs a 150-220 case corpus through both capability extractors + canonicalisers:

  FINAL_V19 / CODEX_V19_1  -> snapshot_b/backend/app/capabilities.py
                              (byte-identical in Snapshot A and B, so the same
                               file answers both labels on this surface)
  EAC_REFERENCE            -> DSH-EAC .../lab/runtime/backend/app/capabilities.py

The comparison is deterministic and offline, so it can cover the whole corpus
without model/rate-limit noise; the live DeepSeek path is already covered by
evidence/hardpairs_{a,b}.jsonl.

Reuses the 120 texts already in evidence/semantic_cases.jsonl and adds targeted
provider-evidence / denial / hearsay / cross-scope / numeric cases.

Output: evidence/eac_differential.jsonl, evidence/eac_differential_summary.json
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve()
LAB = HERE.parents[1]
EAC = Path(r"D:\moodle\CityNexus-Tools\DSH-EAC-V19.1-AutonomousProductLab-20260915")
OUT = LAB / "evidence" / "eac_differential.jsonl"
SUMMARY = LAB / "evidence" / "eac_differential_summary.json"

HARD_CODES = {"STEP_FREE_REQUIRED", "AVOID_STAIRS"}


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


EAC_CAPS = load(EAC / "lab" / "runtime" / "backend" / "app" / "capabilities.py",
                "_diff_eac_caps")
B_CAPS = load(LAB / "snapshot_b" / "backend" / "app" / "capabilities.py",
              "_diff_b_caps")

# ------------------------------------------------------------------ corpus
EXTRA: list[tuple[str, str, str, str, str]] = [
    # (bucket, role, lang, text, why)
    # -- the two mandated false-HARD sentences, as explicit corpus rows
    ("mandated", "denial_en", "en", "I don't need a wheelchair, I can walk",
     "task brief: independent review says EAC still emits a false HARD need"),
    ("mandated", "hearsay_zh", "zh", "朋友说我可能需要轮椅，但我不这么认为",
     "task brief: independent review says EAC still emits a false HARD need"),
    # -- denial family
    ("denial_vs_need", "denial_en", "en", "no wheelchair needed, I can walk fine",
     "explicit denial must not create a HARD need"),
    ("denial_vs_need", "denial_en", "en", "I don't use a wheelchair",
     "explicit denial must not create a HARD need"),
    ("denial_vs_need", "denial_en", "en", "I am not a wheelchair user",
     "explicit denial must not create a HARD need"),
    ("denial_vs_need", "denial_en", "en", "no stairs problem for me, I'm fine",
     "denial of a problem must not create a HARD need"),
    ("denial_vs_need", "denial_zh", "zh", "我不需要轮椅",
     "explicit denial must not create a HARD need"),
    ("denial_vs_need", "denial_zh", "zh", "我不用轮椅",
     "explicit denial must not create a HARD need"),
    ("denial_vs_need", "denial_zh", "zh", "我没有轮椅需求",
     "explicit denial must not create a HARD need"),
    ("denial_vs_need", "denial_zh", "zh", "楼梯对我没问题",
     "denial of a problem must not create a HARD need"),
    # -- hearsay / third party
    ("hearsay", "third_party_en", "en", "my friend needs a wheelchair, not me",
     "third-party need is not the traveller's need"),
    ("hearsay", "third_party_en", "en", "my mother uses a wheelchair",
     "third-party need is not the traveller's need"),
    ("hearsay", "third_party_en", "en", "my colleague said I might need a wheelchair",
     "hearsay must not become a HARD fact"),
    ("hearsay", "third_party_zh", "zh", "我朋友需要轮椅",
     "third-party need is not the traveller's need"),
    ("hearsay", "third_party_zh", "zh", "我妈妈坐轮椅",
     "third-party need is not the traveller's need"),
    ("hearsay", "third_party_zh", "zh", "同事说我也许需要轮椅",
     "hearsay must not become a HARD fact"),
    # -- hypothetical / conditional
    ("hypothetical", "conditional_en", "en", "if I get tired I might need a wheelchair",
     "a hypothetical is not a confirmed hard need"),
    ("hypothetical", "conditional_zh", "zh", "如果累了可能需要轮椅",
     "a hypothetical is not a confirmed hard need"),
    ("hypothetical", "conditional_en", "en", "maybe I should avoid stairs",
     "a hedged preference is not a confirmed hard need"),
    # -- provider evidence (must not manufacture capabilities)
    ("provider_evidence", "toilet_tag", "en",
     "the station has an accessible toilet",
     "a toilet tag is not a step-free route"),
    ("provider_evidence", "ramp_tag", "en", "the venue has a ramp",
     "a ramp is not a proven step-free route"),
    ("provider_evidence", "elevator_tag", "en", "there is an elevator at the museum",
     "an elevator is not a proven step-free route"),
    ("provider_evidence", "toilet_tag_zh", "zh", "车站有无障碍厕所",
     "a toilet tag is not a step-free route"),
    ("provider_evidence", "ramp_tag_zh", "zh", "这里有坡道",
     "a ramp is not a proven step-free route"),
    # -- clause-local negation / history (EAC claimed a fix here)
    ("clause_negation", "history_en", "en",
     "I used to need a wheelchair but not anymore",
     "history must not erase or create a live need"),
    ("clause_negation", "history_en", "en",
     "I did not need help before, but now I need step-free access",
     "the live clause must win over the historical clause"),
    ("clause_negation", "history_zh", "zh",
     "我以前不需要轮椅，现在也不需要",
     "a fully historical denial must not create a need"),
    ("clause_negation", "mixed_en", "en",
     "not the metro, I need a taxi because of the luggage",
     "the negation scopes to the metro, not to the luggage need"),
    ("clause_negation", "mixed_en", "en",
     "no allergies, but I use a wheelchair and need step-free access",
     "an unrelated denial must not erase the wheelchair need"),
    # -- numeric walking / rest, more surface forms
    ("walking_numeric", "limit_en", "en", "I can walk at most 400 metres at a time",
     "bounded walking limit must be parsed"),
    ("walking_numeric", "limit_en", "en", "no more than 20 minutes of walking",
     "bounded continuous walking must be parsed"),
    ("walking_numeric", "limit_en", "en", "I can only walk 300 m per leg",
     "per-leg limit must be parsed"),
    ("walking_numeric", "limit_zh", "zh", "每段最多走 300 米",
     "per-leg limit must be parsed"),
    ("walking_numeric", "limit_zh", "zh", "连续走不超过 15 分钟",
     "continuous walking limit must be parsed"),
    ("walking_numeric", "limit_zh", "zh", "每天走路不要超过 5 公里",
     "daily walking limit must be parsed"),
    ("walking_numeric", "limit_en", "en", "max 5 km walking per day",
     "daily walking limit must be parsed"),
    ("rest_nap_window", "rest_zh", "zh", "中午 12 点到 2 点要休息",
     "rest window must be parsed"),
    ("rest_nap_window", "rest_en", "en", "I need a rest between 12:00 and 14:00",
     "rest window must be parsed"),
    ("rest_nap_window", "nap_zh", "zh", "孩子下午 1 点到 3 点要午睡",
     "nap window must be parsed"),
    ("rest_nap_window", "break_zh", "zh", "每 30 分钟要上一次厕所",
     "toilet break interval must be parsed"),
    ("rest_nap_window", "break_en", "en", "a toilet break every 30 minutes",
     "toilet break interval must be parsed"),
    # -- scope: permanent vs this-trip
    ("scope_permanence", "permanent_zh", "zh", "我长期需要无障碍通道",
     "permanent language should be TRAVELER scope"),
    ("scope_permanence", "permanent_en", "en", "I permanently need step-free access",
     "permanent language should be TRAVELER scope"),
    ("scope_permanence", "permanent_zh", "zh", "我一直坐轮椅，不是这次才需要",
     "permanent language should be TRAVELER scope"),
    ("scope_permanence", "trip_en", "en", "for this trip only I need step-free access",
     "trip-scoped language should be JOURNEY scope"),
    ("scope_permanence", "trip_zh", "zh", "这次旅行我需要无障碍通道",
     "trip-scoped language should be JOURNEY scope"),
    # -- duplicates / multi
    ("duplicate_multi", "dup_en", "en", "wheelchair, must be step-free",
     "the same code must not be stored twice"),
    ("duplicate_multi", "dup_zh", "zh", "轮椅，必须全程无障碍",
     "the same code must not be stored twice"),
    ("duplicate_multi", "multi_en", "en",
     "step-free access, no stairs, and a rest every 30 minutes",
     "multiple codes must all survive"),
    ("duplicate_multi", "multi_zh", "zh", "需要无障碍、不要楼梯、每 30 分钟休息",
     "multiple codes must all survive"),
    # -- stroller / luggage
    ("stroller_luggage", "stroller_en", "en", "travelling with a stroller",
     "stroller context must be captured"),
    ("stroller_luggage", "stroller_zh", "zh", "带着婴儿车",
     "stroller context must be captured"),
    ("stroller_luggage", "luggage_en", "en", "I have very large luggage",
     "large luggage context must be captured"),
    ("stroller_luggage", "luggage_zh", "zh", "行李很多很大",
     "large luggage context must be captured"),
    # -- soft preferences
    ("hard_vs_soft", "soft_en", "en", "I'd prefer a quiet environment",
     "a soft preference must not become HARD"),
    ("hard_vs_soft", "soft_zh", "zh", "我更喜欢安静的地方",
     "a soft preference must not become HARD"),
    ("hard_vs_soft", "soft_en", "en", "slow pace would be nice",
     "a soft preference must not become HARD"),
    ("hard_vs_soft", "hard_en", "en", "I must have step-free access, no exceptions",
     "an explicit hard need must stay HARD"),
    ("hard_vs_soft", "hard_zh", "zh", "必须全程无障碍，没有例外",
     "an explicit hard need must stay HARD"),
    # -- mixed language
    ("mixed_language", "mixed", "mixed", "must be step-free 必须无障碍",
     "mixed-language hard need must be captured"),
    ("mixed_language", "mixed", "mixed", "no stairs 不要楼梯，please",
     "mixed-language stair avoidance must be captured"),
    ("mixed_language", "mixed", "mixed", "轮椅 wheelchair needed",
     "mixed-language wheelchair need must be captured"),
]


def load_corpus() -> list[dict]:
    rows = [json.loads(line) for line in
            (LAB / "evidence" / "semantic_cases.jsonl").read_text(
                encoding="utf-8").splitlines() if line.strip()]
    for i, (bucket, role, lang, text, why) in enumerate(EXTRA, start=1):
        rows.append({
            "id": f"{bucket}-extra{i:04d}",
            "bucket": bucket,
            "role": role,
            "pair_id": f"{bucket}:extra{ i }",
            "topic": role,
            "lang": lang,
            "persona": None,
            "text": text,
            "expected": "",
            "why": why,
            "source": "v191_eac_update",
        })
    return rows


# ------------------------------------------------------------------ runners
def run(mod, text: str) -> dict:
    fn = mod.extract_capabilities_from_text
    params = inspect.signature(fn).parameters
    kwargs = {}
    if "scope" in params:
        kwargs["scope"] = "JOURNEY"
    try:
        items = fn(text, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}", "codes": [],
                "hard_codes": [], "count": 0}
    rows = []
    for item in items:
        if hasattr(item, "code"):
            rows.append({"code": item.code, "severity": item.severity,
                         "class": item.capability_class, "scope": item.scope,
                         "params": dict(item.params or {})})
        elif isinstance(item, dict):
            rows.append(dict(item))
    try:
        canon = mod.canonicalize_capabilities(rows)
        canon_rows = []
        for item in canon:
            if hasattr(item, "code"):
                canon_rows.append({"code": item.code, "severity": item.severity,
                                   "scope": item.scope,
                                   "params": dict(item.params or {})})
            elif isinstance(item, dict):
                canon_rows.append(dict(item))
    except Exception as exc:  # noqa: BLE001
        canon_rows = [{"error": f"{type(exc).__name__}: {exc}"}]
    return {
        "count": len(rows),
        "items": rows,
        "codes": sorted({str(r.get("code")) for r in rows if r.get("code")}),
        "hard_codes": sorted({str(r.get("code")) for r in rows
                              if r.get("code") in HARD_CODES}),
        "canon_count": len(canon_rows),
        "canon_codes": sorted({str(r.get("code")) for r in canon_rows
                               if r.get("code")}),
        "canon_scopes": sorted({str(r.get("scope")) for r in canon_rows
                                if r.get("scope")}),
        "duplicate_codes": sorted(
            {c for c, n in Counter(r.get("code") for r in rows).items()
             if n > 1 and c}),
        "canon_duplicate_codes": sorted(
            {c for c, n in Counter(r.get("code") for r in canon_rows).items()
             if n > 1 and c}),
    }


def main() -> int:
    corpus = load_corpus()
    rows = []
    for case in corpus:
        eac = run(EAC_CAPS, case["text"])
        b = run(B_CAPS, case["text"])
        divergent = (eac["codes"] != b["codes"]
                     or eac.get("canon_scopes") != b.get("canon_scopes")
                     or eac.get("duplicate_codes") != b.get("duplicate_codes"))
        row = {
            "id": case["id"],
            "bucket": case["bucket"],
            "role": case.get("role"),
            "lang": case.get("lang"),
            "text": case["text"],
            "why": case.get("why"),
            "eac": {k: eac.get(k) for k in
                    ("codes", "hard_codes", "count", "canon_codes",
                     "canon_scopes", "duplicate_codes", "canon_duplicate_codes")},
            "b": {k: b.get(k) for k in
                  ("codes", "hard_codes", "count", "canon_codes",
                   "canon_scopes", "duplicate_codes", "canon_duplicate_codes")},
            "divergent": divergent,
            "eac_only_codes": sorted(set(eac["codes"]) - set(b["codes"])),
            "b_only_codes": sorted(set(b["codes"]) - set(eac["codes"])),
            "tags": sorted(
                (["FINAL_V19"] if b["codes"] else [])
                + (["EAC_REFERENCE"] if eac["codes"] else [])
                + (["CODEX_V19_1_IF_AVAILABLE"] if b["codes"] else [])
            ),
        }
        rows.append(row)

    with OUT.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    by_bucket: dict = defaultdict(lambda: {
        "cases": 0, "divergent": 0, "eac_only": 0, "b_only": 0,
        "eac_hard": 0, "b_hard": 0, "eac_dup": 0, "b_dup": 0,
        "eac_traveler_scope": 0, "b_traveler_scope": 0})
    for row in rows:
        s = by_bucket[row["bucket"]]
        s["cases"] += 1
        s["divergent"] += int(row["divergent"])
        s["eac_only"] += int(bool(row["eac_only_codes"]))
        s["b_only"] += int(bool(row["b_only_codes"]))
        s["eac_hard"] += int(bool(row["eac"]["hard_codes"]))
        s["b_hard"] += int(bool(row["b"]["hard_codes"]))
        s["eac_dup"] += int(bool(row["eac"]["duplicate_codes"]))
        s["b_dup"] += int(bool(row["b"]["duplicate_codes"]))
        s["eac_traveler_scope"] += int("TRAVELER" in (row["eac"]["canon_scopes"] or []))
        s["b_traveler_scope"] += int("TRAVELER" in (row["b"]["canon_scopes"] or []))

    summary = {
        "corpus_size": len(rows),
        "unique_texts": len({r["text"] for r in rows}),
        "divergent": sum(1 for r in rows if r["divergent"]),
        "eac_only": sum(1 for r in rows if r["eac_only_codes"]),
        "b_only": sum(1 for r in rows if r["b_only_codes"]),
        "both_empty": sum(1 for r in rows if not r["eac"]["codes"]
                          and not r["b"]["codes"]),
        "eac_hard": sum(1 for r in rows if r["eac"]["hard_codes"]),
        "b_hard": sum(1 for r in rows if r["b"]["hard_codes"]),
        "eac_duplicates": sum(1 for r in rows if r["eac"]["duplicate_codes"]),
        "b_duplicates": sum(1 for r in rows if r["b"]["duplicate_codes"]),
        "eac_canonical_duplicates": sum(
            1 for r in rows if r["eac"]["canon_duplicate_codes"]),
        "b_canonical_duplicates": sum(
            1 for r in rows if r["b"]["canon_duplicate_codes"]),
        "eac_traveler_scope_rows": sum(
            1 for r in rows if "TRAVELER" in (r["eac"]["canon_scopes"] or [])),
        "b_traveler_scope_rows": sum(
            1 for r in rows if "TRAVELER" in (r["b"]["canon_scopes"] or [])),
        "by_bucket": dict(sorted(by_bucket.items())),
        "mandated": [r for r in rows if r["bucket"] == "mandated"],
        "eac_only_examples": [
            {"id": r["id"], "text": r["text"], "eac": r["eac"]["codes"],
             "b": r["b"]["codes"]} for r in rows if r["eac_only_codes"]][:25],
        "b_only_examples": [
            {"id": r["id"], "text": r["text"], "eac": r["eac"]["codes"],
             "b": r["b"]["codes"]} for r in rows if r["b_only_codes"]][:25],
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                       encoding="utf-8")

    print(f"wrote {OUT}")
    print(f"wrote {SUMMARY}")
    print(json.dumps({k: v for k, v in summary.items()
                      if not isinstance(v, (dict, list))},
                     ensure_ascii=False, indent=2))
    print("\n--- by bucket ---")
    for bucket, s in sorted(by_bucket.items()):
        print(f"  {bucket:20s} n={s['cases']:3d} div={s['divergent']:3d} "
              f"eac_only={s['eac_only']:3d} b_only={s['b_only']:3d} "
              f"eac_hard={s['eac_hard']:3d} b_hard={s['b_hard']:3d} "
              f"eac_dup={s['eac_dup']:3d} b_dup={s['b_dup']:3d} "
              f"eac_TV={s['eac_traveler_scope']:3d} b_TV={s['b_traveler_scope']:3d}")
    print("\n--- mandated ---")
    for r in summary["mandated"]:
        print(f"  {r['text']!r} EAC={r['eac']['codes']} B={r['b']['codes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
