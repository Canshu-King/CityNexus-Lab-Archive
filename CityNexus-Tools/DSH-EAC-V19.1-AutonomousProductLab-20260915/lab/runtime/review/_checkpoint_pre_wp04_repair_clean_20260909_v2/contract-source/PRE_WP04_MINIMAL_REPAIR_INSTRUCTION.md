# CODEX — Minimal pre-WP04 correctness repair

## User instruction: NO HASH WORK
Do not calculate, compare, verify, or report SHA/file/package hashes.
Do not spend quota on hash manifests.
Focus only on code behavior, tests, contracts, state consistency, and reproducibility.

## Current status
The WP03 repair is substantially successful.
Existing suite independently reproduced: 41 passed.

Do NOT redesign architecture.
Do NOT start WP04 yet.
Do NOT work on frontend, Visio, AI, real providers, or unrelated refactors.

Only complete the following small repair.

---

## P0-1 Preserve the PLANNED Journey feasibility invariant

Problem:
A Journey can be PLANNED with a SELECTED feasible plan, then a Journey PATCH or new HARD constraint can make that plan infeasible while Journey/Plan state remains unchanged.

Implement a single reusable guard for mutations that can affect selected-plan feasibility.

For a PLANNED Journey with `active_plan_version_id`:
- evaluate the selected plan against the proposed Journey/Constraint state before committing;
- if infeasible, return 422 or 409 using the existing error envelope;
- persist nothing from the rejected mutation;
- do not change Journey/PlanVersion state.

At minimum cover:
- PATCH budget;
- PATCH start/end;
- adding a HARD constraint.

Do not invent PLANNED -> DRAFT in this cycle.

Tests:
- selected -> budget below plan cost -> reject, no mutation;
- selected -> end before selected activities finish -> reject, no mutation;
- selected -> stricter HARD budget/end -> reject, no mutation;
- selected -> harmless change preserving feasibility -> succeeds.

---

## P0-2 Repair LOCKED_COMMITMENT normalization

Current bug:
- locked start is converted to minute-of-day (15:30 -> 930);
- candidate activities are represented relative to Journey start (15:30 with 09:00 start -> 390);
- generation and persisted selection also use different activity identities (`place_id` vs Activity UUID).

Requirements:
- one stable lock identity across generation, persisted revalidation, and future replanning;
- one time basis across all phases;
- canonical locked River Cruise at 15:30 must pass;
- moved/removed locked cruise must fail.

For the MVP, use a stable semantic lock reference plus scheduled start.
Do not make a PlanVersion-specific Activity UUID the only cross-plan preservation identity.

Add tests:
1. canonical `place-river-cruise @ 15:30` LOCKED constraint -> generation succeeds;
2. persisted selected candidate revalidation also succeeds;
3. changed locked start -> fails;
4. removed cruise -> fails;
5. different place at same time -> fails.

Keep the gate deterministic and framework-independent.

---

## P1-1 Fix candidate_count search semantics if small

Current bug:
with HARD budget 33000, request candidate_count=1 returns 422 because only the first raw template is inspected, even though a later 32000 template is feasible.

Implement:
- deterministic raw candidate iteration;
- gate each candidate;
- collect up to requested `candidate_count`;
- stop when count reached or candidate universe exhausted.

Test the 33000/candidate_count=1 case.

---

## P1-2 Small traceability cleanup

If inexpensive:
- audit plan-generation batch (`plans.generated` or equivalent);
- change implementation status:
  - FR-006 IMPLEMENTED -> PARTIAL (authentication not implemented);
  - FR-018 IMPLEMENTED -> SIMULATED/PARTIAL (only mock provider currently exists).

Do not inflate requirement completion counts.

---

## Explicit defer
- WP04 booking/payment implementation;
- Journey ACTIVE/COMPLETED planning policy, unless needed by a failing test;
- Alembic;
- real providers;
- frontend;
- AI;
- Visio;
- performance tuning.

---

## Stop gate
Stop and package for review when:
- all prior 41 tests pass;
- all new P0 tests pass;
- canonical demo still returns >=2 feasible candidates;
- canonical select leaves Journey PLANNED and PlanVersion SELECTED;
- locked canonical cruise is preserved by the same feasibility layer;
- no network dependency introduced.

Preserve repo-relative paths.
Do not include or verify file hashes.
