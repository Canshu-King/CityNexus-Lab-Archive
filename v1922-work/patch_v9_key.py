"""V9 materialization must use the canonical structural anchor identity.

The V9 stay graph names the structural nodes ``arrival-anchor`` /
``departure-anchor``.  Those are planner-local aliases; the canonical identity
is the ``v12:{journey_id}:{key}`` Place id that the authoritative planner,
C4 commitments and the shared gate all agree on.
"""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/operations/v9.py")
s = P.read_text(encoding="utf-8")

old = '''    for index, node in enumerate(nodes, start=1):
        place = _place_for_node(session, journey, node)'''
new = '''    for index, node in enumerate(nodes, start=1):
        place = _place_for_node(session, journey, node)
        # Canonical structural identity, shared with the authoritative planner,
        # the C4 commitment policy and the frozen mobility evidence.
        semantic_identity = _canonical_node_semantic_key(journey, node)'''
assert old in s, "node loop not found"
s = s.replace(old, new, 1)

old2 = '''            metadata_json=_json(
                {
                    "semantic_key": node.key,'''
new2 = '''            metadata_json=_json(
                {
                    "semantic_key": semantic_identity,'''
assert old2 in s, "metadata block not found"
s = s.replace(old2, new2, 1)

helpers = '''

_STRUCTURAL_NODE_KEYS = {"arrival-anchor": "ARRIVAL", "departure-anchor": "DEPARTURE"}


def _canonical_node_semantic_key(journey: Journey, node: Any) -> str:
    """One stable semantic identity for a V9 structural node.

    ``arrival-anchor`` / ``departure-anchor`` are planner-local aliases; the
    canonical identity is the ``v12:{journey_id}:{key}`` Place id used by the
    authoritative planner, C4 commitments and the shared feasibility gate.
    """

    key = str(getattr(node, "key", "") or "")
    if key in _STRUCTURAL_NODE_KEYS:
        return f"v12:{journey.id}:{key}"
    return key
'''
s = s.replace('\n\ndef _place_for_node(', helpers + '\n\ndef _place_for_node(', 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("v9 canonical key patched")
