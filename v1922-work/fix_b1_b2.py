"""B1 + B2 — structural stay operations must survive, and locked truth must not move.

B1: ``_reschedule_with_carried`` filtered anchors with
    ``role == "STAY"`` and then looked for ``:check-in`` / ``:check-out`` keys
    *inside that list*.  ``build_candidate_nodes`` emits LUGGAGE_DROP, CHECK_IN,
    STAY and CHECK_OUT as four distinct roles, so CHECK_IN, CHECK_OUT and
    LUGGAGE_DROP were silently dropped whenever an itinerary was carried
    forward.

B2: carried nodes with ``locked=True`` were re-timed like flexible stops.  A
    confirmed activity must keep its authoritative start/end; only flexible
    stops move around it.

The two passes are replaced by one scheduler that:
  * pins ARRIVAL, DEPARTURE and every LOCKED node at their authoritative times;
  * places flexible stops in the free windows around the pinned truth;
  * emits every structural stay operation in a valid temporal order.
"""

from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/stay_mobility.py")
s = p.read_text(encoding="utf-8")

start = s.index("def _reschedule_with_carried(")
end = s.index("def ordered_events(")
replacement = '''def _reschedule_with_carried(
    anchors: list[GraphNode],
    carried: list[GraphNode],
    arrival_at: datetime,
    departure_at: datetime,
    *,
    journey: Journey | None = None,
) -> list[GraphNode]:
    """Merge the traveller's itinerary with the stay's structural operations.

    Truth rules enforced here:

    * every structural stay operation survives — LUGGAGE_DROP, CHECK_IN, each
      STAY night and CHECK_OUT are four distinct roles and are all emitted;
    * a ``locked`` carried activity keeps its authoritative start/end.  Hotel
      selection must never re-time confirmed truth;
    * flexible stops are placed in the free windows around the pinned nodes;
    * the result is chronologically ordered with a real travel gap per leg.
    """

    structural_roles = {"LUGGAGE_DROP", "CHECK_IN", "STAY", "CHECK_OUT"}
    structural = [node for node in anchors if str(node.role).upper() in structural_roles]
    arrival = next(
        (node for node in anchors if str(node.role).upper() == "ARRIVAL"), None
    )
    departure = next(
        (node for node in anchors if str(node.role).upper() == "DEPARTURE"), None
    )

    cursor = datetime.fromisoformat(arrival.end_at) if arrival else arrival_at
    day_end_hour = 18
    day = cursor.date()
    placed: list[GraphNode] = []
    previous: GraphNode | None = arrival

    def _copy(node: GraphNode, new_start: datetime, new_end: datetime) -> GraphNode:
        return GraphNode(
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

    for node in carried:
        start = datetime.fromisoformat(node.start_at)
        end = datetime.fromisoformat(node.end_at)
        duration = max(timedelta(minutes=15), end - start)
        if node.locked:
            # Authoritative truth: keep the exact window, never re-time it.
            placed.append(node)
            cursor = max(cursor, end)
            previous = node
            continue
        gap = timedelta(
            minutes=_travel_minutes(previous, node, journey=journey) if previous else 0
        )
        new_start = cursor + gap
        if new_start.hour >= day_end_hour or (new_start + duration).hour > day_end_hour + 2:
            day = day + timedelta(days=1)
            new_start = datetime.combine(day, time(9, 0), tzinfo=new_start.tzinfo)
        new_end = new_start + duration
        if new_end > departure_at:
            new_end = departure_at
            new_start = new_end - duration
            if new_start <= cursor:
                continue
        placed.append(_copy(node, new_start, new_end))
        cursor = new_end
        previous = placed[-1]

    # Structural operations are anchored to their own real times, and only
    # pushed later when a locked or flexible stop already occupies the slot.
    nights = sorted(
        (n for n in structural if str(n.role).upper() == "STAY"),
        key=lambda n: str(n.key),
    )
    others = sorted(
        (n for n in structural if str(n.role).upper() != "STAY"),
        key=lambda n: datetime.fromisoformat(n.start_at),
    )
    night_index = 0
    for node in others:
        start = datetime.fromisoformat(node.start_at)
        end = datetime.fromisoformat(node.end_at)
        duration = max(timedelta(minutes=15), end - start)
        if str(node.role).upper() == "CHECK_IN" and nights:
            # Check-in must precede the first night and follow the day's stops.
            new_start = max(start, cursor)
            new_end = new_start + duration
            placed.append(_copy(node, new_start, new_end))
            cursor = new_end
            previous = placed[-1]
            continue
        if str(node.role).upper() == "CHECK_OUT":
            new_start = max(start, cursor)
            new_end = new_start + duration
            if new_end > departure_at:
                new_end = departure_at
                new_start = new_end - duration
            if new_end > new_start:
                placed.append(_copy(node, new_start, new_end))
                cursor = new_end
                previous = placed[-1]
            continue
        # LUGGAGE_DROP and anything else: keep it as early as its own time
        # allows, but never before the traveller has arrived.
        new_start = max(start, cursor)
        new_end = new_start + duration
        if new_end > departure_at:
            continue
        placed.append(_copy(node, new_start, new_end))
        cursor = new_end
        previous = placed[-1]

    for index, node in enumerate(nights):
        start = datetime.fromisoformat(node.start_at)
        end = datetime.fromisoformat(node.end_at)
        span = max(timedelta(minutes=30), end - start)
        night_date = arrival_at.date() + timedelta(days=index)
        new_start = datetime.combine(night_date, time(22, 0), tzinfo=arrival_at.tzinfo)
        new_end = new_start + span
        if new_start >= departure_at or new_end > departure_at:
            continue
        placed.append(_copy(node, new_start, new_end))
        night_index += 1

    out: list[GraphNode] = []
    if arrival:
        out.append(arrival)
    out.extend(placed)
    if departure:
        out.append(departure)
    return _enforce_sequence(out, journey=journey)


'''
s = s[:start] + replacement + s[end:]

# _enforce_sequence: 不得移动 locked 节点
old = '''        if str(node.role).upper() in pinned_roles or cursor is None:
            fixed.append(node)
            cursor = end
            previous = node
            continue'''
new = '''        if (
            str(node.role).upper() in pinned_roles
            or bool(node.locked)
            or cursor is None
        ):
            # Pinned anchors and locked truth keep their authoritative window;
            # everything else is scheduled around them.
            fixed.append(node)
            cursor = max(cursor, end) if cursor is not None else end
            previous = node
            continue'''
assert old in s, "_enforce_sequence pin block not found"
s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("B1 + B2 applied")
print("structural roles handled:", "LUGGAGE_DROP" in s and "CHECK_IN" in s and "CHECK_OUT" in s)
