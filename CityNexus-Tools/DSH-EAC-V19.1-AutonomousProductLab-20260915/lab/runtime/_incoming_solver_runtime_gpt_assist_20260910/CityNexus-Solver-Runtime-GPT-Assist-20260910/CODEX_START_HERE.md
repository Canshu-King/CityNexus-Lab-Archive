# CODEX START HERE - Solver Runtime Stage

## Stage transition

External review accepts the latest Weather Runtime Hardening checkpoint as:

```text
Weather Runtime Hardening = EXTERNAL_FROZEN_PASS
```

Do not reopen Weather, Mobility Runtime, Vertical Slice, Domain, Requirements, or Visio unless a regression test proves a breakage.

The next engineering stage is:

```text
OR-Tools Solver Runtime V1
= real replacement-window CP-SAT candidate generation
```

This is **not** a request for a full TSP, full-day optimizer, microservice, AI planner, or technology migration.

## First actions in the real Windows repository

```powershell
cd D:\moodle\CityNexus
git status --short
git diff --stat
git log --oneline -n 10
```

Inspect the current versions of:

```text
backend/app/main.py::generate_replan
backend/app/planning/ortools_adapter.py
backend/app/planning/replan_candidate_problem.py
backend/app/services.py
backend/app/integrations/mobility/*
backend/app/core/config.py
backend/pyproject.toml
```

Do not assume this Assist package is newer than the live tree. Semantic-merge only.

## What GPT already prepared

This package contains:

- an external Weather freeze review;
- a concrete Solver Runtime architecture contract;
- ORT-01..20 freeze gates;
- a code integration map based on the current `generate_replan()` seam;
- a pure immutable `ReplanSolverProblem` contract;
- a dependency-free reference enumerator used as an oracle;
- an optional CP-SAT reference adapter;
- a pure solver-mode/runtime policy reference that only controls attempt/fallback metadata;
- tests for the pure contract and optional dependency boundary;
- an optional `solver` dependency patch;
- package/static-boundary tools;
- known non-blocking debt that must not be mixed into the solver mutation batch.

Reference preparation validation in GPT's environment:

```text
pure solver/reference tests: 15 PASS / 2 SKIP
compileall: PASS
SKIP reason: OR-Tools is not installed in GPT's environment
```

The Windows repo must run the real OR-Tools branch after installing the optional solver dependency.

## Implementation target

Use one frozen operation-scoped MobilitySnapshot already captured by `generate_replan()` and build a **pure** replacement-window problem for Closure/Weather replacement families when there is a future durable C4 anchor.

```text
Current execution location
+ disruption effective time
+ deterministic replacement options
+ opening windows
+ remaining budget
+ frozen mobility pairs
+ next protected C4
+ safety buffer
        |
        v
ReplanSolverProblem
        |
        v
OR-Tools CP-SAT
        |
        v
SolverCandidate(s)
        |
        v
existing PlanVersion materializer
        |
        v
EXISTING CityNexus deterministic feasibility gate
        |
        v
verified score / ReplanDiff / proposal
```

Solver output is never authoritative.

## Important integration decision

Do not overload `window_opens_at` to smuggle a solver-assigned start time. Extend the internal candidate spec with a semantically explicit field such as:

```text
explicit_candidate_start_at
solver_provenance
```

A solver-generated replacement family can be called:

```text
F4_ORTOOLS_WINDOW_REPLACEMENT
```

The existing F0/F1/F2/F3 path remains the deterministic fallback/regression anchor.

## Feature boundary

Prefer an optional dependency:

```toml
solver = ["ortools==9.15.6755"]
```

and a server-owned mode such as:

```text
CITYNEXUS_SOLVER=deterministic   # default / offline-safe
CITYNEXUS_SOLVER=ortools
CITYNEXUS_SOLVER=auto
```

The browser must never choose feasibility authority.

## Tests first

Before mutating `main.py`, promote the Assist reference tests and implement real integration tests corresponding to ORT-01..20 in `contracts/ORT_TEST_MATRIX.md`.

At minimum, make the real CP-SAT branch prove:

- immutable completed prefix;
- immutable C4 semantic/time anchor;
- frozen mobility only, zero network;
- opening hours and budget;
- deterministic workers/seed;
- unique Top-K option assignments;
- controlled missing dependency / UNKNOWN / timeout fallback;
- no orphan candidate rows;
- solver provenance + mobility snapshot id;
- every materialized candidate reruns CityNexus deterministic feasibility;
- accept-time revalidation remains untouched;
- fully offline Golden Scenario still passes.

## Hard scope boundary

Do not start in this batch:

- LiteLLM / DeepSeek;
- MapLibre real map;
- WebAuthn / Stripe polish;
- GraphHopper / OTP / OSRM;
- time-bounded Weather hazard redesign;
- proposal lifecycle cleanup;
- database redesign;
- microservices;
- PPT / Visio.

## Stop condition

When ORT-01..20 and inherited regressions are green, create a clean Solver Runtime checkpoint and **STOP for external GPT review**.
