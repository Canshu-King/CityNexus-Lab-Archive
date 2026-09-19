"""P1 walking evidence scope.

``MAX_WALKING_PER_LEG_M`` / ``MAX_DAILY_WALKING_M`` must only consume real
walking distance:

* ``WALK`` mode: ``distance_m`` may legitimately represent walking distance.
* ``TRANSIT`` / ``CAR`` / ``BIKE`` / other motorised modes: require an explicit
  ``walking_distance_m``.  A total route distance must never be silently
  reinterpreted as walking distance - that would under-report walking.
"""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/replanning/feasibility.py")
s = P.read_text(encoding="utf-8")

old = '''            fact = facts.get((origin, destination)) if isinstance(facts, Mapping) else None
            if fact is not None:
                distance = getattr(fact, "walking_distance_m", None)
                if distance is None:
                    distance = getattr(fact, "distance_m", None)
                walking_min = getattr(fact, "walking_min", None)
                if walking_min is None and getattr(fact, "mode", None) == "WALK":
                    walking_min = getattr(fact, "minutes", None)
                if distance is not None or walking_min is not None:
                    return (
                        int(distance) if distance is not None else None,
                        int(walking_min) if walking_min is not None else None,
                        pair,
                    )'''

new = '''            fact = facts.get((origin, destination)) if isinstance(facts, Mapping) else None
            if fact is not None:
                # Walking distance has one definition: explicit walking evidence,
                # or (for a genuine WALK leg only) the leg distance itself.  A
                # total route distance on a motorised leg is never walking.
                mode = str(getattr(fact, "mode", "") or "").upper()
                distance = getattr(fact, "walking_distance_m", None)
                if distance is None and mode == "WALK":
                    distance = getattr(fact, "distance_m", None)
                walking_min = getattr(fact, "walking_min", None)
                if walking_min is None and mode == "WALK":
                    walking_min = getattr(fact, "minutes", None)
                if distance is not None or walking_min is not None:
                    return (
                        int(distance) if distance is not None else None,
                        int(walking_min) if walking_min is not None else None,
                        pair,
                    )'''
assert old in s, "walking fact block not found"
s = s.replace(old, new, 1)

old2 = '''    metadata = current.metadata or {}
    distance = current.walking_distance_m
    if distance is None and isinstance(metadata, Mapping):
        distance = metadata.get("walking_distance_m", metadata.get("distance_m"))
    walking_min = current.walking_min
    if walking_min is None and isinstance(metadata, Mapping):
        walking_min = metadata.get("walking_min")'''
new2 = '''    metadata = current.metadata or {}
    distance = current.walking_distance_m
    if distance is None and isinstance(metadata, Mapping):
        # Only an explicit walking distance counts here.  ``distance_m`` is a
        # total route length and must not be promoted to a walking budget.
        distance = metadata.get("walking_distance_m")
    walking_min = current.walking_min
    if walking_min is None and isinstance(metadata, Mapping):
        walking_min = metadata.get("walking_min")'''
assert old2 in s, "metadata walking block not found"
s = s.replace(old2, new2, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("walking scope patched")
