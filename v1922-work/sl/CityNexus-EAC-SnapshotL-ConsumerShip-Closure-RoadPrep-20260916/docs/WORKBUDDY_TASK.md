# WorkBuddy targeted delta — Snapshot L

Read-only.

Freeze Snapshot K and validate only:

## Scheduler
- inbound travel from ARRIVAL/pinned left boundary;
- outbound travel to CHECK_IN/locked right boundary;
- transition origin resets correctly after pinned nodes;
- pinned overlap -> explicit conflict;
- Day-2/Day-3 POIs do not silently move to Day 1.

## Hotel + recovery
- hotel preserves POIs and original day semantics;
- exact locked/C4 times preserved;
- targeted mutable Xiamen POI closure produces material repair or NO_ALTERNATIVE;
- no mobility identity error.

## Network
- direct/proxy policy configurable;
- no hardcoded proxy bypass as the only path.

## Product
- consumer booking import;
- Activity Detail does not falsely call arbitrary stops nearby;
- Copilot traveler-facing;
- Today/Trips/Live/Me cleaned up;
- full visible same-Xiamen trace;
- Chinese-first;
- visual screenshots materially closer to the UI references.

Final:
BLOCKED
or
SNAPSHOT_ACCEPTED_FOR_XIAOMI_13_ULTRA_TRIAL
