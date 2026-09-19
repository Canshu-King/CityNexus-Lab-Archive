"""T1 — a selected stay must AUGMENT the chosen itinerary, never replace it.

``build_candidate_nodes`` builds arrival / stay / departure from scratch and the
materialisation then writes a plan containing only those nodes.  Any real-city
POIs the traveller had already chosen and started simply vanish.

Fix: carry the current selected/active plan's own activities into the stay
graph, between arrival and departure, and only then insert the stay nodes
around them.
"""

from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/app/stay_mobility.py")
s = p.read_text(encoding="utf-8")

old = '''def build_candidate_nodes(
    session: Session, journey: Journey, offer: AccommodationOfferSnapshot
) -> list[GraphNode]:'''

new = '''def _carried_itinerary_nodes(
    session: Session, journey: Journey, *, exclude_keys: set[str]
) -> list[GraphNode]:
    """The traveller's already-chosen stops, as stay-graph nodes.

    A stay selection must *augment* the selected itinerary.  Rebuilding the plan
    from ``city_fixture()`` alone silently deleted every real-city POI the
    traveller had picked (truth blocker T1).  We therefore carry the current
    selected/active plan's own activities forward.

    Only genuinely schedulable stops are carried: the arrival/departure anchors
    are re-created by the stay graph itself, and anything already superseded is
    skipped.
    """

    plan_id = journey.active_plan_version_id
    if not plan_id:
        return []
    rows = session.scalars(
        select(Activity).where(Activity.plan_version_id == plan_id).order_by(Activity.sequence_no)
    ).all()
    carried: list[GraphNode] = []
    for item in rows:
        metadata = _load(item.metadata_json, {}) or {}
        semantic = str(metadata.get("semantic_key") or "").strip()
        role = str(metadata.get("role") or "").upper()
        # Anchors and stay materialisation are rebuilt by this graph.
        if role in {"ARRIVAL", "DEPARTURE"} or item.activity_type in {"arrival", "departure"}:
            continue
        if item.activity_type in {"check_in", "check_out", "stay"}:
            continue
        if semantic and semantic in exclude_keys:
            continue
        key = semantic or str(item.place_id or item.id)
        if key in exclude_keys:
            continue
        if item.latitude is None or item.longitude is None:
            continue
        carried.append(
            GraphNode(
                key=key,
                title=item.title,
                role="ACTIVITY",
                start_at=item.start_at,
                end_at=item.end_at,
                latitude=float(item.latitude),
                longitude=float(item.longitude),
                place_key=item.place_id,
                locked=bool(item.locked),
                estimated_cost_minor=int(item.estimated_cost_minor or 0),
                cost_status=str(metadata.get("cost_status") or "FREE_KNOWN"),
            )
        )
    return carried


def build_candidate_nodes(
    session: Session, journey: Journey, offer: AccommodationOfferSnapshot
) -> list[GraphNode]:'''

assert old in s, "build_candidate_nodes signature not found"
s = s.replace(old, new, 1)

# merge carried activities into the graph before the ordering pass
old2 = '''    ordered = sorted(events, key=lambda node: datetime.fromisoformat(node.start_at))
    result: list[GraphNode] = []
    cursor = arrival_at - timedelta(minutes=1)
    for node in ordered:'''
new2 = '''    # Augment, never replace: keep the traveller's chosen stops.
    carried = _carried_itinerary_nodes(
        session, journey, exclude_keys={str(node.key) for node in events}
    )
    events.extend(carried)
    events.sort(key=lambda node: datetime.fromisoformat(node.start_at))
    ordered = events
    result: list[GraphNode] = []
    cursor = arrival_at - timedelta(minutes=1)
    for node in ordered:'''
assert old2 in s, "ordering block not found"
s = s.replace(old2, new2, 1)

# imports: Activity + select
if "from sqlalchemy import select" not in s:
    s = s.replace("from sqlalchemy.orm import Session", "from sqlalchemy import select\nfrom sqlalchemy.orm import Session", 1)
p.write_text(s, encoding="utf-8", newline="\n")

import ast
ast.parse(s)
print("T1 patch applied")
print("has Activity import:", "Activity" in s.split("def ")[0])
