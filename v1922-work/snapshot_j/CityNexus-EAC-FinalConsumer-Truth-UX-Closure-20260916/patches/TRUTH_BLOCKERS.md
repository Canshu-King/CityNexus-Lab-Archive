# Truth blockers

## T1 — Stay must augment, never erase, the selected itinerary

Before stay selection:
- selected real-city POIs must be recorded.

After stay selection:
- all still-valid selected POIs remain;
- check-in / stay / check-out are inserted around them;
- only explicit conflict resolution may move/remove a POI;
- any changed activity is visible in a diff.

Add regression:

real Xiamen plan with >= 3 POIs
-> select stay
-> reload DB
-> active/selected plan still contains those POIs
-> stay nodes inserted
-> feasibility passes.

## T2 — No-op replan forbidden for disruption

For CLOSURE / WEATHER:

if target cannot be resolved:
- no F0_STABLE_COPY acceptance;
- explicit TARGET_UNRESOLVED / NEEDS_CLARIFICATION.

if target is protected:
- explicit PROTECTED_CONFLICT / MANUAL_RECOVERY_REQUIRED.

if target is mutable:
- proposal must contain at least one material change:
  - removed
  - added
  - moved
  - retimed
  - transport changed
  - or a documented equivalent.

If no feasible material repair:
- durable NO_ALTERNATIVE.

Do not allow:
CLOSURE -> stable copy -> ACCEPTED.

## T3 — Replan acceptance evidence

Final acceptance disruption must target a real mutable Xiamen POI.

Record:
- base plan id
- target activity id/title
- proposal family
- exact diff
- proposed plan id
- accepted plan id
- recovery state before/after.

A hotel check-in closure should be a separate protected-conflict test, not the only success case.

## T4 — Clean acceptance state

Use a fresh acceptance journey and clean test DB/state.

Avoid accumulated provider captures from previous retries.

Report:
- offers captured
- options generated
- dedupe identities
- cards shown

Counts must reconcile.
