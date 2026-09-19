# Codex path after WP04 is externally accepted

Do not execute these early. This is the future roadmap so Codex does not spend quota re-planning later.

## WP05 — Journey execution + JourneyTwin

1. Start Journey: PLANNED -> ACTIVE and SELECTED plan -> ACTIVE.
2. Move first future Activity to READY/ACTIVE according to MVP policy.
3. Build JourneyTwin projection from source records.
4. Complete Activity and advance current/next.
5. Include upcoming commitment summary using stable semantic commitment identity.
6. Tests CNX-I-014/015.
7. Stop/checkpoint.

## WP06 — Event + deterministic replanning

1. Event persistence and closure effect.
2. RealitySnapshot / ContextSnapshot.
3. Partition historical/protected/mutable future.
4. Read ACTIVE C4 commitment from WP04, not a guessed UI lock.
5. Generate F0-F4 bounded candidates.
6. Reuse authoritative feasibility layer.
7. Apply exact 8-component utility weights.
8. Persist ReplanProposal without active-plan mutation.
9. Accept atomically with stale check and final feasibility recheck.
10. CNX-I-016..023 + locked River Cruise unchanged.
11. Stop/checkpoint.

## WP07 — AI Copilot

Only after deterministic core passes. AI may explain/rank verified feasible candidates but cannot override hard gates or activate plans.

## WP08 — Frontend vertical slice

Generate client/types from OpenAPI or consume contract directly. Screens: dashboard, create journey, plans, booking/payment, active journey/twin, demo event, replan compare, history, copilot.

## WP09 — E2E/evidence

Playwright/API golden scenario, AI-off scenario, provider failure, stale/idempotency tests, screenshots, demo reset script, coursework evidence.

## WP10 — 138 requirement expansion

Batch only after vertical slice is stable. Never mark implemented without acceptance evidence/test linkage.
