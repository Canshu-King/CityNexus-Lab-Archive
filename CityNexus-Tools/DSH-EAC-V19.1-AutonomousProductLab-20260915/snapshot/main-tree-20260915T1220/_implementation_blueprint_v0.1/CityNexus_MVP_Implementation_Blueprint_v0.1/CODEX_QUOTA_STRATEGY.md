# Codex Quota Strategy

The objective is to spend model capacity only where implementation uncertainty exists.

## Mechanical work - use the cheaper/faster capable model

Suitable tasks:
- create folders;
- copy contracts;
- SQLAlchemy model transcription from reconciled schema;
- CRUD routers;
- mock-data loaders;
- simple unit tests;
- formatting/lint fixes;
- checkpoint packaging.

Codex instruction: do not re-explain architecture during these tasks. Implement the referenced work package and run its gate.

## Medium reasoning work

Suitable tasks:
- repository/service integration;
- state-transition bugs;
- OpenAPI/implementation mismatch;
- frontend/backend wiring;
- idempotency and transaction boundaries.

## Highest reasoning reserved for WP06

Use the strongest reasoning only for:
- deterministic candidate generation under multiple constraints;
- diagnosing no-feasible-replan cases;
- commitment-preservation edge cases;
- score/tie-break consistency;
- stale snapshot/proposal concurrency behavior.

Even in WP06, do not ask the model to rediscover the algorithm. Point it to `07_REPLANNING_ALGORITHM.md` and ask it to implement or debug a specific failing test.

## Prompt discipline

Good:

`Implement WP02 exactly from 09_WORK_PACKAGES.md. Do not redesign. Run CNX-I-003..007. Stop and package checkpoint.`

Bad:

`Build CityNexus from scratch and make it amazing.`

The second prompt is how humans turn quota into decorative smoke.
