# AUTONOMOUS CYCLE 4 — The product states the budget relationship truthfully and shows unknown prices as unknown, never as 0

## Hypothesis
The product states the budget relationship truthfully and shows unknown prices as unknown, never as 0

## Method
Compare each candidate plan cost against the journey budget, then count accommodation offers with no price evidence.
Driver: `D:\moodle\_v1922_work\lab5.cjs` (Playwright + Chrome, 390x844, locale zh-CN).
Raw probe output: `evidence/LAB_PROBE_RESULTS.json`.

## Evidence
All 3 candidate plans rendered '预算内' (within budget) and '总花费 CNY 0' while every stop carried NO price evidence (price_known=false, cost_minor=0), and 10 of 10 accommodation offers had no price. The product was deriving a confident budget verdict from missing data.

## Verdict
CONFIRMED_DEFECT

## Fix
Files changed: `frontend/src/features/planning/PlanComparison.tsx`

## Residual risk / what a real user trial should watch
Plan cards now read '花费未知 / 暂无价格' and the band is classed 'unknown' whenever no stop carries price evidence. Re-verified in the browser: 3 cards, all '花费未知 / 暂无价格'.
