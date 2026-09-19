# CityNexus — WorkBuddy V16 Real-User Lab (2026-09-14)

This package is the deliverable of the **V16 Real-User Lab** for the CityNexus
Smart-City Traveller System. It follows the V15 operating rules in
`V15 RoadPrep` (isolation of the Codex worktree, DeepSeek V4 Flash, no questions
to the sleeping user, full OUTPUT_CONTRACT).

## What this is

A simulated "real user" drove CityNexus's **own front end** as 12 traveller
personas across 12 different cities — including county towns (沙县, 婺源, 敦煌,
霞浦) and non-CNY currencies (London GBP, Tokyo JPY, Singapore SGD) — and typed
the kinds of things a real traveller types into the DeepSeek chat desk:
self-descriptions, hypotheticals, comfort preferences, and genuine disruptions
(typhoon, train delay, museum closure, lost passport, fever…).

Every product-logic defect found was **fixed in place and re-tested**, in the
spirit of the V16 directive.

## Key results

* 12 / 12 personas created a journey and exercised the full UI (hub → studio →
  stay → discover → live → map → bookings → intelligence → twin → authoritative →
  agent → me) with **0 console errors, 0 page errors, 0 HTTP errors** and
  **≥3 plan options** each.
* 11 product-logic defects catalogued and fixed (see `V16_FINDINGS.md`).
* 17 offline regression tests added and passing (`backend/tests/test_v16_realuser_fixes.py`).

## How to apply the fix

```bash
cd D:\moodle\CityNexus
git apply --check WorkBuddy-V16-RealUserLab-20260914/patches/v16_production.patch
git apply            WorkBuddy-V16-RealUserLab-20260914/patches/v16_production.patch
```

## Package contents

| Path | Purpose |
|------|---------|
| `WORKBUDDY_V16_REALUSER_REPORT.md` | Full lab report (method, findings, validation, results). |
| `V16_FINDINGS.md` | Ranked catalogue of product-logic defects and fixes. |
| `CODEX_MERGE_AFTER_V16.md` | Merge handoff for the Codex worktree. |
| `patches/v16_production.patch` | Apply-ready, production-only diff. |
| `backend/tests/test_v16_realuser_fixes.py` | Regression suite (17 tests). |
| `evidence/v16_lab/` | Raw simulation outputs: per-persona JSON, screenshots, run log. |
| `tools/v16_realuser/matrix.json` | The 12-persona × 13-injection test matrix. |

## Reproduce the simulation

```bash
cd WorkBuddy-V16-RealUserLab-20260914
# backend on 8010 (AI enabled), frontend on 4173 — isolated from Codex's 8000/5173
node frontend/_v16_trial/user_lab.mjs --all
```

DeepSeek key and model are read from the environment
(`CITYNEXUS_AI_ENABLED`, `DEEPSEEK_API_KEY` / `CITYNEXUS_AI_API_KEY`,
`CITYNEXUS_AI_MODEL=deepseek-v4-flash`).
