"""A C4 anchor role that is absent is NOT an ARRIVAL anchor.

Two different C4 commitment shapes exist:

* reservation anchors - carry ``anchor_role`` (ARRIVAL / DEPARTURE / MID_TRIP)
* booking/order anchors - promote a concrete Activity; they carry
  ``semantic_key`` + ``scheduled_start_at`` but **no** ``anchor_role``

Only the first shape is rewritten to a structural planner node.  Treating the
second as ARRIVAL corrupted every booking-protected activity.
"""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/planning/anchors.py")
s = P.read_text(encoding="utf-8")

old = '''def normalise_role(value: Any) -> str:
    role = str(value or ARRIVAL_ROLE).upper().strip()
    return role if role in ANCHOR_ROLES else ARRIVAL_ROLE


def time_boundary_for(role: str) -> str:
    """A departure anchor constrains the END of its activity, an arrival the START."""

    return "END" if normalise_role(role) == DEPARTURE_ROLE else "START"'''
new = '''def normalise_role(value: Any) -> str:
    """Normalise a reservation anchor role.

    An explicit, recognised role is returned as-is.  Anything else returns
    ``""`` - notably a booking/order commitment, which has no reservation role
    and must never be treated as an ARRIVAL anchor.
    """

    role = str(value or "").upper().strip()
    return role if role in ANCHOR_ROLES else ""


def is_reservation_anchor(policy: Mapping[str, Any]) -> bool:
    """True when this C4 policy is a reservation anchor (not a booking anchor)."""

    return bool(normalise_role(policy.get("anchor_role")))


def time_boundary_for(role: str) -> str:
    """A departure anchor constrains the END of its activity, an arrival the START."""

    return "END" if normalise_role(role) == DEPARTURE_ROLE else "START"'''
assert old in s, "normalise_role not found"
s = s.replace(old, new, 1)

old2 = '''    role = normalise_role(policy.get("anchor_role"))
    semantic_key = str(policy.get("semantic_key") or "").strip()
    if not semantic_key:
        semantic_key = str(policy.get("semantic_node_key") or "").strip()
    if role in (ARRIVAL_ROLE, DEPARTURE_ROLE):'''
new2 = '''    role = normalise_role(policy.get("anchor_role"))
    semantic_key = str(policy.get("semantic_key") or "").strip()
    if not semantic_key:
        semantic_key = str(policy.get("semantic_node_key") or "").strip()
    if role in (ARRIVAL_ROLE, DEPARTURE_ROLE) and journey_id:'''
assert old2 in s, "identity role branch not found"
s = s.replace(old2, new2, 1)

old3 = '''    structural_place_id,
)'''
new3 = '''    is_reservation_anchor,
    structural_place_id,
)'''
if old3 in s:
    s = s.replace(old3, new3, 1)

s = s.replace('''__all__ = [
    "anchor_identity_from_policy",''', '''__all__ = [
    "anchor_identity_from_policy",
    "is_reservation_anchor",''', 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
