from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/planning/anchor_schedule.py")
s = p.read_text(encoding="utf-8")
assert "_estimate_gap_minutes" in s and "def _estimate_gap_minutes" not in s

helper = '''def _estimate_gap_minutes(
    travel_minutes: Mapping[tuple[str, str], int] | None,
    origin: str | None,
    destination: str | None,
) -> int:
    """Frozen travel time for one leg, or the deterministic fixture default."""

    if not origin or not destination:
        return 0
    if travel_minutes is not None:
        value = travel_minutes.get((origin, destination))
        if value is not None:
            return int(value)
    return DEFAULT_TRAVEL_MIN


'''
marker = "def _anchor_windows("
assert marker in s
s = s.replace(marker, helper + marker, 1)
p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("helper 已恢复，语法 ok")
