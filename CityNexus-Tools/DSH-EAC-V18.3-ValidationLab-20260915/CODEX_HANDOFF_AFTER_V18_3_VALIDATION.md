# Codex Handoff — after DSH-EAC V18.3 Validation Lab

This note is for the Codex agent that owns `D:\moodle\CityNexus`. A separate
WorkBuddy continuation ran an **independent** validation lab against read-only
copies and throwaway runtimes. It did **not** modify your worktree. Here is what
you need to act on.

## 1. Defects you should merge

### F2 — `capabilities` unconfigured branch missing `ready` (OPEN, safe, 1 line)
- File: `backend/app/integrations/hermes/native_client.py`
- Fn: `native_hermes_status()` — the **unconfigured** branch.
- Symptom: readers doing `caps['ready']` raise `KeyError` *only* when native Hermes
  is unconfigured (the isolation state this lab exercises).
- Fix: add `"ready": False,` to that branch.
- Patch: `patches/V18_3_LOW_CONFLICT_FIXES.patch` (paths are repo-root relative; it was
  generated against the **validated source-snapshot**, so if your live tree has already
  evolved, just port the identical one-line addition shown above — do not force-apply.)

### F3 — `.v8-runtime-card` missing CSS (OPEN, safe, 1–2 lines)
- File: `frontend/src/features/intelligence/ControlTowerPanel.tsx:47` uses
  `className="v8-runtime-card"` (data-testid `v17-runtime-status`).
- Symptom: no CSS rule exists for that class → label/value/disclaimer collapse to
  one line on all viewports.
- Fix:
  ```css
  .v8-runtime-card { display: block; }
  .v8-runtime-card b, .v8-runtime-card small { display: block; }
  ```
- Patch: `patches/V18_3_LOW_CONFLICT_FIXES.patch`

### F1 — RESOLVED (no action)
Unknown native-Hermes run now returns 502 `REQUEST_ERROR` instead of a bare 500.
Already fixed in `backend/app/main.py:491` (client constructed inside `try`).

## 2. What the lab proved (no action needed)
- Native Hermes E2E path is genuine and isolated (Stream A, 7/7 gates).
- Semantic policy correct + injection-safe: 5764/5764 (Stream B).
- Fail-closed contract on unknown runs/stops/SSE (Streams C/D).
- Concurrency: distinct runs per duplicate request; unknown journey → 404 (Stream E).

## 3. Evidence gaps gated by upstream LLM availability
Not product bugs — blocked only because DeepSeek returned "Service is too busy":
- **CN-C** approval-object generation (run `tests/run_concurrency_approval.py --case CN-C` on a responsive window).
- **CH5** reconnect-dedup live proof (rerun `tests/run_chaos.py --case CH5 --run-id <fresh>`).
- **A11y screenshots** at 1440×900 / 1280×720 / 390×844 / 430×932 (run `tests/capture_a11y_screenshots.py` with the stack up).

## 4. How to re-run the lab
```bash
cd D:/moodle/CityNexus-Tools/DSH-EAC-V18.3-ValidationLab-20260915
python tests/start_hermes_gateway.py     # :8653 profile citynexus-harness-lab
python tests/_run_backend_foreground.py  # :8022 isolated db
python tests/run_semantic_corpus.py      # offline, always works
python tests/run_api_contract.py         # C1-C10
python tests/run_chaos.py                # CH1-CH6
python tests/run_concurrency_approval.py # CN-A..CN-C
python tests/aggregate_results.py        # rewrites evidence/results.json
```
The semantic corpus + API contract + chaos + concurrency scripts are LLM-free or
backend-only and will run even when DeepSeek is busy.

## 5. Integrity note
`D:\moodle\CityNexus` was **not** modified by this lab. The lab used
`source-snapshot/` (a copy) and `citynexus_lab.db` (throwaway). You can verify
with `git status` on your tree — it should be exactly as you left it.
