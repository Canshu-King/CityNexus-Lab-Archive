"""P0 probe: does a HARD accessibility/capability constraint change planning?

Run against the isolated copy.  Writes evidence/accessibility_truth_probe.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LAB_ROOT = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
sys.path.insert(0, str(LAB_ROOT / "repo_copy" / "backend" / "tests"))
import v19_harness as H  # noqa: E402

LAB = H.LAB
EVIDENCE = LAB / "evidence"
records: list[dict] = []


def note(case: str, **kw):
    entry = {"case": case}
    entry.update(kw)
    records.append(entry)
    print(f"[{case}] {json.dumps({k: v for k, v in kw.items() if k != 'plan_titles'}, ensure_ascii=False, default=str)[:400]}")


def baseline_plan_ids() -> list[str]:
    status, body = H.generate_plans()
    if status != 201 or not isinstance(body, list):
        return []
    return [p["id"] for p in body]


def plan_signature(body) -> list[list[str]]:
    if not isinstance(body, list):
        return []
    return [[a.get("place_id") or a.get("city_service_id") for a in p.get("activities", [])] for p in body]


# ---------------------------------------------------------------- baseline
H.reset_demo()
status, base = H.generate_plans()
base_sig = plan_signature(base)
note(
    "BASELINE_PLANS",
    status=status,
    plan_count=len(base) if isinstance(base, list) else None,
    signatures=base_sig,
    locked_places=[
        a.get("place_id")
        for p in (base if isinstance(base, list) else [])
        for a in p.get("activities", [])
        if a.get("locked")
    ],
)

# ------------------------------------------------- 1. verified step-free (simulated via HARD rule)
H.reset_demo()
st, cbody = H.add_constraint("STEP_FREE_REQUIRED", params={"requirement": "VERIFIED_STEP_FREE"})
note("HARD_STEP_FREE_ADD", add_status=st, constraint=cbody)
st2, gen2 = H.generate_plans()
note(
    "HARD_STEP_FREE_GENERATE",
    status=st2,
    plan_count=len(gen2) if isinstance(gen2, list) else None,
    failures=H.recorded_failures(st2, gen2),
    raw=str(gen2)[:600],
)

# ------------------------------------------------- 2. unknown step-free
H.reset_demo()
H.add_constraint("STEP_FREE_REQUIRED", params={"evidence": "UNKNOWN"})
st3, gen3 = H.generate_plans()
note(
    "HARD_STEP_FREE_UNKNOWN_EVIDENCE",
    status=st3,
    plan_count=len(gen3) if isinstance(gen3, list) else None,
    failures=H.recorded_failures(st3, gen3),
    raw=str(gen3)[:400],
)

# ------------------------------------------------- 3. SOFT capability must not block
H.reset_demo()
H.add_constraint("STEP_FREE_REQUIRED", kind="SOFT", params={"evidence": "UNKNOWN"})
st4, gen4 = H.generate_plans()
note(
    "SOFT_STEP_FREE_GENERATE",
    status=st4,
    plan_count=len(gen4) if isinstance(gen4, list) else None,
    failures=H.recorded_failures(st4, gen4),
    identical_to_baseline=plan_signature(gen4) == base_sig,
)

# ------------------------------------------------- 4. walking limit in metres
H.reset_demo()
H.add_constraint("MAX_WALKING_PER_LEG_M", params={"max_m": 1})
st5, gen5 = H.generate_plans()
note(
    "HARD_MAX_WALKING_1M",
    status=st5,
    plan_count=len(gen5) if isinstance(gen5, list) else None,
    failures=H.recorded_failures(st5, gen5),
    identical_to_baseline=plan_signature(gen5) == base_sig,
)

# ------------------------------------------------- 5. quiet environment
H.reset_demo()
H.add_constraint("QUIET_ENVIRONMENT", params={"max_db": 40})
st6, gen6 = H.generate_plans()
note(
    "HARD_QUIET_ENVIRONMENT",
    status=st6,
    plan_count=len(gen6) if isinstance(gen6, list) else None,
    failures=H.recorded_failures(st6, gen6),
    identical_to_baseline=plan_signature(gen6) == base_sig,
)

# ------------------------------------------------- 6. rest / nap windows
H.reset_demo()
H.add_constraint("MIDDAY_REST_WINDOW", params={"start": "12:00", "end": "14:00"})
st7, gen7 = H.generate_plans()
note(
    "HARD_MIDDAY_REST_WINDOW",
    status=st7,
    plan_count=len(gen7) if isinstance(gen7, list) else None,
    failures=H.recorded_failures(st7, gen7),
    identical_to_baseline=plan_signature(gen7) == base_sig,
)

H.reset_demo()
H.add_constraint("INFANT_NAP_WINDOW", params={"start": "13:00", "end": "15:00"})
st8, gen8 = H.generate_plans()
note(
    "HARD_INFANT_NAP_WINDOW",
    status=st8,
    plan_count=len(gen8) if isinstance(gen8, list) else None,
    failures=H.recorded_failures(st8, gen8),
    identical_to_baseline=plan_signature(gen8) == base_sig,
)

# ------------------------------------------------- 7. luggage / stroller
for code in ("LARGE_LUGGAGE", "STROLLER"):
    H.reset_demo()
    H.add_constraint(code, params={"count": 2})
    st9, gen9 = H.generate_plans()
    note(
        f"HARD_{code}",
        status=st9,
        plan_count=len(gen9) if isinstance(gen9, list) else None,
        failures=H.recorded_failures(st9, gen9),
        identical_to_baseline=plan_signature(gen9) == base_sig,
    )

# ------------------------------------------------- 8. known-good HARD still works
H.reset_demo()
H.add_constraint("BUDGET_MAX", category="budget", params={"amount_minor": 100, "currency": "CNY"})
st10, gen10 = H.generate_plans()
note(
    "CONTROL_HARD_BUDGET_MAX_100",
    status=st10,
    plan_count=len(gen10) if isinstance(gen10, list) else None,
    failures=H.recorded_failures(st10, gen10),
    identical_to_baseline=plan_signature(gen10) == base_sig,
)

# ------------------------------------------------- 9. is the constraint echoed to the UI?
H.reset_demo()
H.add_constraint("STEP_FREE_REQUIRED", params={})
note("CONSTRAINT_LIST_VISIBLE", constraints=H.list_constraints())
exp = H.experience()
note(
    "EXPERIENCE_SURFACE_KEYS",
    keys=sorted(exp.keys()),
    mentions_capability=("capability" in json.dumps(exp, ensure_ascii=False).lower()),
    mentions_step_free=("step_free" in json.dumps(exp, ensure_ascii=False).lower()),
    mentions_accessib=("accessib" in json.dumps(exp, ensure_ascii=False).lower()),
)

H.write_json(EVIDENCE / "accessibility_truth_probe.json", records)
print("wrote", EVIDENCE / "accessibility_truth_probe.json")
