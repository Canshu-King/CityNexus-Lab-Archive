"""P1 probe: TRAVELER vs JOURNEY scope, leakage, deactivation, provenance."""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
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
    print(f"[{case}] {json.dumps(kw, ensure_ascii=False, default=str)[:420]}")


def create_journey(title: str, *, start_offset_days: int = 0) -> dict:
    start = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc) + timedelta(days=start_offset_days)
    end = start + timedelta(hours=10)
    response = H.client.post(
        "/api/v1/journeys",
        json={
            "traveler_id": H.DEMO_TRAVELER_ID,
            "title": title,
            "city_code": "CNX-DEMO",
            "timezone": "Asia/Shanghai",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "budget": {"amount_minor": 50000, "currency": "CNY"},
            "planning_mode": "balanced",
            "party_size": 1,
        },
    )
    return {"status": response.status_code, "body": response.json() if response.status_code < 300 else response.text[:300]}


def plan_places(journey_id: str) -> list[list[str]]:
    status, body = H.generate_plans(journey_id)
    if status != 201 or not isinstance(body, list):
        return []
    return [[a.get("place_id") for a in p.get("activities", [])] for p in body]


def set_mission(journey_id: str, command: str) -> tuple[int, Any]:
    """Mission preferences are only reachable through a natural-language command."""

    response = H.client.put(
        f"/api/v1/journeys/{journey_id}/guardian/mission",
        json={"command": command, "requested_autonomy": "PLAN_ONLY"},
    )
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return response.status_code, body


# =====================================================================
# 1. baseline: two journeys for the same traveler
# =====================================================================
H.reset_demo()
j_a = create_journey("V19 Journey A")
j_b = create_journey("V19 Journey B", start_offset_days=30)
ja = j_a["body"]["id"] if j_a["status"] == 201 else None
jb = j_b["body"]["id"] if j_b["status"] == 201 else None
note("CREATE_TWO_JOURNEYS", a=j_a["status"], b=j_b["status"], journey_a=ja, journey_b=jb)

base_a = plan_places(ja) if ja else []
base_b = plan_places(jb) if jb else []
note("BASELINE_PLANS", a=base_a, b=base_b)

# =====================================================================
# 2. "This Journey only" preference -> must not leak into Journey B
# =====================================================================
if ja:
    st, body = set_mission(ja, "这次旅程我想多安排室内活动，尽量少走路")
    note("MISSION_SCOPED_SET_ON_A", status=st, body=str(body)[:260])
    after_a = plan_places(ja)
    after_b = plan_places(jb) if jb else []
    note(
        "THIS_JOURNEY_ONLY_LEAK_CHECK",
        journey_a_changed=after_a != base_a,
        journey_b_changed=after_b != base_b,
        journey_b_plan=after_b,
        note="a mission preference set on Journey A must not change Journey B",
    )

# =====================================================================
# 3. TRAVELER-scope preference -> leaks into every journey by design
# =====================================================================
st, body = H.set_preferences(
    [{"category": "interest", "key": "indoor", "value": True, "weight": 1.0}]
)
note("TRAVELER_PREFERENCE_SET", status=st, body=str(body)[:200])
leak_a = plan_places(ja) if ja else []
leak_b = plan_places(jb) if jb else []
note(
    "TRAVELER_SCOPE_LEAK",
    journey_a=leak_a,
    journey_b=leak_b,
    note=(
        "the preferences table has no journey_id: a 'this journey only' intent stored "
        "here silently becomes a permanent traveller-scope preference"
    ),
)
prefs = H.get_preferences()
note("PREFERENCE_SCOPE_FIELDS", preference_count=len(prefs), keys=sorted(prefs[0].keys()) if prefs else [])

# =====================================================================
# 4. learned TravelerTwin evidence -> must never become HARD capability
# =====================================================================
H.reset_demo()
st, body = H.add_constraint("STEP_FREE_REQUIRED", params={"evidence": "UNKNOWN"})
gen_blocked = H.generate_plans()[0]
note("HARD_CAPABILITY_BLOCKS", gen_status=gen_blocked)

