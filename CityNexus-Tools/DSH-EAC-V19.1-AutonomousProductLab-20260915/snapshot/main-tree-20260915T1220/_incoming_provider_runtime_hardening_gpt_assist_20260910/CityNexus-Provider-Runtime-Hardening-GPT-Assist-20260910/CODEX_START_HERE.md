# Codex Start Here

You are receiving an external adversarial review of the Provider Runtime Gate.

Do not assume the uploaded checkpoint is already frozen just because PRT-01..08
are green.

## First action in the user's real repository

```powershell
git status --short
git diff --stat
```

Do not reset or rollback anything.

## Safe merge procedure

1. Copy only `tests/test_gpt_adversarial_provider_hardening.py` into
   `backend/tests/`.
2. Run it against the real current worktree.
3. The reviewed checkpoint fails all five tests, but the real repo may already
   contain newer fixes.
4. Semantic-merge only the failures that remain.
5. Use `patches/02_PROVIDER_RUNTIME_HARDENING_CODE.patch` as a reference, not as
   permission to overwrite newer code.
6. Run the Provider Runtime tests, previous Golden/hardening tests, full backend,
   compileall, Ruff, OpenAPI parity, frontend build and Playwright.
7. When all Provider Runtime + PRH gates pass, produce a clean checkpoint and
   stop.
8. Only after external freeze move to `contracts/NEXT_WEATHER_RUNTIME_GATE.md`.

## External validation already performed on the reference copy

```text
uploaded checkpoint + new adversarial tests:
5 failed

reference hardening:
13 provider/hardening tests passed
full backend: 170 passed, 1 skipped
compileall: PASS
OpenAPI: 38/38
```

## Important architecture choice

The reference patch uses the proposal's persisted snapshot for accept-time
revalidation. If the current worktree already has an explicit fresh acceptance
snapshot design, that is also acceptable if and only if:

- capture happens outside deterministic feasibility;
- the new frozen evidence is persisted/auditable;
- no implicit MockMobilityProvider substitution occurs;
- offline mode remains deterministic.
