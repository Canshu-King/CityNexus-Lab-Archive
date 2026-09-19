"""Make confirm_reservation_draft concurrency-safe and identity-consistent."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/operations/v9.py")
s = P.read_text(encoding="utf-8")

old = '''    now = _now()
    price = data.get("price_amount_minor")'''

new = '''    # Quarantine any historical duplicate identity *before* relying on the
    # unique index, so the constraint can be enforced without collapsing two
    # genuinely different bookings.
    quarantine_duplicate_confirmation_identities(session, journey.id)
    session.flush()
    now = _now()
    price = data.get("price_amount_minor")'''
assert old in s, "price marker not found"
s = s.replace(old, new, 1)

s = s.replace(
    "from app.core.audit import record_audit",
    "from app.core.audit import record_audit\n"
    "from app.operations.reservation_identity import (\n"
    "    quarantine_duplicate_confirmation_identities,\n"
    ")",
    1,
)
P.write_text(s, encoding="utf-8", newline="\n")
print("v9 concurrency patched")
