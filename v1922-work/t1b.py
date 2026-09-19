"""T1 part 2 — re-schedule the carried POIs onto the stay timeline.

Carrying the traveller's POIs forward is necessary but not sufficient: keeping
their *stale* times collides with the stay nodes and the gate correctly rejects
the plan (INSUFFICIENT_TRAVEL_GAP).  The stay graph therefore re-times the
carried stops as a real sequence starting at the arrival anchor, with a genuine
travel gap between consecutive stops, and only then places check-in / nights /
check-out / departure around them.
"""

from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/stay_mobility.py")
s = p.read_text(encoding="utf-8")

old = '''    # Augment, never replace: keep the traveller's chosen stops.
    carried = _carried_itinerary_nodes(
        session, journey, exclude_keys={str(node.key) for node in events}
    )
    events.extend(carried)
    events.sort(key=lambda node: datetime.fromisoformat(node.start_at))
    ordered = events
    result: list[GraphNode] = []
    cursor = arrival_at - timedelta(minutes=1)
    for node in ordered:
        start = datetime.fromisoformat(node.start_at)
        end = datetime.fromisoformat(node.end_at)
        if start < cursor and node.role not in {"STAY"}:
            continue
        result.append(node)
        cursor = max(cursor, end)
    return result'''

new = '''    # Augment, never replace: keep the traveller's chosen stops.
    carried = _carried_itinerary_nodes(
        session, journey, exclude_keys={str(node.key) for node in events}
    )
    if carried:
        events = _reschedule_with_carried(events, carried, arrival_at, departure_at)
    events.sort(key=lambda node: datetime.fromisoformat(node.start_at))
    result: list[GraphNode] = []
    cursor = arrival_at - timedelta(minutes=1)
    for node in ordered_events(events):
        start = datetime.fromisoformat(node.start_at)
        end = datetime.fromisoformat(node.end_at)
        if start < cursor and node.role not in {"STAY", "ACTIVITY"}:
            continue
        result.append(node)
        cursor = max(cursor, end)
    return result


def ordered_events(events: list[GraphNode]) -> list[GraphNode]:
    """Stable temporal order: anchors keep their slot, everything else follows."""

    role_rank = {"ARRIVAL": 0, "ACTIVITY": 1, "STAY": 2, "DEPARTURE": 3}
    return sorted(
        events,
        key=lambda node: (
            datetime.fromisoformat(node.start_at),
            role_rank.get(str(node.role).upper(), 2),
        ),
    )


def _reschedule_with_carried(
    anchors: list[GraphNode],
    carried: list[GraphNode],
    arrival_at: datetime,
    departure_at: datetime,
) -> list[GraphNode]:
    """Re-time the carried stops into a feasible sequence after arrival.

    The traveller's chosen stops keep their relative order, their own duration
    and get a real travel gap between them.  The stay nodes are then re-anchored
    so check-in follows the last stop instead of colliding with it.
    """

    by_role = {str(node.role).upper(): node for node in anchors}
    arrival = by_role.get("ARRIVAL")
    departure = by_role.get("DEPARTURE")
    stays = [node for node in anchors if str(node.role).upper() == "STAY"]

    cursor = datetime.fromisoformat(arrival.end_at) if arrival else arrival_at
    scheduled: list[GraphNode] = []
    previous: GraphNode | None = arrival
    for node in carried:
        start = datetime.fromisoformat(node.start_at)
        end = datetime.fromisoformat(node.end_at)
        duration = max(timedelta(minutes=15), end - start)
        gap = timedelta(minutes=_travel_minutes(previous, node)) if previous else timedelta(0)
        new_start = cursor + gap
        new_end = new_start + duration
        # Never run past the departure anchor.
        if new_end > departure_at:
            new_end = departure_at
            new_start = new_end - duration
            if new_start <= cursor:
                # No room left: the gate will judge the reduced stop set.
                continue
        scheduled.append(
            GraphNode(
                key=node.key,
                title=node.title,
                role=node.role,
                start_at=new_start.isoformat(),
                end_at=new_end.isoformat(),
                latitude=node.latitude,
                longitude=node.longitude,
                place_key=node.place_key,
                locked=node.locked,
                estimated_cost_minor=node.estimated_cost_minor,
                cost_status=node.cost_status,
            )
        )
        cursor = new_end
        previous = scheduled[-1]

    last_activity_end = cursor
    new_stays: list[GraphNode] = []
    stay_cursor = last_activity_end
    for node in stays:
        start = datetime.fromisoformat(node.start_at)
        end = datetime.fromisoformat(node.end_at)
        duration = max(timedelta(minutes=30), end - start)
        new_start = max(start, stay_cursor)
        new_end = new_start + duration
        if new_end > departure_at:
            continue
        new_stays.append(
            GraphNode(
                key=node.key,
                title=node.title,
                role=node.role,
                start_at=new_start.isoformat(),
                end_at=new_end.isoformat(),
                latitude=node.latitude,
                longitude=node.longitude,
                place_key=node.place_key,
                locked=node.locked,
                estimated_cost_minor=node.estimated_cost_minor,
                cost_status=node.cost_status,
            )
        )
        stay_cursor = new_end

    out: list[GraphNode] = []
    if arrival:
        out.append(arrival)
    out.extend(scheduled)
    out.extend(new_stays)
    if departure:
        out.append(departure)
    return out


def _travel_minutes(a: GraphNode | None, b: GraphNode) -> int:
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

assert old in s, "carried merge block not found"
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8", newline="\n")
import ast; ast.parse(s)
print("T1 part 2 applied")
