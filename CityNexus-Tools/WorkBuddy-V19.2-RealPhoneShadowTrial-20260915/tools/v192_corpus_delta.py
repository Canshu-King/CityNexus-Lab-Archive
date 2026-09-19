"""Run the frozen 120-case raw-language corpus against V19.1 (C) and V19.2 (A).

The corpus is the one frozen in the V19.1 round (``evidence/semantic_cases.jsonl``).
Running the *same* cases against both snapshots turns every difference into a
labelled verdict instead of an opinion:

    FIXED      expected now satisfied, was not before
    REGRESSED  expected satisfied before, not now
    NEW_DEFECT a case that now emits a hard requirement it must not emit
    IMPROVED   a false hard requirement disappeared
    STABLE     identical outcome

Usage:
    python tools/v192_corpus_delta.py
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
V191_LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915")
EVID = LAB / "evidence"
CORPUS = V191_LAB / "evidence" / "semantic_cases.jsonl"
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

SNAPSHOTS = {
    "C": V191_LAB / "snapshot_c" / "backend",
    "A": LAB / "snapshot_a" / "backend",
}


def load(backend: Path, tag: str):
    for key in [k for k in sys.modules if k == "app" or k.startswith("app.")]:
        del sys.modules[key]
    sys.path.insert(0, str(backend))
    try:
        mod = importlib.import_module("app.capabilities")
    finally:
        sys.path.remove(str(backend))
    loaded = Path(getattr(mod, "__file__", "")).resolve()
    if backend.resolve() not in loaded.parents:
        raise RuntimeError(f"{tag}: loaded {loaded} instead of {backend}")
    sys.modules[f"_pin_{tag}"] = mod
    return mod


MODS = {tag: load(path, tag) for tag, path in SNAPSHOTS.items()}


def outcome(mod, text: str) -> dict:
    items = list(mod.extract_capabilities_from_text(text))
    codes = sorted({i["code"] for i in items})
    hard = sorted({i["code"] for i in items if i["severity"] == "HARD"})
    return {
        "codes": codes,
        "hard": hard,
        "items": [
            {"code": i["code"], "severity": i["severity"], "scope": i["scope"], "params": i["params"]}
            for i in items
        ],
    }


def expected_spec(expect: str) -> tuple[str, str | None]:
    """Parse 'STEP_FREE_REQUIRED HARD' / 'no HARD capability' style expectations.

    Returns ("", None) for prose expectations we do not attempt to satisfy
    mechanically; those cases are still diffed C-vs-A, just not scored.
    """
    text = str(expect or "").strip()
    tokens = text.upper().split()
    if not tokens:
        return "", None
    if tokens[0] in CAPABILITY_CODES:
        severity = tokens[1] if len(tokens) > 1 and tokens[1] in {"HARD", "STRONG", "SOFT"} else None
        return tokens[0], severity
    if "NO HARD" in text.upper():
        return "", None
    return "?prose", None


CAPABILITY_CODES = {
    "STEP_FREE_REQUIRED",
    "AVOID_STAIRS",
    "WHEELCHAIR_PLACE_ACCESS",
    "ACCESSIBLE_TOILET",
    "MIDDAY_REST_WINDOW",
    "REST_EVERY_MIN",
    "INFANT_NAP_WINDOW",
    "TOILET_BREAK_EVERY_MIN",
    "MAX_WALKING_PER_LEG_M",
    "MAX_CONTINUOUS_WALKING_MIN",
    "MAX_DAILY_WALKING_M",
    "STROLLER",
    "LARGE_LUGGAGE",
    "SLOW_PACE",
    "QUIET_ENVIRONMENT",
    "INDOOR_PREFERRED",
    "SENSORY_LOW_STIMULATION",
}


def satisfies(spec, result) -> bool | None:
    code, severity = spec
    if code == "?prose":
        return None
    if not code:
        return not result["hard"]
    if code not in result["codes"]:
        return False
    if severity == "HARD":
        return code in result["hard"]
    return True


def diff_kind(res_c, res_a) -> str:
    """Classify the C -> A outcome change.  This is the primary signal: the
    `expected` column is prose for many cases, so a mechanical diff is the only
    trustworthy comparison."""
    if res_c["items"] == res_a["items"]:
        return "IDENTICAL"
    hard_c, hard_a = set(res_c["hard"]), set(res_a["hard"])
    if hard_a - hard_c and not hard_c - hard_a:
        return "A_ADDS_HARD"
    if hard_c - hard_a and not hard_a - hard_c:
        return "A_REMOVES_HARD"
    if hard_c != hard_a:
        return "A_HARD_MIXED"
    if set(res_c["codes"]) != set(res_a["codes"]):
        return "A_CODE_CHANGE"
    return "A_PARAM_CHANGE"


rows = []
for line in CORPUS.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    case = json.loads(line)
    spec = expected_spec(case.get("expected"))
    res_c = outcome(MODS["C"], case["text"])
    res_a = outcome(MODS["A"], case["text"])
    ok_c, ok_a = satisfies(spec, res_c), satisfies(spec, res_a)
    rows.append(
        {
            "id": case["id"],
            "bucket": case["bucket"],
            "text": case["text"],
            "expected": case.get("expected"),
            "spec": {"code": spec[0], "severity": spec[1]},
            "C": res_c,
            "A": res_a,
            "ok_C": ok_c,
            "ok_A": ok_a,
            "diff": diff_kind(res_c, res_a),
            "why": case.get("why"),
        }
    )

counts = Counter(r["diff"] for r in rows)
print("=== 120-case corpus, V19.1 (C) -> V19.2 (A) ===")
print(f"corpus: {CORPUS}")
print(f"total {len(rows)}")
for k in ("IDENTICAL", "A_ADDS_HARD", "A_REMOVES_HARD", "A_HARD_MIXED", "A_CODE_CHANGE", "A_PARAM_CHANGE"):
    if counts.get(k):
        print(f"  {k:<16} {counts[k]}")

changed = [r for r in rows if r["diff"] != "IDENTICAL"]
print(f"\n--- changed rows ({len(changed)}) ---")
for r in changed:
    print(f"\n[{r['diff']}] {r['id']}  ({r['bucket']})")
    print(f"  text     : {r['text']}")
    print(f"  expected : {r['expected']}   ok_C={r['ok_C']} ok_A={r['ok_A']}")
    print(f"  C  hard={r['C']['hard']} codes={r['C']['codes']}")
    print(f"  A  hard={r['A']['hard']} codes={r['A']['codes']}")
    if r["diff"] in {"A_ADDS_HARD", "A_HARD_MIXED"}:
        for item in r["A"]["items"]:
            if item["code"] in (set(r["A"]["hard"]) - set(r["C"]["hard"])):
                print(f"     A adds {item['code']} {item['severity']} {item['scope']} {item['params']}")
    if r["diff"] in {"A_PARAM_CHANGE", "A_CODE_CHANGE"}:
        print(f"     C items: {r['C']['items']}")
        print(f"     A items: {r['A']['items']}")

scored = [r for r in rows if r["ok_C"] is not None]
print("\n--- scored rows only (expected parsed to a real code / no-HARD) ---")
print(f"  scored: {len(scored)}  ok_C={sum(1 for r in scored if r['ok_C'])}  ok_A={sum(1 for r in scored if r['ok_A'])}")
print(f"  FIXED (C fail -> A pass): {sum(1 for r in scored if not r['ok_C'] and r['ok_A'])}")
print(f"  REGRESSED (C pass -> A fail): {sum(1 for r in scored if r['ok_C'] and not r['ok_A'])}")
for r in scored:
    if r["ok_C"] and not r["ok_A"]:
        print(f"    REGRESSED {r['id']}: {r['text']}")
        print(f"       C hard={r['C']['hard']}  A hard={r['A']['hard']}")

by_bucket: dict[str, Counter] = defaultdict(Counter)
for r in rows:
    by_bucket[r["bucket"]][r["diff"]] += 1
print("\n--- by bucket (changed only) ---")
for b, c in sorted(by_bucket.items()):
    parts = ", ".join(f"{k}={v}" for k, v in sorted(c.items()) if k != "IDENTICAL")
    if parts:
        print(f"  {b:<20} {parts}")

EVID.mkdir(parents=True, exist_ok=True)
out = EVID / "corpus_delta_c_to_a.json"
out.write_text(
    json.dumps(
        {
            "corpus": str(CORPUS),
            "snapshots": {k: str(v) for k, v in SNAPSHOTS.items()},
            "counts": dict(counts),
            "scored": {
                "total": len(scored),
                "ok_C": sum(1 for r in scored if r["ok_C"]),
                "ok_A": sum(1 for r in scored if r["ok_A"]),
            },
            "rows": rows,
        },
        ensure_ascii=False,
        indent=1,
    ),
    encoding="utf-8",
)
print(f"\nwritten: {out}")
