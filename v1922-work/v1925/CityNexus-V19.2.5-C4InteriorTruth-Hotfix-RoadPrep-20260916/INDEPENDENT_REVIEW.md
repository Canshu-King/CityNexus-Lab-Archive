# Independent Review

## Snapshot G checks independently confirmed

- Uploaded EAC V19.2.4 SHA-256 exactly matches the ZIP frozen inside the WorkBuddy package:
  `b6c521c1163791146bdf0989bca0d40f61c2c865862eabe6156274a7eeb0b017`.
- `V19_2_4_CODE.patch` applies cleanly to the declared LF-normalised V19.2.1 baseline.
- After applying, all 22 packaged source files match the reconstructed tree byte-for-byte after LF normalisation.
- V19.2.4 truth probe F01-F04 passes.
- Recovery durable-truth probe passes.
- Reservation migration/helper probe passes.
- Release ZIP contains none of the banned caches/logs/db files.

## Residual shared-gate defect independently reproduced

Against the exact Snapshot G code:

```text
ARRIVAL 12:30 + MID_TRIP 10:00
-> shared evaluate_feasibility() passed=true   WRONG

DEPARTURE 15:30 + MID_TRIP 17:00
-> shared evaluate_feasibility() passed=true   WRONG

ARRIVAL 12:30 + role-less booking C4 10:00
-> shared evaluate_feasibility() passed=true   WRONG
```

Root cause:

`evaluate_feasibility()` builds `anchor_keys` for every `LOCKED_COMMITMENT` and then skips every
anchor activity when enforcing ARRIVAL/DEPARTURE boundaries.

Only structural edge anchors (`ARRIVAL`, `DEPARTURE`) should skip their own edge checks.
Interior locks (`MID_TRIP` and role-less booking/order anchors) must remain inside the usable city interval.

## Verified starter semantics

The included patch changes the skip rule to role-aware logic.

Independent probe after the patch:

```text
MID_TRIP before ARRIVAL       -> FAIL C4_ACTIVITY_BEFORE_ARRIVAL
MID_TRIP after DEPARTURE      -> FAIL C4_ACTIVITY_AFTER_DEPARTURE
role-less C4 before ARRIVAL   -> FAIL C4_ACTIVITY_BEFORE_ARRIVAL
valid MID_TRIP inside bounds  -> PASS
valid role-less C4 inside     -> PASS
```

The prior V19.2.4 F01-F04 truth probe remains 4/4 PASS.

## Evidence-pack note

WorkBuddy's prose correctly distinguishes Snapshot F and Snapshot G, but the archived
`F_recovery_results.json` and `F_reservation_results.json` contain post-fix/pass-style data.
This is an evidence bookkeeping defect, not a Snapshot-G production defect. The G behaviour was
independently re-run and confirmed.
