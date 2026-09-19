"""_location_key must tolerate callers whose activity has no metadata field."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/replanning/feasibility.py")
s = P.read_text(encoding="utf-8")

old = '''    metadata = activity.metadata or {}
    if isinstance(metadata, Mapping):
        semantic = str(metadata.get("semantic_key") or "").strip()
        if semantic:
            return semantic
    return activity.place_id or activity.city_service_id or None'''
new = '''    metadata = getattr(activity, "metadata", None) or {}
    if isinstance(metadata, Mapping):
        semantic = str(metadata.get("semantic_key") or "").strip()
        if semantic:
            return semantic
    return activity.place_id or activity.city_service_id or None'''
assert old in s
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
