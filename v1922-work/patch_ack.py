from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/main.py")
s = p.read_text(encoding="utf-8")

anchor = '''@app.get("/api/v1/travelers/{traveler_id}/traveler-twin")
def get_traveler_twin(traveler_id: UUID, session: Session = Depends(get_session)):'''

new_endpoint = '''@app.post("/api/v1/journeys/{journey_id}/recovery/acknowledge")
def acknowledge_journey_recovery(
    journey_id: UUID, session: Session = Depends(get_session)
):
    """Governed acknowledgement of an open recovery warning.

    This records that the traveller saw the warning.  It deliberately does NOT
    resolve the recovery, does not mark the plan feasible, and does not hide the
    journey truth: ``experience_flags.needs_review`` stays true until a
    revalidated feasible plan is actually selected.
    """

    journey = require(session, Journey, str(journey_id), "Journey")
    event = acknowledge_recovery(session, journey)
    if event is None:
        raise HTTPException(404, "no open recovery to acknowledge")
    failures: list[str] = []
    is_feasible: bool | None = None
    if journey.active_plan_version_id:
        try:
            gate = validate_selected_plan_feasibility(session, journey)
            is_feasible = None if gate is None else bool(gate.passed)
            failures = list(gate.failures) if gate else []
        except ValueError as exc:
            is_feasible = False
            failures = [str(exc)]
    record_audit(
        session,
        action="journey.recovery.acknowledged",
        entity_type="Event",
        entity_id=event.id,
        journey_id=journey.id,
        actor_type="USER",
        actor_id=journey.traveler_id,
        after={"acknowledged": True, "resolved": False, "still_infeasible": is_feasible is False},
    )
    recovery = recovery_state(
        session, journey, is_feasible=is_feasible, failures=failures
    )
    session.commit()
    return {
        "journey_id": journey.id,
        "acknowledged": True,
        "resolved": False,
        "recovery": recovery,
    }


@app.get("/api/v1/travelers/{traveler_id}/traveler-twin")
def get_traveler_twin(traveler_id: UUID, session: Session = Depends(get_session)):'''

assert anchor in s, "twin endpoint anchor not found"
s = s.replace(anchor, new_endpoint, 1)
p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("acknowledge 端点已添加")
