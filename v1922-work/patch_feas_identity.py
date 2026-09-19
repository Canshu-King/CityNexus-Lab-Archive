"""Canonical mobility identity: use metadata.semantic_key across all stages.

``Activity.metadata.semantic_key`` is the stable routing/feasibility identity;
``Activity.place_id`` is only the database Place identity.  Provider mobility
evidence is captured against semantic node keys, so the gate must key on the
same identity at generation, selection, booking, start and replanning.
"""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/replanning/feasibility.py")
s = P.read_text(encoding="utf-8")

old = '''def activity_from_record(item: Any) -> FeasibilityActivity:
    """Adapt an ORM Activity (or compatible mapping) into gate facts."""

    # A persisted Activity UUID is an implementation detail of one
    # PlanVersion.  Feasibility (and especially locked commitments) must use
    # the stable semantic location identity so generation and revalidation
    # evaluate the same candidate.  Services are handled the same way; only
    # activities without a location fall back to their own id/key.
    place_id = _field(item, "place_id")
    city_service_id = _field(item, "city_service_id")
    semantic_key = place_id or city_service_id or _field(item, "activity_key")
    if semantic_key is None:
        semantic_key = _field(item, "id")
    metadata_raw = _field(item, "metadata_json", _field(item, "metadata", {}))
    metadata = _parse_json(metadata_raw, {})
    if not isinstance(metadata, Mapping):
        metadata = {}'''

new = '''def activity_from_record(item: Any) -> FeasibilityActivity:
    """Adapt an ORM Activity (or compatible mapping) into gate facts."""

    # One invariant: ``Activity.metadata.semantic_key`` is the stable routing /
    # feasibility identity and ``Activity.place_id`` is the database Place
    # identity.  Provider mobility evidence is frozen against semantic keys, so
    # the gate must key on exactly the same value at generation, selection,
    # booking, start and replanning - otherwise the persisted snapshot appears
    # to be missing its pairs (MOBILITY_DATA_UNAVAILABLE identity drift).
    place_id = _field(item, "place_id")
    city_service_id = _field(item, "city_service_id")
    metadata_raw = _field(item, "metadata_json", _field(item, "metadata", {}))
    metadata = _parse_json(metadata_raw, {})
    if not isinstance(metadata, Mapping):
        metadata = {}
    routed_key = place_id or city_service_id or _field(item, "activity_key")
    semantic_key = str(metadata.get("semantic_key") or "").strip() or routed_key
    if semantic_key is None:
        semantic_key = _field(item, "id")'''
assert old in s, "activity_from_record not found"
s = s.replace(old, new, 1)

# _location_key must prefer the stable semantic identity for routing lookups.
old2 = '''def _location_key(activity: FeasibilityActivity) -> str | None:
    return activity.place_id or activity.city_service_id or None'''
new2 = '''def _location_key(activity: FeasibilityActivity) -> str | None:
    """Routing identity for one activity.

    Prefer the frozen-evidence semantic key so a persisted plan reloads against
    the exact same mobility facts that produced it; fall back to the concrete
    Place identity for callers that never carried a semantic key.
    """

    metadata = activity.metadata or {}
    if isinstance(metadata, Mapping):
        semantic = str(metadata.get("semantic_key") or "").strip()
        if semantic:
            return semantic
    return activity.place_id or activity.city_service_id or None'''
assert old2 in s, "_location_key not found"
s = s.replace(old2, new2, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("feasibility identity patched")
