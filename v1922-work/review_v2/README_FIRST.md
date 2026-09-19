# CityNexus-EAC-Review-20260918

Review package for the **Xiaomi trial final hotfix v2** round.

This package is a **narrow evidence-correction package**. It contains the fix
for one real defect plus the correction of one false-positive assertion, and it
documents (but deliberately does not fix) a third defect that blocks the
end-to-end closure replan.

## Read in this order

1. **`FINDINGS.md`** — the three findings, what is fixed, what is open.
2. **`CHANGED_FILES.txt`** — every file touched and why.
3. **`R1_D_PHYSICAL_IDENTITY_PATCH.txt`** — exact code of the real fix.
4. **`TEST_RESULTS.md`** — 762 passed / 15 skipped; the 3 new tests.
5. **`MOCK_MOBILITY_LIMITATION.md`** — the open defect, with root cause and options.
6. **`AUTONOMOUS_CYCLE_1..5.md`** — independent adversarial findings.
7. `patched_source/` — full patched files for review.

## One-line status

The engine's physical-venue identity is now correct and the harness can no
longer report a false "recovered". The remaining blocker is a fabricated
constant travel time (20 min) on every newly-created replan leg, which makes the
deterministic gate correctly refuse the proposal. **Do not ship a Xiaomi trial
until that is resolved** — see `MOCK_MOBILITY_LIMITATION.md`.
