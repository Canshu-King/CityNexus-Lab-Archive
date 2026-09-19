"""P1 probe: numeric/boundary + silent-drop attacks on HARD capability rules."""

from __future__ import annotations

import json
import sys
from pathlib import Path

LAB_ROOT = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
sys.path.insert(0, str(LAB_ROOT / "repo_copy" / "backend" / "tests"))
import v19_harness as H  # noqa: E402

EVIDENCE = LAB_ROOT / "evidence"
records: list[dict] = []


def note(case: str, **kw):
    entry = {"case": case}
    entry.update(kw)
    records.append(entry)
    print(f"[{case}] {json.dumps(kw, ensure_ascii=False, default=str)[:320]}")


def try_value(rule_code: str, params: dict, *, kind: str = "HARD", category: str = "capability"):
    H.reset_demo()
    add_status, add_body = H.add_constraint(rule_code, kind=kind, category=category, params=params)
    gen_status, gen_body = H.generate_plans()
    return {
        "add_status": add_status,
        "gen_status": gen_status,
        "plan_count": len(gen_body) if isinstance(gen_body, list) else None,
        "blocked": gen_status != 201,
        "error": (gen_body.get("error", {}).get("message") if isinstance(gen_body, dict) else str(gen_body)[:120]),
    }


# ---------------------------------------------------------------- walking metres
print("== MAX_WALKING_PER_LEG_M boundaries ==")
walking_cases = {
    "zero": {"max_m": 0},
    "one": {"max_m": 1},
    "hundred": {"max_m": 100},
    "just_below_500": {"max_m": 499},
    "at_500": {"max_m": 500},
    "just_above_500": {"max_m": 501},
    "thousand": {"max_m": 1000},
    "huge": {"max_m": 10_000_000},
    "negative": {"max_m": -5},
    "string_numeric": {"max_m": "500"},
    "string_units": {"max_m": "500m"},
    "null": {"max_m": None},
    "absent": {},
    "wrong_key": {"max_walking_m": 500},
    "km_key": {"max_km": 0.5},
}
walking_results = {}
for name, params in walking_cases.items():
    result = try_value("MAX_WALKING_PER_LEG_M", params)
    walking_results[name] = result
    note(f"WALK_{name}", **result)

note(
    "WALK_VALUE_SENSITIVITY",
    interpretation=(
        "All values produce the same outcome => the numeric value is never read; "
        "only the presence of the unsupported HARD rule matters."
    ),
    distinct_outcomes=len({(v["gen_status"], v["plan_count"]) for v in walking_results.values()}),
    outcomes={k: (v["gen_status"], v["plan_count"]) for k, v in walking_results.items()},
)

# ---------------------------------------------------------------- time windows
print("== rest/nap window boundaries ==")
window_cases = {
    "normal": {"start": "12:00", "end": "14:00"},
    "cross_midnight": {"start": "23:30", "end": "01:00"},
    "start_after_end": {"start": "15:00", "end": "13:00"},
    "equal": {"start": "13:00", "end": "13:00"},
    "invalid_text": {"start": "lunchtime", "end": "naptime"},
    "hour_24": {"start": "24:00", "end": "25:00"},
    "empty": {},
    "minutes_only": {"rest_every_min": 60},
    "max_continuous": {"max_continuous_walking_min": 30},
    "rest_every_zero": {"rest_every_min": 0},
    "rest_every_negative": {"rest_every_min": -30},
}
for rule in ("MIDDAY_REST_WINDOW", "INFANT_NAP_WINDOW", "MAX_CONTINUOUS_WALKING_MIN", "REST_EVERY_MIN"):
    for name, params in window_cases.items():
        result = try_value(rule, params)
        note(f"{rule}::{name}", **result)

# ---------------------------------------------------------------- silent drop vectors
print("== silent-drop vectors ==")

# 1. inactive constraint
H.reset_demo()
st, body = H.add_constraint("STEP_FREE_REQUIRED", params={})
cid = body["id"] if isinstance(body, dict) else None
note("DROP_delete_then_generate", delete_status=H.delete_constraint(cid) if cid else None)
gen_status, gen_body = H.generate_plans()
note(
    "DROP_after_delete",
    gen_status=gen_status,
    plan_count=len(gen_body) if isinstance(gen_body, list) else None,
    note="deleting the HARD capability restores planning => capability is not durable",
)

# 2. reactivating via DB flip of active flag
H.reset_demo()
st, body = H.add_constraint("STEP_FREE_REQUIRED", params={})
cid = body["id"] if isinstance(body, dict) else None
import sqlite3  # noqa: E402

db = LAB_ROOT / "v19_redteam.db"
with sqlite3.connect(db) as conn:
    conn.execute("UPDATE constraints SET active = 0 WHERE id = ?", (cid,))
    conn.commit()
gen_status, gen_body = H.generate_plans()
note(
    "DROP_active_flag_zero",
    gen_status=gen_status,
    plan_count=len(gen_body) if isinstance(gen_body, list) else None,
    note="active=0 silences a HARD capability with no audit and no UI warning",
)
note("DROP_active_audit", constraints=[c for c in H.list_constraints() if c["id"] == cid])

# 3. duplicate/conflicting rules: HARD capability + SOFT same rule
H.reset_demo()
H.add_constraint("STEP_FREE_REQUIRED", kind="HARD", params={})
H.add_constraint("STEP_FREE_REQUIRED", kind="SOFT", params={})
gen_status, gen_body = H.generate_plans()
note(
    "CONFLICT_hard_and_soft_same_rule",
    gen_status=gen_status,
    plan_count=len(gen_body) if isinstance(gen_body, list) else None,
    note="HARD still wins (fail-closed); no explicit conflict is surfaced to the traveler",
)

# 4. unsupported HARD with empty rule code
H.reset_demo()
st, body = H.add_constraint("", params={})
gen_status, gen_body = H.generate_plans()
note(
    "EMPTY_RULE_CODE",
    add_status=st,
    gen_status=gen_status,
    plan_count=len(gen_body) if isinstance(gen_body, list) else None,
    failures=H.recorded_failures(gen_status, gen_body),
)

# 5. category-only capability (rule_code that the gate cannot read)
H.reset_demo()
st, body = H.add_constraint("ACCESSIBILITY", category="accessibility", params={"level": "unknown"})
gen_status, gen_body = H.generate_plans()
note(
    "CATEGORY_ONLY_ACCESSIBILITY",
    add_status=st,
    gen_status=gen_status,
    plan_count=len(gen_body) if isinstance(gen_body, list) else None,
)

H.write_json(EVIDENCE / "boundary_and_drop_probe.json", records)
print("wrote", EVIDENCE / "boundary_and_drop_probe.json")
