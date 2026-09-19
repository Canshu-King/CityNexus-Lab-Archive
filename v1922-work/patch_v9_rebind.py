"""Remove the temporary mobility rebind hack.

Provider mobility evidence is frozen against semantic node keys, and
``Activity.metadata.semantic_key`` now carries that same identity.  The V19.2.1
rebind existed only because the gate keyed on concrete Place ids; with one
canonical identity the persisted evidence is already exactly what the gate
needs, so the translation layer is deleted rather than extended.
"""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/operations/v9.py")
s = P.read_text(encoding="utf-8")

old = '''    # Validate against the exact mobility evidence just materialized; a
    # downstream runtime recapture would create split-brain truth.
    # The V9 graph stores semantic node keys in provider facts while the
    # materialized Activity rows use concrete Place ids. Rebind the same
    # frozen fact values to those concrete ids for the shared gate; do not
    # recapture a new provider snapshot.
    rebound = {}
    for index, fact in enumerate(facts):
        if index + 1 < len(activities):
            rebound[(activities[index].place_id, activities[index + 1].place_id)] = TravelEstimateFact(
                origin_key=activities[index].place_id,
                destination_key=activities[index + 1].place_id,
                minutes=fact.duration_min,
                provider_key=fact.provider_key,
                captured_at=fact.captured_at,
                degraded=False,
                distance_m=fact.distance_m,
                walking_min=fact.walking_min,
            )
    gate_snapshot = MobilitySnapshot(
        facts=rebound,
        source_provider_key=str(mobility_evidence.get("source_provider") or "v9"),
        captured_at=str(mobility_evidence.get("captured_at") or _now()),
        snapshot_id=mobility_snapshot_id,
    )'''

new = '''    # Validate against the exact mobility evidence just materialized; a
    # downstream runtime recapture would create split-brain truth.
    #
    # One canonical identity is used end to end:
    #     Activity.metadata.semantic_key  -> routing / frozen-evidence identity
    #     Activity.place_id               -> database Place identity
    # The stored bundle is already keyed by those semantic node keys, so it is
    # consumed directly.  There is deliberately no identity rebinding here.
    gate_snapshot = MobilitySnapshot.from_evidence(mobility_evidence)'''
assert old in s, "v9 rebind block not found"
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("v9 rebind removed")
