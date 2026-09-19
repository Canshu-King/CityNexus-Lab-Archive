"""Add _safe_estimate_minutes and _anchor_block_reason to services.py."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/services.py")
s = P.read_text(encoding="utf-8")

helpers = '''

def _safe_estimate_minutes(provider, origin: str | None, destination: str | None) -> int:
    """Frozen-provider lookup that never raises for an unknown pair.

    A missing pair is a real planning fact (``MOBILITY_DATA_UNAVAILABLE`` in the
    gate), not a reason to abort the whole generation loop.
    """

    if not origin or not destination:
        return 0
    try:
        return int(provider.estimate_minutes(origin, destination))
    except (KeyError, TypeError, ValueError):
        return 0


def _anchor_block_reason(session: Session, journey: Journey) -> str:
    """Name the C4 anchor that blocked generation, when there is one.

    ``select`` already returns an accurate ``LOCKED_COMMITMENT_LOST:<key>``;
    ``generate`` must not collapse that into an anonymous sentence.
    """

    try:
        anchors, unresolved = resolve_plan_anchors(session, journey)
    except Exception:  # noqa: BLE001 - reason text must never break generation
        return ""
    if unresolved:
        return ": C4_ANCHOR_UNRESOLVED:" + ",".join(sorted(set(unresolved)))
    if anchors:
        keys = ", ".join(sorted({anchor.semantic_key for anchor in anchors}))
        return f": C4_ANCHOR_BLOCKED:{keys}"
    return ""
'''

marker = "def _generic_compose_plans("
assert marker in s
s = s.replace(marker, helpers.strip("\n") + "\n\n\n" + marker, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("helpers added")
