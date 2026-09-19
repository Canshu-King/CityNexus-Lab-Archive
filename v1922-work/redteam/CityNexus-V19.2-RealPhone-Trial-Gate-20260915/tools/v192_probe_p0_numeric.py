"""P0 evidence probe: numeric unit confusion and speculative over-filtering.

Two defect families surfaced by the corpus delta and need exact, reproducible
evidence before they can be written into a gate table:

  N1  unit confusion - a minutes value becomes a metres cap (and vice versa)
  N4  speculative over-filtering - a clause containing "如果"/"if"/"maybe" is
      dropped wholesale, which can silently discard a real accessibility need

Usage:
    python tools/v192_probe_p0_numeric.py [label]
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

LAB = Path(os.environ.get("V192_LAB", Path(__file__).resolve().parent.parent))
LABEL = (sys.argv[1] if len(sys.argv) > 1 else "a").lower()
BACKEND = LAB / f"snapshot_{LABEL}" / "backend"
EVID = Path(os.environ.get("V192_EVID", LAB / "evidence"))
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
print(f"lab={LAB}\nbackend={BACKEND}\nevidence={EVID}")

sys.path.insert(0, str(BACKEND))
caps = importlib.import_module("app.capabilities")
sys.path.remove(str(BACKEND))


def items(text: str):
    return list(caps.extract_capabilities_from_text(text))


print("=" * 78)
print("N1  numeric unit confusion")
print("=" * 78)
print("A minutes value must not become a metres cap, and vice versa.\n")

UNIT_CASES = [
    # (sentence, forbidden outcome description)
    ("连续走不能超过 20 分钟", "MAX_WALKING_PER_LEG_M must not appear"),
    ("连续走不能超过 45 分钟", "MAX_WALKING_PER_LEG_M must not appear"),
    ("每段走 500 米", "no minutes cap from a metres value"),
    ("每隔 60 分钟休息一次", "MAX_WALKING_PER_LEG_M must not appear"),
    ("每隔 90 分钟上厕所", "MAX_WALKING_PER_LEG_M must not appear"),
    ("我每天走路不能超过 3000 米", "MAX_WALKING_PER_LEG_M must not duplicate the daily cap"),
    ("走路不能超过 500 米", "MAX_CONTINUOUS_WALKING_MIN must not appear"),
]

n1_rows = []
for text, rule in UNIT_CASES:
    got = items(text)
    flat = [
        {"code": i["code"], "severity": i["severity"], "params": i["params"]} for i in got
    ]
    codes = [i["code"] for i in got]
    if "MAX_WALKING_PER_LEG_M must not appear" in rule:
        bad = "MAX_WALKING_PER_LEG_M" in codes
    elif "MAX_WALKING_PER_LEG_M must not duplicate" in rule:
        bad = "MAX_WALKING_PER_LEG_M" in codes and "MAX_DAILY_WALKING_M" in codes
    elif "MAX_CONTINUOUS_WALKING_MIN must not appear" in rule:
        bad = "MAX_CONTINUOUS_WALKING_MIN" in codes
    else:
        bad = False
    n1_rows.append({"text": text, "rule": rule, "items": flat, "violation": bad})
    flag = "VIOLATION" if bad else "ok"
    print(f"[{flag:9}] {text}")
    print(f"            rule: {rule}")
    for f in flat:
        print(f"            -> {f['code']:<28} {f['severity']:<7} {f['params']}")
    if not flat:
        print("            -> (no capability produced)")
    print()

print("=" * 78)
print("N4  speculative / third-party over-filtering")
print("=" * 78)
print("A stated need inside a clause containing '如果'/'if'/'maybe' must survive,")
print("and a companion's journey need must survive.\n")

FILTER_CASES = [
    ("如果可能的话我需要无障碍通道", "real need inside an 'if' clause"),
    ("if possible I need step-free access", "real need inside an 'if' clause"),
    ("我可能需要轮椅", "hedged but first-person need"),
    ("maybe I need a wheelchair", "hedged but first-person need"),
    ("我妈妈要午休", "companion journey need"),
    ("我父亲走不了远路", "companion journey need"),
    ("如果能推婴儿车就方便多了", "soft preference inside an 'if' clause"),
    ("我朋友需要轮椅，不是我", "genuine third-party denial - must stay empty"),
]

n4_rows = []
for text, why in FILTER_CASES:
    got = items(text)
    flat = [{"code": i["code"], "severity": i["severity"], "scope": i["scope"]} for i in got]
    n4_rows.append({"text": text, "why": why, "items": flat})
    print(f"{text}")
    print(f"   ({why})")
    for f in flat:
        print(f"   -> {f['code']:<28} {f['severity']:<7} {f['scope']}")
    if not flat:
        print("   -> (no capability produced)")
    print()

print("=" * 78)
print("N2/N3  decimal corruption and the 0 m policy")
print("=" * 78)
DECIMAL_CASES = [
    ("走路不能超过 1.5 公里", 1500),
    ("走路不能超过 2.5 公里", 2500),
    ("走路不能超过 0.5 公里", 500),
    ("走路不能超过 1.5 米", 2),
    ("走路不能超过 0.5 米", 1),
    ("走路不能超过 0 米", None),
]
dec_rows = []
for text, expect in DECIMAL_CASES:
    got = {i["code"]: i for i in items(text)}
    params = got.get("MAX_WALKING_PER_LEG_M", {}).get("params", {})
    actual = params.get("max_m", "MISSING")
    silent = params.get("needs_clarification") is False
    if expect is None:
        ok = actual != 0 or not silent
    else:
        ok = actual == expect
    dec_rows.append(
        {
            "text": text,
            "expected_max_m": expect,
            "actual_max_m": actual,
            "needs_clarification": params.get("needs_clarification"),
            "ok": ok,
        }
    )
    print(f"[{'ok' if ok else 'DEFECT':9}] {text:<26} expected={expect!s:<6} actual={actual!s:<6} "
          f"needs_clarification={params.get('needs_clarification')}")
print()
print("Note: '.' is a member of the clause-split character class, so '1.5' is")
print("split into '1' and '5' before the numeric parser ever sees it.")

EVID.mkdir(parents=True, exist_ok=True)
out = EVID / f"p0_numeric_{LABEL}.json"
out.write_text(
    json.dumps(
        {
            "label": LABEL,
            "capabilities": str(BACKEND / "app" / "capabilities.py"),
            "n1_unit_confusion": n1_rows,
            "n4_filtering": n4_rows,
            "n2_n3_decimal": dec_rows,
            "summary": {
                "n1_violations": sum(1 for r in n1_rows if r["violation"]),
                "n1_total": len(n1_rows),
                "n2_n3_defects": sum(1 for r in dec_rows if not r["ok"]),
                "n2_n3_total": len(dec_rows),
                "n4_empty": sum(1 for r in n4_rows if not r["items"]),
                "n4_total": len(n4_rows),
            },
        },
        ensure_ascii=False,
        indent=1,
    ),
    encoding="utf-8",
)
print(f"\nwritten: {out}")
