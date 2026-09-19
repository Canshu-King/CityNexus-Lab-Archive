"""Step-by-step replication of extract_capabilities_from_text's walking branch.

`_number_before` alone returns 1500 for "走路不能超过 1.5 km", yet extract
returns max_m=1.  Reproduce the internal state to find where the value is lost.
"""

from __future__ import annotations

import importlib
import os
import re
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
LABEL = (sys.argv[1] if len(sys.argv) > 1 else "a").lower()
BACKEND = LAB / f"snapshot_{LABEL}" / "backend"
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

sys.path.insert(0, str(BACKEND))
caps = importlib.import_module("app.capabilities")
sys.path.remove(str(BACKEND))

TEXT = "走路不能超过 1.5 km"
raw_value = str(TEXT or "").strip().casefold()
clauses = [
    part.strip()
    for part in re.split(r"[,，。；;.!?！？\n]+|\bbut\b|\bhowever\b|但|但是|不过", raw_value)
    if part.strip()
]
print("raw_value :", repr(raw_value))
print("clauses   :", clauses)

active = []
for clause in clauses:
    negated = any(m in clause for m in caps._NEGATED_MARKERS) or bool(
        re.search(r"\b(?:don't|do not|doesn't|does not|not|never|no)\b", clause)
    )
    speculative = any(m in clause for m in caps._SPECULATIVE_MARKERS)
    third_party = any(m in clause for m in caps._THIRD_PARTY_MARKERS)
    first_person = any(m in clause for m in caps._FIRST_PERSON_MARKERS)
    facility_only = any(m in clause for m in caps._FACILITY_SUBJECT_MARKERS) and not first_person and any(
        t in clause for t in ("无障碍", "轮椅", "wheelchair", "accessible", "step-free", "step free")
    )
    explicit_limit = any(
        t in clause
        for t in ("不能超过", "最多走", "最多步行", "cannot walk more than", "walk no more than", "walking limit")
    )
    print(
        f"  clause={clause!r} negated={negated} spec={speculative} third={third_party} "
        f"facility={facility_only} explicit_limit={explicit_limit}"
    )
    if speculative or third_party or facility_only:
        continue
    positive_need = any(m in clause for m in ("必须", "务必", "现在", "当前", "must", "now", "required", "need to"))
    if negated and not positive_need:
        if not explicit_limit:
            continue
    active.append(clause)

value = " ".join(active)
print("value     :", repr(value))

walking_tokens = (
    "少走", "少步行", "不能走太多", "步行少", "走路少", "不能超过", "最多走", "最多步行",
    "low walking", "walk less", "avoid long walks", "avoid walking", "walking limit",
    "cannot walk more than", "walk no more than",
)
walking = any(t in value for t in walking_tokens)
print("walking   :", walking)

TERMS1 = ("每段", "每程", "每腿", "每次", "per leg", "each leg", "under", "less than")
TERMS2 = ("走", "walking", "walk")
m1 = caps._number_before(value, TERMS1)
m2 = caps._number_before(value, TERMS2)
print("number_before TERMS1 :", m1)
print("number_before TERMS2 :", m2)

# The exact regex, re-derived, to see which alternative the engine picks.
unit = r"(?:公里|千米|km|kilomet(?:er|re)s?|米|公尺|m|分钟|分鐘|min|minutes?)"
for label, terms in (("TERMS1", TERMS1), ("TERMS2", TERMS2)):
    pat = r"(?:" + "|".join(re.escape(t) for t in terms) + r").{0,18}?(-?[0-9]{1,8}(?:\.[0-9]+)?)\s*(" + unit + r")?"
    mm = re.search(pat, value, re.I)
    print(f"  {label} match={mm.group(0)!r} groups={mm.groups() if mm else None}")

print()
print("actual extract:", caps.extract_capabilities_from_text(TEXT))
