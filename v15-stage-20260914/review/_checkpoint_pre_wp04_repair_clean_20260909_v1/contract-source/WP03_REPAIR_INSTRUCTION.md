# CODEX NEXT INSTRUCTION — WP03 correctness repair

## User constraint: no hash work
Do **not** spend quota/time on SHA-256, file hash comparison, copied-source hash equality, package hash verification, or similar review bookkeeping. The user explicitly does not want hash checks.

Focus only on executable correctness, contracts, tests, state transitions, data integrity, and a reproducible checkpoint.

## Current decision
WP00: PASS with evidence caveat.
WP01: CONDITIONAL PASS.
WP02: CONDITIONAL PASS.
WP03: REPAIR_REQUIRED.

Do **not** start WP04 yet.
Do **not** redesign architecture.
Do **not** reopen Visio work.
Do **not** add real network providers.
Do **not** work on frontend yet.

## Required P0 repair

### 1. Create one authoritative deterministic feasibility function
Use it from:
- initial plan generation;
- plan selection revalidation;
- later WP06 replanning.

For WP03 it must enforce at least:
- all active HARD constraints relevant to the current candidate;
- `BUDGET_MAX`;
- `JOURNEY_END_BY`;
- journey start/end boundary;
- activity non-overlap;
- place/service availability/open interval;
- travel time fits between adjacent activities;
- deterministic mock provider data only.

Do not score or persist a candidate before this gate passes.

### 2. Revalidate on select
Before selecting a candidate:
- reload current Journey;
- reload active Constraints;
- reload current availability/mobility context;
- re-run the same feasibility gate.

If infeasible:
- return 422 using the existing error envelope;
- do not mutate Journey;
- do not mutate PlanVersion states.

### 3. Align lifecycle
Follow the declared MVP state machine:
- initial plan selection: `CANDIDATE -> SELECTED`;
- Journey: `DRAFT -> PLANNED`;
- WP05 start will later perform `SELECTED -> ACTIVE`.

Do not silently change the state-machine contract to fit current code.

### 4. Strengthen the tests
Add/repair tests so they prove behavior rather than only persistence:

- CNX-I-001: verify complete expected schema and required indexes.
- CNX-I-007: prove a stricter HARD budget affects planner output.
- New: stricter `JOURNEY_END_BY` rejects plans that end after it.
- New: closed/unavailable place makes candidate infeasible.
- New: insufficient mobility gap makes candidate infeasible.
- CNX-I-009: independently assert generated candidates satisfy the same feasibility gate.
- New: generate -> add stricter HARD constraint -> select old candidate returns 422 with no state change.
- CNX-I-010: assert selected PlanVersion state is `SELECTED` and Journey reference/status are consistent.

### 5. Fix duplicate preference input
Duplicate `(category,key)` items in the same PUT request must not become HTTP 500.
Prefer deterministic request validation with 422.

## P1 repair if it is small
Reconcile ORM metadata with SQL for:
- Journey active_plan_version_id FK
- Journey current_activity_id FK
- PlanVersion parent_plan_version_id FK
- SQL unique constraints for preferences, places, city_services, plan_versions, activities

Add audit records for material WP01-WP03 mutations, especially Journey update and plan selection. If not implemented this cycle, correct checkpoint prose so it does not claim full mutation audit coverage.

Resolve the ignored `JourneyCreate.planning_mode` field before frontend work. Do not invent a larger redesign.

## Explicitly defer this cycle
- Alembic migration polishing unless needed by a concrete repair.
- WP04 booking/payment.
- WP05 execution.
- WP06 replanning.
- frontend.
- AI.
- Visio.
- performance optimisation unrelated to a failing test.

## Stop gate
Stop and create a new checkpoint review package when:
- all previous tests pass;
- all new P0 regression tests pass;
- the canonical demo still generates at least two feasible plans;
- canonical select leaves Journey PLANNED with the declared selected-plan lifecycle;
- no runtime network dependency was introduced.

The review package should preserve repo-relative paths so it can be executed directly. Do not include or verify file hashes.
