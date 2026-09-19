from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/main.py")
s = p.read_text(encoding="utf-8")

old = '''    recovery = recovery_state(session, journey, is_feasible=is_feasible, failures=failures)
    if recovery is not None:
        recovery["journey_status"] = journey.status
    payload["recovery"] = recovery
    # Staleness is an independent condition: the selected plan's frozen
    # evidence may have expired without any HARD capability recovery event.
    staleness = any("STALE_RECOMPOSE_REQUIRED" in item for item in failures)
    payload["experience_flags"] = {
        "needs_review": bool(recovery) or staleness,
        "recovery_required": bool(recovery),
        "staleness": staleness,
        "feasibility_failures": failures,
    }
    return payload'''

new = '''    # A feasible selected plan means the durable recovery is genuinely over:
    # resolve it transactionally so the Event, this projection and the phone UI
    # can never disagree, and a page reload cannot resurrect it.
    if is_feasible is True:
        resolve_recovery_events(session, journey)
    recovery = recovery_state(session, journey, is_feasible=is_feasible, failures=failures)
    if recovery is not None:
        recovery["journey_status"] = journey.status
    payload["recovery"] = recovery
    # Staleness is an independent condition: the selected plan's frozen
    # evidence may have expired without any HARD capability recovery event.
    staleness = any("STALE_RECOMPOSE_REQUIRED" in item for item in failures)
    open_recovery = recovery is not None and recovery.get("state") != "RESOLVED"
    flags = recovery_flags(session, journey)
    flags["staleness"] = staleness
    flags["feasibility_failures"] = failures
    flags["needs_review"] = bool(open_recovery) or staleness
    flags["recovery_required"] = bool(open_recovery)
    flags["acknowledged"] = bool(recovery and recovery.get("acknowledged"))
    flags["recovery_state"] = recovery.get("state") if recovery else None
    payload["experience_flags"] = flags
    return payload'''
assert old in s, "experience block not found"
s = s.replace(old, new, 1)

s = s.replace(
    "from app.planning.hard_recovery import (\n    open_recovery_event,\n    recovery_state,\n    resolve_recovery_events,\n)",
    "from app.planning.hard_recovery import (\n    acknowledge_recovery,\n    open_recovery_event,\n    record_replan_outcome,\n    recovery_flags,\n    recovery_state,\n    resolve_recovery_events,\n)",
    1,
)
p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("ok")
