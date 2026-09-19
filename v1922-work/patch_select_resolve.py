from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/main.py")
s = p.read_text(encoding="utf-8")

old = '''    journey.status = "PLANNED"
    journey.active_plan_version_id = plan.id
    journey.updated_at = datetime.now(timezone.utc).isoformat()
    after = {
        "journey": journey_schema(journey).model_dump(mode="json"),
        "plan_status": plan.status,
        "previous_selected_plan_id": current.id if current else None,
    }
    record_audit(
        session,
        action="plan.selected",'''

new = '''    journey.status = "PLANNED"
    journey.active_plan_version_id = plan.id
    journey.updated_at = datetime.now(timezone.utc).isoformat()
    # The plan just passed the same feasibility gate used by generate/start, so
    # any open recovery is genuinely over.  Resolve it in the same transaction
    # so the Event, /experience and the phone UI cannot disagree.
    resolved_recovery = resolve_recovery_events(session, journey)
    after = {
        "journey": journey_schema(journey).model_dump(mode="json"),
        "plan_status": plan.status,
        "previous_selected_plan_id": current.id if current else None,
        "resolved_recovery_events": resolved_recovery,
    }
    record_audit(
        session,
        action="plan.selected",'''
assert old in s, "select transition not found"
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("select 已接线解决恢复")
