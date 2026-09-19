from pathlib import Path
P = Path("D:/moodle/CityNexus/backend/app/main.py")
s = P.read_text(encoding="utf-8")
old = '''    failures: list[str] = []
    is_feasible: bool | None = None
    if journey.status == "ACTIVE":
        try:
            gate = validate_selected_plan_feasibility(session, journey)
            is_feasible = None if gate is None else bool(gate.passed)
            failures = list(gate.failures) if gate else []
        except ValueError as exc:
            is_feasible = False
            failures = [str(exc)]'''
new = '''    failures: list[str] = []
    is_feasible: bool | None = None
    # A stale or infeasible selected plan must be visible to the phone whether
    # the journey is still PLANNED (about to start) or already ACTIVE.
    if journey.status in {"PLANNED", "ACTIVE"} and journey.active_plan_version_id:
        try:
            gate = validate_selected_plan_feasibility(session, journey)
            is_feasible = None if gate is None else bool(gate.passed)
            failures = list(gate.failures) if gate else []
        except ValueError as exc:
            is_feasible = False
            failures = [str(exc)]'''
assert old in s
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
