# External Review Findings — V4 Final

## What is genuinely strong

The reviewed V4 source contains:
- real OR-Tools CP-SAT Solver V2 as the primary V2 path;
- deterministic enumeration fallback with distinct provenance;
- Mission Compiler V2 with strict model output schema plus deterministic fallback;
- RapidFuzz and Shapely integration;
- persistent JourneyMission / GuardianRun / AgentRun / AgentRunStep state;
- Autonomy Envelope and Agent Gateway;
- a backend-connected Journey Operations UI;
- a clean conceptual split between semantic inference, optimization, policy and domain mutation.

Independent focused replay in the review environment:
- 33 passed / 1 skipped for V4 Mission, Agent Authority and Impact suites.
- The skip was the local review environment's missing OR-Tools boundary.
- The Windows checkpoint's CP-SAT evidence remains the authoritative environment-specific proof.

## Finding V5-A — the proactive Guardian does not use the configured Agent runtime

`app/agent/guardian.py::scan_guardian()` currently creates:

provider_key = "citynexus-guardian"
model_key = "deterministic-recovery-controller-v1"

and then executes a fixed sequence:
1. inspect_twin
2. request_replan
3. accept_replan

It never calls `configured_journey_agent()`.

This is a useful deterministic fallback controller, but it is not a model-orchestrated Guardian.

V5 target:
Guardian should delegate recovery to the configured AgentRuntime (Hermes primary when configured, Native DeepSeek fallback), while retaining the deterministic controller as an offline fallback.

## Finding V5-B — "proactive" still requires a manual scripted trigger

The frontend's `runProactiveGuardianScenario()` currently:
1. creates a WEATHER event;
2. creates a TRAFFIC_DELAY event;
3. POSTs `/guardian/scan`.

The backend exposes `/guardian/scan`, but there is no scheduler/worker or provider pulse that invokes it automatically.

Therefore the V4 flagship proves "no new chat prompt", but not "CityNexus autonomously notices the world changing".

V5 target:
introduce a server-owned City Signal / Guardian Pulse worker. Weather/provider facts should create/update events and trigger Guardian evaluation without a UI button.

## Finding V5-C — cooldown is currently decorative

`GuardianRun.cooldown_until` is written and returned, but it is not consulted by the Guardian logic.

V5 target:
make cooldown/dedup real, scoped to semantic incident identity, not merely Event IDs.

## Finding V5-D — model mission draft can widen user authority

In `create_mission()`, when a model draft exists, the code replaces deterministic numeric bounds with model values:

- max_cost_delta_minor
- max_loss_minor
- max_schedule_drift_min

The result is later intersected with the global traveler policy, but not with explicit limits already extracted from the user's text.

A model that reads "最多多花五十元" as 500 yuan can therefore widen the per-mission budget as long as the global policy permits it.

This is not "giving AI more power". It is allowing a compiler error to expand the user's mandate.

Required rule:
authority-bearing fields must be monotonic. Model interpretation may make an instruction more specific, but must not exceed an explicit user cap extracted by a reliable local parser.

## Finding V5-E — model mutable interpretation can erase explicit protection

Current merge:
- unions deterministic + model mutable IDs;
- unions deterministic + model protected IDs;
- removes protected IDs that appear in mutable.

Therefore a wrong model draft can turn an explicitly protected Activity into mutable.

Required rule:
explicit local polarity from the raw user text outranks a conflicting model draft.
The model remains authoritative for ambiguous semantic intent where there is no explicit deterministic contradiction.

## Finding V5-F — unresolved model references are reported as empty

`JourneyMission.unresolved_references_json` is currently created as `"[]"` even when model references fail server resolution.

Persist unresolved references and surface them in the Control Tower.

## Finding V5-G — final package hygiene claim is not exact

The uploaded V4 ZIP contains `.ruff_cache` entries and a `scripts/__pycache__/...pyc` artifact.

Treat archive inspection as executable acceptance criteria in V5.
