"""Only rewrite *reservation* anchors to structural planner nodes."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/replanning/protected_commitments.py")
s = P.read_text(encoding="utf-8")

old = '''        role = normalise_role(policy.get("anchor_role"))
        raw_key = str(policy.get("semantic_key") or "").strip()
        legacy_key = str(policy.get("semantic_node_key") or "").strip()
        semantic_key = raw_key or legacy_key

        # ARRIVAL / DEPARTURE always resolve to the structural planner Place
        # identity, even when an earlier release persisted an unsatisfiable
        # synthetic UUID or a bare structural placeholder.
        if role in STRUCTURAL_ANCHOR_KEYS:
            journey_id = str(getattr(item, "journey_id", "") or "")
            semantic_key = (
                structural_place_id(journey_id, role) if journey_id else STRUCTURAL_ANCHOR_KEYS[role]
            )

        if not semantic_key:'''
new = '''        role = normalise_role(policy.get("anchor_role"))
        raw_key = str(policy.get("semantic_key") or "").strip()
        legacy_key = str(policy.get("semantic_node_key") or "").strip()
        semantic_key = raw_key or legacy_key

        # ARRIVAL / DEPARTURE *reservation* anchors always resolve to the
        # structural planner Place identity, even when an earlier release
        # persisted an unsatisfiable synthetic UUID or a bare placeholder.
        # A booking/order C4 anchor has no anchor_role and keeps its own
        # activity-anchored semantic_key untouched.
        if role in STRUCTURAL_ANCHOR_KEYS:
            journey_id = str(getattr(item, "journey_id", "") or "")
            semantic_key = (
                structural_place_id(journey_id, role) if journey_id else STRUCTURAL_ANCHOR_KEYS[role]
            )

        if not semantic_key:'''
assert old in s, "role branch not found"
s = s.replace(old, new, 1)

old2 = '''        if not semantic_key:
            constraints.append(
                {
                    "kind": "HARD",
                    "category": "commitment",
                    "rule_code": "UNRESOLVED_COMMITMENT_ANCHOR",'''
new2 = '''        if not semantic_key:
            if not role:
                # A booking/order anchor with no readable identity is not a
                # reservation anchor; leave it to the existing activity_id
                # protection path rather than inventing an unresolved anchor.
                continue
            constraints.append(
                {
                    "kind": "HARD",
                    "category": "commitment",
                    "rule_code": "UNRESOLVED_COMMITMENT_ANCHOR",'''
assert old2 in s, "unresolved branch not found"
s = s.replace(old2, new2, 1)

# A booking anchor without an explicit time is satisfied by its activity_id.
old3 = '''        scheduled_start = policy.get("scheduled_start_at")
        if not scheduled_start:
            raise ValueError("C4 commitment lacks a stable time anchor")'''
new3 = '''        scheduled_start = policy.get("scheduled_start_at")
        if not scheduled_start:
            if not normalise_role(policy.get("anchor_role")):
                # Booking/order anchors are bound to a concrete Activity, not a
                # relative schedule; they are protected through activity_id.
                continue
            raise ValueError("C4 commitment lacks a stable time anchor")'''
assert old3 in s, "scheduled_start branch not found"
s = s.replace(old3, new3, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
