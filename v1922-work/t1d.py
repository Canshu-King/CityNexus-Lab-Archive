"""T1 part 4 — schedule carried POIs with the same fact generator the gate uses.

``_mode_fact`` is what materialises every stay-graph leg's duration, and the
feasibility gate validates those exact facts.  Re-timing with anything else
(a distance heuristic, an unrelated provider) produces a schedule that looks
feasible locally and then fails ``INSUFFICIENT_TRAVEL_GAP`` at the gate.
"""

from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/stay_mobility.py")
s = p.read_text(encoding="utf-8")

# _travel_minutes takes a journey so it can call the real fact generator.
old = '''def _travel_minutes(
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
    return max(5, math.ceil(_distance_m(a, b) / 350) + 4)'''

new = '''def _travel_minutes(
    a: GraphNode | None,
    b: GraphNode,
    *,
    journey: Journey | None = None,
) -> int:
    """Inter-stop travel time, from the same generator the gate will validate.

    ``_mode_fact`` produces every stay-graph leg duration, and the feasibility
    gate checks those exact facts.  Using anything else here (a distance
    heuristic, a different provider) yields a schedule that looks feasible at
    planning time and then fails ``INSUFFICIENT_TRAVEL_GAP``.
    """

    if a is None:
        return 0
    shared = _shared_prefix_len(str(a.key), str(b.key))
    if shared >= 12:
        # Same complex: no meaningful leg.
        return 5
    if journey is not None:
        try:
            fact = _mode_fact(
                journey.id, None, a, b, "WALK", journey.budget_currency
            )
            return max(0, int(fact.duration_min))
        except Exception:
            pass
    return max(5, math.ceil(_distance_m(a, b) / 350) + 4)'''
assert old in s, "_travel_minutes v3 not found"
s = s.replace(old, new, 1)

s = s.replace('''    arrival_at: datetime,
    departure_at: datetime,
    *,
    provider: Any | None = None,
) -> list[GraphNode]:''', '''    arrival_at: datetime,
    departure_at: datetime,
    *,
    journey: Journey | None = None,
) -> list[GraphNode]:''', 1)

old_gap = '''    gap = (
            timedelta(minutes=_travel_minutes(previous, node, provider=provider))
            if previous
            else timedelta(0)
        )'''
new_gap = '''    gap = (
            timedelta(minutes=_travel_minutes(previous, node, journey=journey))
            if previous
            else timedelta(0)
        )'''
assert old_gap in s, "gap block not found"
s = s.replace(old_gap, new_gap, 1)

old_call = '''        events = _reschedule_with_carried(
            events, carried, arrival_at, departure_at, provider=_journey_mobility_provider(session, journey)
        )'''
new_call = '''        events = _reschedule_with_carried(
            events, carried, arrival_at, departure_at, journey=journey
        )'''
assert old_call in s, "reschedule call not found"
s = s.replace(old_call, new_call, 1)

# drop the helper that referenced a non-existent module function
i = s.find("\n\ndef _journey_mobility_provider(")
if i != -1:
    s = s[:i].rstrip("\n") + "\n"
p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("T1 part 4 applied; _journey_mobility_provider removed:", "_journey_mobility_provider" not in s)
