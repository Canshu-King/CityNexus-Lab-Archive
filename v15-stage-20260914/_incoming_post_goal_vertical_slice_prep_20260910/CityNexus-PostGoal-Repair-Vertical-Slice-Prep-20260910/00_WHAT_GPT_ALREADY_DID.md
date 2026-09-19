# What GPT already did for Codex

Do not spend another long cycle rediscovering these facts.

## Read and reconciled

GPT read/reconciled the 2026-09-10 complete handoff, product/GitHub masterplan, WP06→WP07 road-prep review package, and overnight Goal checkpoint. The 2026-09-07 Visio-centered handoff is historical background only; the current mainline is real software → Golden Scenario → course artifacts.

## Independently reproduced

Uploaded overnight backend:

```text
149 passed, 1 skipped
```

Then GPT added five adversarial tests to the untouched checkpoint. Result:

```text
5 failed
```

The five failures are preserved verbatim in:

```text
reports/ORIGINAL_FIVE_DEFECT_FAILURES.txt
```

So the defects are not guesses derived from prose.

## Directly implemented on a clean review copy

GPT repaired:

```text
F3 effective Event time + evidence-consistent persisted F3 schedule
C4 activity_id remap after accepted replan
persisted-plan MobilitySnapshot injection seam
Open-Meteo Unix timestamp + UTC semantics
TRAFFIC_DELAY extra_minutes semantics
```

GPT also created a real backend Golden Scenario contract test covering:

```text
plan → booking → capture → C4 → start → event → replan → accept
→ PlanVersion transition → C4 remap → JourneyTwin reload
```

Final backend evidence on a fresh patched copy:

```text
6 focused passed
155 passed, 1 skipped full suite
compileall PASS
```

## Frontend work already prepared

GPT inspected the actual frontend and confirmed it is still a hardcoded/localStorage shell. Existing Playwright is UI smoke, not backend-connected E2E.

To reduce Codex design work, GPT prepared semantic starter code for:

```text
API client
Golden Scenario bootstrap
XState Journey Mode workflow
Vite backend proxy
multi-server Playwright config
backend-connected Playwright test skeleton
```

These are under `future_scaffold/frontend/`.

They are intentionally marked scaffold because final npm compilation could not be completed in GPT's sandbox after dependency installation timed out. Codex should adapt/compile, not rewrite the architecture from scratch.

## Work Codex should NOT repeat

Do not:

```text
re-investigate whether the five defects exist on the uploaded checkpoint
re-design CityNexus product identity
reopen Visio route repair
recount requirements just to regain context
perform file/archive SHA review
install every optional provider before the Golden vertical slice
replace FastAPI with another stack
let OR-Tools/AI/provider bypass deterministic feasibility
```

The efficient next action is to run the supplied focused tests on the **real Windows worktree**, semantic-merge missing fixes, and then connect frontend to backend.
