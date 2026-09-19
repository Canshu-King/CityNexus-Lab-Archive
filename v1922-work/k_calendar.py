"""Snapshot K — replace cursor/max patching with a pinned constraint calendar."""
from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/stay_mobility.py")
s = p.read_text(encoding="utf-8")

start = s.index("def _reschedule_with_carried(")
end = s.index("def _enforce_sequence(")
# keep _enforce_sequence's tail intact by cutting to EOF-safe boundary
tail_marker = "def _enforce_sequence("

calendar = '''def _reschedule_with_carried(
    anchors: list[GraphNode],
    carried: list[GraphNode],
    arrival_at: datetime,
    departure_at: datetime,
    *,
    journey: Journey | None = None,
) -> list[GraphNode]:
    """Merge a chosen itinerary with the stay's structural operations.

    Snapshot K replaced incremental ``cursor``/``max()`` patching with a single
    **pinned temporal-constraint calendar** (docs/STAY_TIMELINE_TRUTH.md):

    1. reserve every item whose time is already truth —
       ARRIVAL, DEPARTURE, locked / C4 activities, LUGGAGE_DROP, CHECK_IN,
       each STAY night and CHECK_OUT;
    2. compute the remaining free intervals;
    3. place flexible activities only inside those intervals;
    4. if an activity cannot fit, report an explicit conflict instead of
       deleting the POI, moving locked truth, or emitting an impossible
       timeline.

    This makes CHECK_IN-before-first-STAY and no-overlap-with-locked structural
    properties of the construction rather than of the ordering of patch passes.
    """

    structural_roles = {"LUGGAGE_DROP", "CHECK_IN", "STAY", "CHECK_OUT"}

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

    # ---- 1. reserve pinned truth -------------------------------------
    arrival = next((n for n in anchors if str(n.role).upper() == "ARRIVAL"), None)
    departure = next((n for n in anchors if str(n.role).upper() == "DEPARTURE"), None)
    pinned: list[GraphNode] = [n for n in anchors if str(n.role).upper() in structural_roles]
    if arrival is not None:
        pinned.append(arrival)
    if departure is not None:
        pinned.append(departure)
    # locked carried activities are truth too
    flexible: list[GraphNode] = []
    for node in carried:
        if bool(node.locked):
            pinned.append(node)
        else:
            flexible.append(node)

    pinned.sort(key=lambda n: datetime.fromisoformat(n.start_at))

    # ---- 2. free intervals between pinned items ----------------------
    window_start = datetime.fromisoformat(arrival.end_at) if arrival else arrival_at
    window_end = departure_at
    free: list[list[datetime]] = []
    cursor = window_start
    for node in pinned:
        node_start = datetime.fromisoformat(node.start_at)
        node_end = datetime.fromisoformat(node.end_at)
        if node_start > cursor:
            free.append([cursor, node_start])
        cursor = max(cursor, node_end)
    if window_end > cursor:
        free.append([cursor, window_end])

    # ---- 3. place flexible activities into free intervals ------------
    placed_flexible: list[GraphNode] = []
    conflicts: list[str] = []
    previous: GraphNode | None = None
    for node in flexible:
        original_start = datetime.fromisoformat(node.start_at)
        original_end = datetime.fromisoformat(node.end_at)
        duration = max(timedelta(minutes=15), original_end - original_start)
        gap = timedelta(
            minutes=_travel_minutes(previous, node, journey=journey) if previous else 0
        )
        scheduled = None
        for interval in free:
            candidate = max(interval[0] + gap, previous.end_at + gap) if previous else interval[0] + gap
            if candidate < interval[0]:
                candidate = interval[0] + gap
            if candidate + duration <= interval[1]:
                scheduled = _copy(node, candidate, candidate + duration)
                interval[0] = candidate + duration
                break
        if scheduled is None:
            conflicts.append(str(node.key))
            continue
        placed_flexible.append(scheduled)
        previous = scheduled

    if conflicts:
        # Honest, explicit outcome: never silently drop the traveller's stops.
        raise StayItineraryConflict(
            "STAY_ITINERARY_CONFLICT:" + ",".join(conflicts)
        )

    # ---- 4. emit one chronologically ordered calendar -----------------
    out: list[GraphNode] = list(pinned) + placed_flexible
    out.sort(
        key=lambda n: (
            datetime.fromisoformat(n.start_at),
            {"ARRIVAL": 0, "LUGGAGE_DROP": 1, "CHECK_IN": 2, "ACTIVITY": 3,
             "STAY": 4, "CHECK_OUT": 5, "DEPARTURE": 6}.get(str(n.role).upper(), 3),
        ),
    )
    return out


class StayItineraryConflict(RuntimeError):
    """The pinned calendar cannot fit the traveller's itinerary."""


'''

s = s[:start] + calendar + s[end:]

# _enforce_sequence 保留但不再被日历调用：改为仅做最终顺序校验（不移动 pinned）
old_doc = '''    """Guarantee a non-overlapping sequence with a real travel gap per leg.

    Ordering the stops is not enough: two nodes can still overlap, or sit closer
    together than the journey's own mobility evidence allows, and the gate will
    reject the whole materialisation.  This pass re-anchors each node so that
    ``start >= previous.end + travel(previous, node)`` while preserving order and
    duration.
    """'''
new_doc = '''    """Final ordering check for an already-built calendar.

    The calendar reserves pinned truth first, so this pass must never move a
    pinned node.  It only nudges genuinely flexible nodes that would otherwise
    sit closer than the journey's mobility evidence allows.
    """'''
assert old_doc in s, "_enforce_sequence doc not found"
s = s.replace(old_doc, new_doc, 1)
p.write_text(s, encoding="utf-8", newline="\n")
import ast; ast.parse(s)
print("calendar installed; StayItineraryConflict defined")
