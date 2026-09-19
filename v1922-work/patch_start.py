"""Start must re-use the exact select/booking truth policy."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/main.py")
s = P.read_text(encoding="utf-8")

old = '''    plan = session.get(PlanVersion, journey.active_plan_version_id)
    if plan is None or plan.status != "SELECTED":
        raise HTTPException(409, "selected plan is missing or inconsistent")
    activities = session.scalars(
        select(Activity).where(Activity.plan_version_id == plan.id).order_by(Activity.sequence_no)
    ).all()
    journey.status = "ACTIVE"'''

new = '''    plan = session.get(PlanVersion, journey.active_plan_version_id)
    if plan is None or plan.status != "SELECTED":
        raise HTTPException(409, "selected plan is missing or inconsistent")
    # /start must apply the same evidence/staleness truth policy as select and
    # booking.  Starting a journey on expired frozen provider evidence is a
    # silent safety regression, so refuse it and surface the re-sync condition.
    try:
        gate = validate_selected_plan_feasibility(session, journey)
    except ValueError as exc:
        message = str(exc)
        raise HTTPException(409, message) from exc
    if gate is not None and not gate.passed:
        raise HTTPException(
            409,
            "START_BLOCKED_INFEASIBLE: " + ", ".join(gate.failures),
        )
    activities = session.scalars(
        select(Activity).where(Activity.plan_version_id == plan.id).order_by(Activity.sequence_no)
    ).all()
    journey.status = "ACTIVE"'''

assert old in s, "start block not found"
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("start patched")
