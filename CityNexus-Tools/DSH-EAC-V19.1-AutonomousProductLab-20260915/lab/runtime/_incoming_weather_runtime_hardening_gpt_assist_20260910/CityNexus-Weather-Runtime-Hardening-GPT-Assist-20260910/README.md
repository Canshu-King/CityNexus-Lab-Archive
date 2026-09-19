# CityNexus Weather Runtime Hardening - GPT Assist

This package is an external adversarial review and repair aid for `CityNexus-Weather-Runtime-Checkpoint-20260910.zip`.

The submitted checkpoint is materially good, but six additional semantic defects were demonstrated with executable tests. The included reference patch fixes those six on a clean checkpoint copy and preserves all original gates.

Start with:

1. `REVIEW_FINDINGS.md`
2. `CODEX_START_HERE.md`
3. `CODEX_ONE_SHOT_PROMPT.txt`
4. `tests/test_gpt_weather_adversarial_next.py`
5. `contracts/WEATHER_RUNTIME_HARDENING_FREEZE_GATE.md`

Do not start OR-Tools until the Weather Runtime hardening checkpoint is externally frozen.

Solver road-prep is already included in:

- `contracts/SOLVER_RUNTIME_GAP_ANALYSIS.md`
- `contracts/NEXT_SOLVER_RUNTIME_BLUEPRINT.md`