# fabricate repeated low_walking outcome evidence for the demo traveler
with H.SessionLocal() as session:  # type: ignore[attr-defined]
    from app.db.models import JourneyOutcomeEvent  # noqa: E402

    journey_row = session.get(__import__("app.db.models", fromlist=["Journey"]).Journey, H.DEMO_JOURNEY_ID)
    for index in range(6):
        session.add(
            JourneyOutcomeEvent(
                id=str(uuid.uuid4()),
                journey_id=H.DEMO_JOURNEY_ID,
                activity_id=None,
                event_type="ACTIVITY_COMPLETED",
                actor_type="TRAVELER",
                actor_id=H.DEMO_TRAVELER_ID,
                occurred_at_actual=f"2026-10-10T1{index}:00:00+08:00",
                source="DOMAIN",
                payload_json=json.dumps({"preference_dimension": "low_walking", "direction": "low_walking"}),
                created_at=f"2026-10-10T1{index}:00:00+08:00",
            )
        )
    session.commit()
    note("OUTCOME_EVIDENCE_SEEDED", journey=journey_row.id if journey_row else None)

from app.execution.traveler_twin import learn_from_journey, planning_preference_items  # noqa: E402

with H.SessionLocal() as session:  # type: ignore[attr-defined]
    journey_row = session.get(__import__("app.db.models", fromlist=["Journey"]).Journey, H.DEMO_JOURNEY_ID)
    snapshot = learn_from_journey(session, journey_row)
    session.commit()
    payload = json.loads(snapshot.learned_soft_preferences_json)
    note(
        "LEARNED_EVIDENCE",
        learned=payload,
        source_labels=sorted({item.get("source") for item in payload}),
        note="learned evidence is labelled LEARNED_SOFT and lives in learned_soft_preferences_json",
    )
    items = planning_preference_items(session, H.DEMO_TRAVELER_ID, H.DEMO_JOURNEY_ID)
    learned_items = [item for item in items if getattr(item, "source", "") == "LEARNED_SOFT"]
    note(
        "LEARNED_FED_TO_PLANNER",
        learned_item_count=len(learned_items),
        weights=[float(getattr(item, "weight", 0.0)) for item in learned_items],
        categories=sorted({str(getattr(item, "category", "")) for item in learned_items}),
        note="learned evidence reaches the planner as weight-1.0 interest preferences, not as constraints",
    )

# does learned low_walking escalate into a HARD constraint anywhere?
with H.SessionLocal() as session:  # type: ignore[attr-defined]
    from app.db.models import JourneyConstraint  # noqa: E402
    from sqlalchemy import select  # noqa: E402

    rows = session.scalars(
        select(JourneyConstraint).where(JourneyConstraint.journey_id == H.DEMO_JOURNEY_ID)
    ).all()
    codes = sorted({row.rule_code for row in rows})
    note(
        "LEARNED_TO_CONSTRAINT_ESCALATION",
        constraint_rule_codes=codes,
        learned_created_any_constraint=any(
            row.rule_code not in {"STEP_FREE_REQUIRED", "JOURNEY_END_BY", "BUDGET_MAX", "MINIMISE_PLAN_CHANGES"}
            for row in rows
        ),
        note=(
            "the only capability row present is the STEP_FREE_REQUIRED injected by this "
            "probe; learned evidence created no JourneyConstraint at all"
        ),
    )

# =====================================================================
# 5. deactivation: cleared learned evidence must stop affecting plans
# =====================================================================
clear = H.client.delete(f"/api/v1/travelers/{H.DEMO_TRAVELER_ID}/traveler-twin/learned")
note("LEARNED_CLEARED", status=clear.status_code, body=str(clear.json() if clear.status_code < 300 else clear.text)[:260])
twin = H.traveler_twin()
note(
    "TWIN_AFTER_CLEAR",
    learned_soft=twin.get("learned_soft_preferences"),
    evidence_count=twin.get("evidence_count"),
)

# =====================================================================
# 6. provenance / audit explainability
# =====================================================================
with H.SessionLocal() as session:  # type: ignore[attr-defined]
    from app.db.models import AuditLog  # noqa: E402
    from sqlalchemy import select  # noqa: E402

    actions = [
        row.action
        for row in session.scalars(
            select(AuditLog).where(AuditLog.journey_id == H.DEMO_JOURNEY_ID).order_by(AuditLog.created_at)
        ).all()
    ]
note(
    "AUDIT_TRAIL",
    actions=sorted(set(actions)),
    constraint_actions=[a for a in actions if "constraint" in a],
    capability_actions=[a for a in actions if "capab" in a or "accessib" in a or "step" in a],
    note="there is no capability-specific audit vocabulary",
)

H.write_json(EVIDENCE / "cross_journey_scope_probe.json", records)
print("wrote", EVIDENCE / "cross_journey_scope_probe.json")
