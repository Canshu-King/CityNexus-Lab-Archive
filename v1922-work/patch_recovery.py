"""Wire durable HARD capability recovery into the confirm endpoint."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/main.py")
s = P.read_text(encoding="utf-8")

old = '''    feasibility = None
    if journey.status == "ACTIVE":
        gate = validate_selected_plan_feasibility(session, journey)
        feasibility = {
            "passed": gate.passed if gate else None,
            "failures": list(gate.failures) if gate else [],
            "state": "PLAN_FEASIBLE" if gate and gate.passed else "REPLAN_REQUIRED" if gate else "NO_ACTIVE_PLAN",
        }
    snapshot = refresh_snapshot(session, journey.traveler_id)
    session.commit()
    return {"journey_id": journey.id, "capabilities": rows, "summary": summarize_capabilities(rows), "traveler_twin": traveler_twin_payload(snapshot), "active_plan_feasibility": feasibility}'''

new = '''    feasibility = None
    recovery = None
    if journey.status == "ACTIVE":
        # Re-evaluate the active plan against the newly confirmed capability.
        # A HARD need (or any evidence regression) invalidates it; the active
        # plan itself is never silently rewritten.
        try:
            gate = validate_selected_plan_feasibility(session, journey)
            failures = list(gate.failures) if gate else []
            passed = gate.passed if gate else None
        except ValueError as exc:
            # Stale/inconsistent frozen evidence is itself an invalidation.
            failures = [str(exc)]
            passed = False
        feasibility = {
            "passed": passed,
            "failures": failures,
            "state": (
                "PLAN_FEASIBLE"
                if passed
                else "REPLAN_REQUIRED"
                if passed is False
                else "NO_ACTIVE_PLAN"
            ),
        }
        hard_codes = [
            str(item["code"])
            for item in rows
            if str(item.get("severity", "")).upper() == "HARD"
        ]
        if passed is False:
            # Durable, governed recovery state - not a response-only field.
            hard_code = hard_codes[0] if hard_codes else "EVIDENCE_REGRESSION"
            event = open_recovery_event(
                session,
                journey,
                capability_code=hard_code,
                capability_params={},
                failures=failures,
            )
            record_audit(
                session,
                action="journey.recovery.required",
                entity_type="Event",
                entity_id=event.id,
                journey_id=journey.id,
                actor_type="USER",
                actor_id=journey.traveler_id,
                after={
                    "reason": "HARD_CAPABILITY_INVALIDATES_ACTIVE_PLAN",
                    "capability_code": hard_code,
                    "failures": failures,
                },
            )
            recovery = recovery_state(
                session, journey, is_feasible=False, failures=failures
            )
        elif passed is True:
            resolve_recovery_events(session, journey)
    snapshot = refresh_snapshot(session, journey.traveler_id)
    session.commit()
    return {
        "journey_id": journey.id,
        "capabilities": rows,
        "summary": summarize_capabilities(rows),
        "traveler_twin": traveler_twin_payload(snapshot),
        "active_plan_feasibility": feasibility,
        "recovery": recovery,
    }'''

assert old in s, "confirm endpoint block not found"
s = s.replace(old, new, 1)

# Wire recovery into /experience
old2 = '''@app.get("/api/v1/journeys/{journey_id}/experience")
def get_journey_experience(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    return experience_payload(session, journey)'''
new2 = '''@app.get("/api/v1/journeys/{journey_id}/experience")
def get_journey_experience(journey_id: UUID, session: Session = Depends(get_session)):
    journey = require(session, Journey, str(journey_id), "Journey")
    payload = experience_payload(session, journey)
    # Surface the durable recovery state (and, if the plan is still ACTIVE,
    # re-check feasibility so a stale plan cannot look healthy to the phone).
    failures: list[str] = []
    is_feasible: bool | None = None
    if journey.status == "ACTIVE":
        try:
            gate = validate_selected_plan_feasibility(session, journey)
            is_feasible = None if gate is None else bool(gate.passed)
            failures = list(gate.failures) if gate else []
        except ValueError as exc:
            is_feasible = False
            failures = [str(exc)]
    recovery = recovery_state(session, journey, is_feasible=is_feasible, failures=failures)
    if recovery is not None:
        recovery["journey_status"] = journey.status
    payload["recovery"] = recovery
    payload["experience_flags"] = {
        "needs_review": bool(recovery),
        "recovery_required": bool(recovery),
        "staleness": any("STALE_RECOMPOSE_REQUIRED" in item for item in failures),
        "feasibility_failures": failures,
    }
    return payload'''
assert old2 in s, "experience endpoint not found"
s = s.replace(old2, new2, 1)

s = s.replace(
    "from app.replanning.provider_snapshots import MobilitySnapshot, TravelEstimateFact",
    "from app.planning.hard_recovery import (\n"
    "    open_recovery_event,\n"
    "    recovery_state,\n"
    "    resolve_recovery_events,\n"
    ")\n"
    "from app.replanning.provider_snapshots import MobilitySnapshot, TravelEstimateFact",
    1,
)
P.write_text(s, encoding="utf-8", newline="\n")
print("recovery wired")
