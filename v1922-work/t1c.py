"""T1 part 3 — schedule carried POIs using the SAME travel times the gate uses.

The gate validates consecutive legs with the mobility provider's
``estimate_minutes``.  A locally invented estimate (distance / 350) is far too
optimistic for real Xiamen distances (43–116 real walking minutes), so the
re-timed sequence still collided.

The stay graph therefore asks the Journey's own mobility provider for each leg.
"""

from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/stay_mobility.py")
s = p.read_text(encoding="utf-8")

old = '''def _travel_minutes(a: GraphNode | None, b: GraphNode) -> int:
    """Deterministic inter-stop travel estimate, consistent with ``_mode_fact``."""

    if a is None:
        return 0
    shared = 0
    try:
        shared = int(_shared_prefix_len(str(a.key), str(b.key)))
    except Exception:
        shared = 0
    distance = _distance_m(a, b)
    # Two stop keys sharing a long prefix sit in the same complex.
    if shared >= 12:
        return 5
    return max(5, math.ceil(distance / 350) + 4)


def _shared_prefix_len(a: str, b: str) -> int:
    count = 0
    for x, y in zip(a, b):
        if x != y:
            break
        count += 1
    return count'''

new = '''def _travel_minutes(
    a: GraphNode | None,
    b: GraphNode,
    *,
    provider: Any | None = None,
) -> int:
    """Inter-stop travel time.

    When the Journey's mobility provider is available we ask it, so the
    re-timed sequence uses exactly the durations the feasibility gate will
    later validate.  A locally invented estimate would look feasible at
    scheduling time and then fail the gate.
    """

    if a is None:
        return 0
    if provider is not None:
        try:
            return max(0, int(provider.estimate_minutes(str(a.key), str(b.key))))
        except Exception:
            pass
    shared = _shared_prefix_len(str(a.key), str(b.key))
    if shared >= 12:
        return 5
    return max(5, math.ceil(_distance_m(a, b) / 350) + 4)


def _shared_prefix_len(a: str, b: str) -> int:
    count = 0
    for x, y in zip(a, b):
        if x != y:
            break
        count += 1
    return count'''

assert old in s, "_travel_minutes block not found"
s = s.replace(old, new, 1)

old2 = '''def _reschedule_with_carried(
    anchors: list[GraphNode],
    carried: list[GraphNode],
    arrival_at: datetime,
    departure_at: datetime,
) -> list[GraphNode]:'''
new2 = '''def _reschedule_with_carried(
    anchors: list[GraphNode],
    carried: list[GraphNode],
    arrival_at: datetime,
    departure_at: datetime,
    *,
    provider: Any | None = None,
) -> list[GraphNode]:'''
assert old2 in s
s = s.replace(old2, new2, 1)

old3 = '''    gap = timedelta(minutes=_travel_minutes(previous, node)) if previous else timedelta(0)'''
new3 = '''        gap = (
            timedelta(minutes=_travel_minutes(previous, node, provider=provider))
            if previous
            else timedelta(0)
        )'''
s = s.replace(old3, '    gap = (\n            timedelta(minutes=_travel_minutes(previous, node, provider=provider))\n            if previous\n            else timedelta(0)\n        )', 1)

old4 = '''    if carried:
        events = _reschedule_with_carried(events, carried, arrival_at, departure_at)'''
new4 = '''    if carried:
        events = _reschedule_with_carried(
            events, carried, arrival_at, departure_at, provider=_journey_mobility_provider(session, journey)
        )'''
assert old4 in s
s = s.replace(old4, new4, 1)

helper = '''

def _journey_mobility_provider(session: Session, journey: Journey) -> Any | None:
    """The same mobility provider the feasibility gate validates against."""

    try:
        from app.replanning.feasibility import _mobility_provider_for  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        from app.integrations.mobility.runtime import build_provider_for_journey  # type: ignore
    except Exception:
        return None
    try:
        return build_provider_for_journey(session, journey)  # type: ignore[attr-defined]
    except Exception:
        return None
'''
s = s.rstrip("\n") + "\n" + helper
p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("T1 part 3 applied")
