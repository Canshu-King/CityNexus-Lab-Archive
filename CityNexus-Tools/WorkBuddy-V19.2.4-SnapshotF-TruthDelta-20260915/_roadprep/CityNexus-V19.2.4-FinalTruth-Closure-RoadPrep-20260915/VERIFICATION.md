# Independent verification performed before this Road-Prep

## Snapshot F shared feasibility gate

Against the submitted final V19.2.3 source with a frozen deterministic
MobilitySnapshot:

```text
prearrival:
  passed = false?  NO
  actual passed = true
  failures = []

postdeparture:
  actual passed = true
  failures = []

arrival_after_departure:
  actual passed = true
  failures = []
```

This is the primary P0.

## Verified starter fix behaviour

The included starter patch was applied in an isolated copy of Snapshot F.

After the patch:

```text
prearrival
-> passed=false
-> C4_ACTIVITY_BEFORE_ARRIVAL:p

postdeparture
-> passed=false
-> C4_ACTIVITY_AFTER_DEPARTURE:p

arrival_after_departure
-> passed=false
-> C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE

valid control
-> passed=true
-> failures=[]
```

## Recovery probe

Before starter fix:

```text
Event.status = DETECTED
recovery_state(is_feasible=True).state = RESOLVED
recovery_flags.recovery_required = true
```

After starter fix:

```text
Event.status = DETECTED
recovery_state(is_feasible=True).state = RECOVERY_REQUIRED
recovery_flags.recovery_required = true
projection disagreement = none
unvalidated candidate count = 0
```

## Reservation helper

Snapshot F helper on a purpose-built duplicate DB:

```text
IntegrityError:
CHECK constraint failed: event_type IN (...)
```

After starter fix:

```text
winner -> CONFIRMED
loser -> QUARANTINED_DUPLICATE_IDENTITY
Event.event_type -> USER_CHANGE
payload.kind -> RESERVATION_IDENTITY_DUPLICATE
second helper run -> []
```

## Startup migration

Snapshot F startup migration itself was independently replayed and PASSED:

- legacy duplicates quarantined;
- partial unique index created;
- audit Event valid;
- new authoritative duplicate rejected by SQLite.

Do not regress this while fixing the ORM helper.

## Patch portability

The EAC V19.2.3 patch was independently checked against the explicitly
LF-normalised V19.2.1 baseline:

`git apply --check -> PASS`

The V19.2.4 starter patch in this package was independently checked against the
submitted Snapshot-F source:

`git apply --check -> PASS`
