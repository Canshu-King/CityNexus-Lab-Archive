"""Cross-snapshot numeric/time boundary comparison.

Runs the same numeric probes against every snapshot available in the V19.1 lab
(FINAL_V19 = b, Codex V19.1 = c) and this lab (V19.2 = a), so a finding can be
labelled FIXED / STILL_REPRODUCIBLE / REGRESSED rather than merely "broken".

Usage:
    python tools/v192_cross_snapshot_numeric.py
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
V191_LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915")
EVID = LAB / "evidence"
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

SNAPSHOTS = [
    ("FINAL_V19 (B)", V191_LAB / "snapshot_b" / "backend"),
    ("Codex V19.1 (C)", V191_LAB / "snapshot_c" / "backend"),
    ("V19.2 (A)", LAB / "snapshot_a" / "backend"),
]


def load(backend: Path, tag: str):
    """Load ``app.capabilities`` from a specific snapshot.

    ``importlib.import_module`` caches on the dotted name, so loading three
    snapshots in one process would silently hand back the first module three
    times.  Purge the cached entries first, and keep a per-snapshot reference
    alive under a private name so the module object is not garbage collected
    between loads.
    """
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
    sys.modules[f"_pinned_{tag}"] = mod
    return mod


# (text, code, param key) -> what the extractor should produce
CASES = [
    ("走路不能超过 100 米", "MAX_WALKING_PER_LEG_M", "max_m"),
    ("走路不能超过 500 米", "MAX_WALKING_PER_LEG_M", "max_m"),
    ("走路不能超过 501 米", "MAX_WALKING_PER_LEG_M", "max_m"),
    ("走路不能超过 1 km", "MAX_WALKING_PER_LEG_M", "max_m"),
    ("走路不能超过 1 公里", "MAX_WALKING_PER_LEG_M", "max_m"),
    ("走路不能超过 1.5 km", "MAX_WALKING_PER_LEG_M", "max_m"),
    ("走路不能超过 0.5 km", "MAX_WALKING_PER_LEG_M", "max_m"),
    ("走路不能超过 0 米", "MAX_WALKING_PER_LEG_M", "max_m"),
    ("走路不能超过 2.5 米", "MAX_WALKING_PER_LEG_M", "max_m"),
    ("每段不超过 100 米", "MAX_WALKING_PER_LEG_M", "max_m"),
    ("连续走路不能超过 30 分钟", "MAX_CONTINUOUS_WALKING_MIN", "max_min"),
    ("每天走路不能超过 5000 米", "MAX_DAILY_WALKING_M", "max_m"),
    ("每隔 60 分钟休息一次", "REST_EVERY_MIN", "interval_min"),
    ("每隔 90 分钟上厕所", "TOILET_BREAK_EVERY_MIN", "interval_min"),
    ("午休 12:00 到 14:00", "MIDDAY_REST_WINDOW", "start"),
    ("午休 15:00 到 13:00", "MIDDAY_REST_WINDOW", "start"),
]

results: dict[str, dict] = {}
mods = {}
for name, backend in SNAPSHOTS:
    if not backend.exists():
        results[name] = {"__missing__": str(backend)}
        continue
    mods[name] = load(backend, name.split()[0].lower().replace(".", ""))
    print(f"loaded {name:<16} <- {mods[name].__file__}")

for name, backend in SNAPSHOTS:
    if name not in mods:
        continue
    mod = mods[name]
    row: dict[str, object] = {}
    for text, code, key in CASES:
        items = {i["code"]: i for i in mod.extract_capabilities_from_text(text)}
        params = items.get(code, {}).get("params")
        row[f"{text} :: {key}"] = params.get(key, "MISSING") if params else "MISSING"
        if code in {"MIDDAY_REST_WINDOW"}:
            row[f"{text} :: flags"] = (
                sorted(k for k in params if k in {"needs_clarification", "defaulted_window"})
                if params
                else []
            )
    results[name] = row

names = [n for n, _ in SNAPSHOTS if n in mods]
print("=== numeric / time boundary semantics across snapshots ===\n")
header = f"{'case':<46}" + "".join(f"{n:>20}" for n in names)
print(header)
print("-" * len(header))
for text, code, key in CASES:
    label = f"{text} :: {key}"
    if len(label) > 44:
        label = label[:41] + "..."
    print(f"{label:<46}" + "".join(f"{str(results[n].get(label, '-')):>20}" for n in names))
    if code == "MIDDAY_REST_WINDOW":
        fl = f"{text} :: flags"
        print(f"{'  ^ flags':<46}" + "".join(f"{str(results[n].get(fl, '-')):>20}" for n in names))

EVID.mkdir(parents=True, exist_ok=True)
out = EVID / "cross_snapshot_numeric.json"
out.write_text(json.dumps({"snapshots": names, "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\nwritten: {out}")
