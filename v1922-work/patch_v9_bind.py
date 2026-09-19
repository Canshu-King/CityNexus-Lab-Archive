"""Bind C4 commitments to the canonical structural activity."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/operations/v9.py")
s = P.read_text(encoding="utf-8")

old = '''    active_commitments = session.scalars(
        select(Commitment).where(
            Commitment.journey_id == journey.id,
            Commitment.status == "ACTIVE",
        )
    ).all()
    by_semantic = {_load(item.metadata_json, {}).get("semantic_key"): item for item in activities}
    for commitment in active_commitments:
        policy = _load(commitment.policy_json, {})
        semantic = policy.get("semantic_node_key")
        if semantic and semantic in by_semantic:
            commitment.activity_id = by_semantic[semantic].id
            policy["semantic_key"] = by_semantic[semantic].place_id
            commitment.policy_json = _json(policy)
            commitment.updated_at = _now()'''

new = '''    active_commitments = session.scalars(
        select(Commitment).where(
            Commitment.journey_id == journey.id,
            Commitment.status == "ACTIVE",
        )
    ).all()
    by_semantic = {
        str(_load(item.metadata_json, {}).get("semantic_key") or ""): item
        for item in activities
    }
    by_place = {item.place_id: item for item in activities}
    for commitment in active_commitments:
        policy = _load(commitment.policy_json, {})
        role = str(policy.get("anchor_role") or "").upper()
        # Reservation anchors resolve to their canonical structural node; a
        # booking/order anchor keeps its own activity-anchored identity.
        if role in {"ARRIVAL", "DEPARTURE"}:
            candidate_key = f"v12:{journey.id}:{role.lower()}-anchor"
        else:
            candidate_key = str(policy.get("semantic_key") or policy.get("semantic_node_key") or "")
        activity = by_semantic.get(candidate_key) or by_place.get(candidate_key)
        if activity is not None:
            commitment.activity_id = activity.id
            if role in {"ARRIVAL", "DEPARTURE"}:
                policy["semantic_key"] = candidate_key
            commitment.policy_json = _json(policy)
            commitment.updated_at = _now()'''
assert old in s, "commitment binding block not found"
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
