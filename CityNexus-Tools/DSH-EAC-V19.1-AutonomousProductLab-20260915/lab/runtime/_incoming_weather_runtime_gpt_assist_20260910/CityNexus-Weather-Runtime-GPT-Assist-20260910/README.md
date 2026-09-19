# CityNexus Weather Runtime GPT Assist - 2026-09-10

Purpose: remove as much reasoning and implementation work as possible from the next Codex window while preserving Codex's ability to inspect the real Windows repository and improve the design.

## Current project gate

```text
Vertical Slice                 FROZEN_PASS
Provider Runtime               FROZEN_PASS
Weather Runtime                NEXT
OR-Tools                       BLOCKED UNTIL WEATHER FREEZE
AI / MapLibre / Trust polish   LATER
```

## What GPT did in this package

GPT independently inspected the latest Provider Runtime Hardening checkpoint and found that Open-Meteo foundations exist but there is still no real deterministic weather-to-Activity runtime path.

GPT then prepared a reference implementation and adversarial gate covering WRT-01..WRT-12.

Reference validation:

```text
Weather gate:     12 PASS
Focused old+new:  33 PASS
Full backend:     182 PASS / 1 SKIP printed
Compileall:       PASS
```

See `reports/REFERENCE_VALIDATION.md` for the Linux post-pytest cleanup caveat and Ruff limitation.

## Package map

```text
README.md
CURRENT_WEATHER_GAP_ANALYSIS.md
PRODUCT_AND_GITHUB_CONTEXT.md
CODEX_START_HERE.md
CODEX_ONE_SHOT_PROMPT.txt

contracts/
  WEATHER_RUNTIME_ARCHITECTURE.md
  WEATHER_RUNTIME_FREEZE_GATE.md
  NEXT_SOLVER_GATE.md

patches/
  01_WEATHER_RUNTIME_TESTS.patch
  02_WEATHER_RUNTIME_REFERENCE_IMPL.patch
  ALL_WEATHER_RUNTIME_REFERENCE.patch

tests/
  test_weather_runtime_gate_gpt.py

reference_overlay/
  backend/app/integrations/context/weather_runtime.py
  backend/app/integrations/context/weather_snapshot.py
  backend/app/integrations/context/weather_ingestion.py
  backend/tests/test_weather_runtime_gate_gpt.py
  data/mock/places.json

reports/
  BASELINE_WEATHER_GATE_FAILURES.txt
  WEATHER_GATE_12_PASS.txt
  FOCUSED_REGRESSION_33_PASS.txt
  FULL_BACKEND.txt
  COMPILEALL.txt
  RUFF.txt
  REFERENCE_VALIDATION.md

tools/
  run_weather_runtime_gate.ps1
  check_review_package_hygiene.ps1
```

## Most important instruction

Do not blindly apply the reference code patch. Apply/copy the tests first against the actual worktree. If the GPT Web Codex window has already implemented part of Weather Runtime, use the tests to discover the delta and semantic-merge only what remains.

## Reference semantic choices

The reference implementation deliberately chooses boring, auditable rules over clever inference:

- query per unique explicit weather-sensitive Place
- use exact Place coordinates as query-scope evidence
- hourly provider rows become half-open one-hour validity intervals
- convert UTC to Journey timezone before Activity overlap
- `indoor` means no automatic rain attribution
- `outdoor` means eligible
- `weather_sensitive` is an explicit override
- unknown means no auto-attribution
- only current/future non-terminal Activities are eligible
- repeated provider facts are idempotent
- repeated outage polling does not create an Event storm

This is intentionally suitable for Software Engineering traceability and testing.
