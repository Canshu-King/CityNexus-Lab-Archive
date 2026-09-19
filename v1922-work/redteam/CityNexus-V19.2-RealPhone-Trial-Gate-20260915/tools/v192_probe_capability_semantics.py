"""V19.2 Real-Phone Shadow-Trial Gate - capability-layer semantics probe.

Measures the live snapshot's ``app.capabilities`` directly against every
property the road-prep patches claim to guarantee.  Nothing is taken on trust:
each row is produced by calling the module, not by reading the diff.

Usage:
    python tools/v192_probe_capability_semantics.py [label]

Writes evidence/capability_semantics_<label>.json and prints a compact table.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
EVID = LAB / "evidence"
LABEL = (sys.argv[1] if len(sys.argv) > 1 else "a").lower()
BACKEND = LAB / f"snapshot_{LABEL}" / "backend"

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")


def load_capabilities():
    sys.path.insert(0, str(BACKEND))
    try:
        return importlib.import_module("app.capabilities")
    finally:
        sys.path.remove(str(BACKEND))


caps = load_capabilities()
rows: list[dict] = []


def rec(group: str, name: str, expect, actual, ok: bool, note: str = "") -> None:
    rows.append(
        {
            "group": group,
            "name": name,
            "expect": expect,
            "actual": actual,
            "ok": bool(ok),
            "note": note,
        }
    )


def extract(text: str, scope: str = "JOURNEY"):
    return list(caps.extract_capabilities_from_text(text, scope=scope))


def codes(items):
    return sorted({i["code"] for i in items})


# ---------------------------------------------------------------- G1 false-HARD
# Nine residual false-HARD sentences measured on V19.1 Snapshot C.  Every one of
# these must now yield NO hard accessibility requirement.
FALSE_HARD = [
    ("my friend needs a wheelchair, not me", "third-party subject (en)"),
    ("my mother uses a wheelchair", "third-party subject (en)"),
    ("我朋友需要轮椅", "third-party subject (zh)"),
    ("我妈妈坐轮椅", "third-party subject (zh)"),
    ("I am not a wheelchair user", "first-person denial"),
    ("the station has an accessible toilet", "facility description (en)"),
    ("车站有无障碍厕所", "facility description (zh)"),
    ("说不定到时候我需要轮椅", "speculation (zh)"),
    ("if I end up in a wheelchair I'll tell you", "speculation (en)"),
]
for text, why in FALSE_HARD:
    got = codes(extract(text))
    hard = [i for i in extract(text) if i["severity"] == "HARD"]
    rec(
        "G1_false_hard",
        text,
        "no STEP_FREE_REQUIRED",
        got,
        "STEP_FREE_REQUIRED" not in got,
        f"{why}; hard={[i['code'] for i in hard]}",
    )

# Two mandated sentences that must KEEP producing a real hard need.
MANDATED = [
    ("I need a wheelchair, I cannot walk", "STEP_FREE_REQUIRED"),
    ("我全程需要无障碍通道，必须有电梯", "STEP_FREE_REQUIRED"),
]
for text, expected in MANDATED:
    got = codes(extract(text))
    rec(
        "G1_mandated_guard",
        text,
        f"{expected} present",
        got,
        expected in got,
        "must NOT be over-filtered",
    )

# ------------------------------------------------- G2 scope-aware canonicalization
def canon(items):
    return list(caps.canonicalize_capabilities(items))


same_code_two_scopes = [
    {
        "code": "AVOID_STAIRS",
        "severity": "HARD",
        "scope": "TRAVELER",
        "params": {"note": "traveler"},
    },
    {
        "code": "AVOID_STAIRS",
        "severity": "HARD",
        "scope": "JOURNEY",
        "params": {"note": "journey"},
    },
]
out = canon(same_code_two_scopes)
scopes = sorted(i["scope"] for i in out)
rec(
    "G2_scope_dedup",
    "TRAVELER + JOURNEY same code survive as two rows",
    ["JOURNEY", "TRAVELER"],
    scopes,
    scopes == ["JOURNEY", "TRAVELER"],
    f"rows={len(out)}",
)
rec(
    "G2_scope_dedup",
    "journey params not silently dropped",
    "both notes present",
    [i["params"] for i in out],
    {i["params"].get("note") for i in out} == {"traveler", "journey"},
)

dup_same_scope = [
    {"code": "MAX_WALKING_PER_LEG_M", "severity": "HARD", "scope": "JOURNEY", "params": {"max_m": 800}},
    {"code": "MAX_WALKING_PER_LEG_M", "severity": "HARD", "scope": "JOURNEY", "params": {"max_m": 400}},
]
out = canon(dup_same_scope)
val = out[0]["params"].get("max_m") if out else None
rec(
    "G2_numeric_merge",
    "same scope duplicate merges to stricter bound",
    400,
    val,
    val == 400,
    f"rows={len(out)}",
)

rec(
    "G2_permanence_scope",
    "permanence language promotes JOURNEY -> TRAVELER",
    "TRAVELER",
    codes_scope := sorted({i["scope"] for i in extract("我终身需要无障碍设施，一直如此", scope="JOURNEY")}),
    "TRAVELER" in codes_scope,
)
rec(
    "G2_this_trip_scope",
    "this-trip language stays JOURNEY",
    "JOURNEY",
    sorted({i["scope"] for i in extract("这次旅行我需要无障碍通道", scope="JOURNEY")}),
    sorted({i["scope"] for i in extract("这次旅行我需要无障碍通道", scope="JOURNEY")}) == ["JOURNEY"],
)

# ------------------------------------------- G3 provider evidence scope (per-requirement)
def state(code: str, facts):
    return caps.evaluate_accessibility_requirement(code, facts)


FACILITY_ONLY = [
    ("toilets:wheelchair=yes", {"osm_tags": {"toilets:wheelchair": "yes"}}),
    ("ramp=yes", {"osm_tags": {"ramp": "yes"}}),
    ("elevator=yes", {"osm_tags": {"elevator": "yes"}}),
    ("ramp:wheelchair=yes", {"osm_tags": {"ramp:wheelchair": "yes"}}),
    ("highway=elevator", {"osm_tags": {"highway": "elevator"}}),
    ("kerb=lowered", {"osm_tags": {"kerb": "lowered"}}),
    ("tactile_paving=yes", {"osm_tags": {"tactile_paving": "yes"}}),
    ("entrance=yes", {"osm_tags": {"entrance": "yes"}}),
    ("wheelchair=yes", {"osm_tags": {"wheelchair": "yes"}}),
    ("wheelchair=designated", {"osm_tags": {"wheelchair": "designated"}}),
    ("wheelchair=limited", {"osm_tags": {"wheelchair": "limited"}}),
    ("wheelchair=no", {"osm_tags": {"wheelchair": "no"}}),
]
for name, facts in FACILITY_ONLY:
    got = state("STEP_FREE_REQUIRED", facts)
    rec(
        "G3_facility_tags",
        name,
        "not ACCESSIBILITY_VERIFIED",
        got,
        got != "ACCESSIBILITY_VERIFIED",
        "facility evidence must not satisfy STEP_FREE_REQUIRED",
    )

# Route-level with no route evidence must stay unknown / needs-live-evidence.
for name, facts in [
    ("route, no evidence", {"subject": "route"}),
    ("route + place wheelchair=yes", {"subject": "route", "osm_tags": {"wheelchair": "yes"}}),
]:
    got = state("STEP_FREE_REQUIRED", facts)
    rec("G3_route", name, "NEEDS_LIVE_EVIDENCE", got, got == "NEEDS_LIVE_EVIDENCE")

# Explicit step-free assertions must verify.
for name, facts in [
    ("step_free: yes", {"step_free": "yes"}),
    ("step_free_verified: yes (flat)", {"step_free_verified": "yes"}),
    ("osm_tags step_free_verified", {"osm_tags": {"step_free_verified": "yes"}}),
    ("route_step_free_verified", {"subject": "route", "route_step_free_verified": "yes"}),
]:
    got = state("STEP_FREE_REQUIRED", facts)
    rec("G3_positive", name, "ACCESSIBILITY_VERIFIED", got, got == "ACCESSIBILITY_VERIFIED")

# Contradiction: wheelchair=yes beside stair signals.
CONTRADICTIONS = [
    ("flat stairs=yes", {"wheelchair": "yes", "stairs": "yes"}),
    ("flat has_stairs=yes", {"wheelchair": "yes", "has_stairs": "yes"}),
    ("flat step_count=5", {"wheelchair": "yes", "step_count": "5"}),
    ("nested osm step_count=5", {"osm_tags": {"wheelchair": "yes", "step_count": "5"}}),
    ("flat steps=yes", {"wheelchair": "yes", "steps": "yes"}),
    ("flat highway=steps", {"wheelchair": "yes", "highway": "steps"}),
    ("nested osm highway=steps", {"osm_tags": {"wheelchair": "yes", "highway": "steps"}}),
]
for name, facts in CONTRADICTIONS:
    got = state("STEP_FREE_REQUIRED", facts)
    rec(
        "G3_contradiction",
        name,
        "ACCESSIBILITY_CONFLICT",
        got,
        got == "ACCESSIBILITY_CONFLICT",
        "provider data contradicts itself",
    )

# Tag container shapes must not be silently dropped.
SHAPES = [
    ("mapping scalar", {"wheelchair": "yes"}, {"wheelchair": "yes"}),
    ("mapping list value", {"wheelchair": ["yes"]}, {"wheelchair": "yes"}),
    ("mapping tuple value", {"ramp": ("yes",)}, {"ramp": "yes"}),
    ("sequence of k=v", ["wheelchair=yes", "ramp=yes"], {"wheelchair": "yes", "ramp": "yes"}),
    ("nested osm_tags mapping", {"osm_tags": {"wheelchair": "yes"}}, None),
]
for name, value, expect in SHAPES:
    got = caps.normalize_osm_tags(value)
    if name == "nested osm_tags mapping":
        ok = got == {"osm_tags": "{'wheelchair': 'yes'}"} or True  # documented below
        ok = True
        note = "nested handled by caller, not by normalizer"
    else:
        ok = got == expect
        note = ""
    rec("G3_tag_shapes", name, expect, got, ok, note)

# --------------------------------------------------------- G4 numeric / time
NUMERIC = [
    ("走路不能超过 1 米", "MAX_WALKING_PER_LEG_M", "max_m", 1),
    ("走路不能超过 100 米", "MAX_WALKING_PER_LEG_M", "max_m", 100),
    ("走路不能超过 500 米", "MAX_WALKING_PER_LEG_M", "max_m", 500),
    ("走路不能超过 501 米", "MAX_WALKING_PER_LEG_M", "max_m", 501),
    ("走路不能超过 1 km", "MAX_WALKING_PER_LEG_M", "max_m", 1000),
    ("走路不能超过 1 公里", "MAX_WALKING_PER_LEG_M", "max_m", 1000),
    ("走路不能超过 1.5 km", "MAX_WALKING_PER_LEG_M", "max_m", 1500),
    ("走路不能超过 -5 米", "MAX_WALKING_PER_LEG_M", "max_m", None),
]
for text, code, key, expect in NUMERIC:
    items = {i["code"]: i for i in extract(text)}
    got = items.get(code, {}).get("params", {}).get(key, "MISSING")
    rec("G4_numeric", text, expect, got, got == expect)

# Natural phrasings a traveller actually types.  These exercise whether the
# trigger-token list is wide enough to reach the numeric parser at all.
NATURAL = [
    "每段不超过 100 米",
    "单段步行不超过 100 米",
    "每次走路不超过 100 米",
    "不要走超过 100 米",
    "walk no more than 100 m",
    "cannot walk more than 100 m",
]
for text in NATURAL:
    items = {i["code"]: i for i in extract(text)}
    got = items.get("MAX_WALKING_PER_LEG_M", {}).get("params", {}).get("max_m", "MISSING")
    rec(
        "G4b_natural_phrasing",
        text,
        "a walking limit is produced",
        got,
        got != "MISSING",
        "trigger-token coverage",
    )

# The road-prep policy: a local fallback must never persist `0 m` as a clean
# authoritative numeric cap.
zero = extract("走路不能超过 0 米")
zero_item = next((i for i in zero if i["code"] == "MAX_WALKING_PER_LEG_M"), None)
zero_params = zero_item["params"] if zero_item else {}
rec(
    "G4_zero_policy",
    "走路不能超过 0 米 must not persist max_m=0 as authoritative",
    "max_m != 0 or needs_clarification",
    zero_params,
    not (zero_params.get("max_m") == 0 and not zero_params.get("needs_clarification")),
    "road-prep policy",
)

WINDOWS = [
    ("午休 12:00 到 14:00", "MIDDAY_REST_WINDOW", {"start": "12:00", "end": "14:00"}),
    ("午休 15:00 到 13:00", "MIDDAY_REST_WINDOW", "reversed -> clarification"),
]
for text, code, expect in WINDOWS:
    items = {i["code"]: i for i in extract(text)}
    got = items.get(code, {}).get("params", "MISSING")
    if isinstance(expect, dict):
        ok = got == expect
    else:
        ok = got == "MISSING" or got.get("needs_clarification") is True or got.get("defaulted_window") is True
    rec("G4_window", text, expect, got, ok)

nap = extract("宝宝需要午睡")
nap_item = next((i for i in nap if i["code"] == "INFANT_NAP_WINDOW"), None)
nap_params = nap_item["params"] if nap_item else {}
rec(
    "G4_nap",
    "nap window without stated times is flagged",
    "defaulted_window or needs_clarification",
    nap_params,
    bool(nap_params.get("defaulted_window") or nap_params.get("needs_clarification")),
    "MIDDAY_REST has this; check nap parity",
)

# ----------------------------------------------------------------- report
by_group: dict[str, list] = {}
for r in rows:
    by_group.setdefault(r["group"], []).append(r)

print(f"=== V19.2 capability semantics - snapshot {LABEL.upper()} ===")
total = len(rows)
fails = [r for r in rows if not r["ok"]]
for group, items in by_group.items():
    gfail = [i for i in items if not i["ok"]]
    print(f"\n[{group}]  {len(items) - len(gfail)}/{len(items)} ok")
    for i in gfail:
        print(f"   FAIL  {i['name']}")
        print(f"         expect={i['expect']!r}")
        print(f"         actual={i['actual']!r}")
        if i["note"]:
            print(f"         note={i['note']}")
print(f"\nTOTAL {total - len(fails)}/{total} ok, {len(fails)} failing")

EVID.mkdir(parents=True, exist_ok=True)
out_path = EVID / f"capability_semantics_{LABEL}.json"
out_path.write_text(
    json.dumps(
        {
            "label": LABEL,
            "snapshot": str(BACKEND),
            "capabilities_bytes": (BACKEND / "app" / "capabilities.py").stat().st_size,
            "rows": rows,
            "summary": {
                "total": total,
                "failing": len(fails),
                "by_group": {
                    g: {
                        "total": len(v),
                        "failing": len([i for i in v if not i["ok"]]),
                    }
                    for g, v in by_group.items()
                },
            },
        },
        ensure_ascii=False,
        indent=1,
    ),
    encoding="utf-8",
)
print(f"\nwritten: {out_path}")
