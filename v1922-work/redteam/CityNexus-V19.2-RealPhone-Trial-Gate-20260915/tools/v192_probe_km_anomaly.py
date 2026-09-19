"""Isolate the `1.5 km` numeric anomaly in the live extractor."""

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

CASES = [
    "走路不能超过 1.5 km",
    "走路不能超过 1.5 公里",
    "走路不能超过 1.5km",
    "走路不能超过 1500 米",
    "走路不能超过 1.50 km",
    "走路不能超过 0.5 km",
    "走路不能超过 2 km",
]
print("text                              _number_before(走..)  extract max_m")
for text in CASES:
    nb = caps._number_before(text, ("走", "walking", "walk"))
    items = {i["code"]: i for i in caps.extract_capabilities_from_text(text)}
    got = items.get("MAX_WALKING_PER_LEG_M", {}).get("params", {})
    print(f"{text:<34} {str(nb):<20} {got}")

print()
print("--- raw regex trace for '走路不能超过 1.5 km' ---")
value = "走路不能超过 1.5 km"
unit = r"(?:公里|千米|km|kilomet(?:er|re)s?|米|公尺|m|分钟|分鐘|min|minutes?)"
pattern = r"(?:" + "|".join(re.escape(t) for t in ("走", "walking", "walk")) + r").{0,18}?(-?[0-9]{1,8}(?:\.[0-9]+)?)\s*(" + unit + r")?"
m = re.search(pattern, value, re.I)
print("pattern:", pattern)
print("match:", m.group(0) if m else None, "| groups:", m.groups() if m else None)

print()
print("--- _bounded_number behaviour ---")
for v in (1.5, 1500.0, "1.5", 1500, 0.5):
    print(f"  _bounded_number({v!r}) = {caps._bounded_number(v)!r}")
