from pathlib import Path

p = Path("D:/moodle/CityNexus/backend/db/schema.sql")
s = p.read_text(encoding="utf-8")

old = '''CREATE UNIQUE INDEX IF NOT EXISTS uq_transport_reservations_journey_confirmation
    ON transport_reservations(journey_id, confirmation_ref);'''
new = '''-- Authoritative reservation identity.
--
-- Partial index: only rows that still *claim* a confirmation reference are
-- constrained.  Quarantined historical duplicates are moved to
-- status = 'QUARANTINED_DUPLICATE_IDENTITY' and have their draft pointer
-- released, so they are excluded from the constraint while their evidence and
-- audit trail are preserved intact.  A plain unique index over
-- (journey_id, confirmation_ref) cannot be created while duplicate rows exist;
-- this is what makes the rule actually enforceable.
CREATE UNIQUE INDEX IF NOT EXISTS uq_transport_reservations_journey_confirmation
    ON transport_reservations(journey_id, confirmation_ref)
    WHERE confirmation_ref IS NOT NULL
      AND status <> 'QUARANTINED_DUPLICATE_IDENTITY';'''
assert old in s, "unique index not found in schema.sql"
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("schema.sql 改为部分唯一索引")
