# Trace integrity gate

READY requires evidence that corresponds to the FINAL code.

For every critical feature:
- identify fix timestamp / checkpoint;
- identify browser evidence timestamp after that fix;
- identify journey_id;
- identify selected/active plan ids where relevant.

Critical features:
1. AI planning success gate
2. plan select
3. hotel select
4. booking confirm
5. Copilot place answer
6. Live material replan
7. replan accept

Reject:
- pre-fix screenshots cited as post-fix proof;
- new UUID without material diff;
- API-only substitute for user action;
- changed journey_id;
- demo/reset substitution.

If all product blockers are fixed but one final screenshot/trace is merely stale,
classify the implementation separately from the evidence gap, but do not grant
full trial acceptance until the final visible proof exists.
