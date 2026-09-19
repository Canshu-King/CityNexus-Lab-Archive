"""Experience flags must always expose staleness, not only when recovery exists."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/main.py")
s = P.read_text(encoding="utf-8")

old = '''    recovery = recovery_state(session, journey, is_feasible=is_feasible, failures=failures)
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

new = '''    recovery = recovery_state(session, journey, is_feasible=is_feasible, failures=failures)
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
assert old in s, "experience flags block not found"
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
