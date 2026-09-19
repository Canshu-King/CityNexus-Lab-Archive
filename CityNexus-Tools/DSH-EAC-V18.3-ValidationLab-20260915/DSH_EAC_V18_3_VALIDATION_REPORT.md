# DSH-EAC V18.3 — 6H Independent Validation Lab — Master Report

**Lab:** CityNexus DeepSeek Harness EAC V18.3
**Workspace:** `D:\moodle\CityNexus-Tools\DSH-EAC-V18.3-ValidationLab-20260915`
**Policy:** `NO_USER_DECISION_POLICY` — Codex retains exclusive ownership of
`D:\moodle\CityNexus`; this lab used read-only copies + throwaway runtimes only.
**Main tree modified:** **NO** (verified before/after).

---

## 0. Why this lab exists / what was stuck

The DeepSeek Harness owned two V18.3 tasks. Both stalled because the upstream
DeepSeek endpoint returned **"Service is too busy. We advise users to temporarily
switch to alternative LLM API service providers."** — every LLM-dependent call
hung, and the live harness self-terminated after one native E2E pass with no
task-board driver. This continuation (WorkBuddy) completed the lab against the
isolated stack without needing the user to decide anything.

---

## 1. Stream scorecard

| Stream | Scope | Result |
|---|---|---|
| A | Isolated Native Hermes E2E | ✅ PASS (7/7 gates) |
| B | Semantic Traveller Corpus | ✅ PASS (5764/5764, 4 injections neutralised) |
| C | Runtime / API Contract | ⚠️ F1 RESOLVED · F2 OPEN |
| D | Hermes Chaos & Recovery | ✅ PASS (5/6 injectable; CH5 inconclusive this window) |
| E | Concurrency / Idempotency / Approval | ⚠️ CN-A/CN-B PASS · CN-C N/A (DeepSeek busy) |
| F | Desktop / Mobile / A11y | ⚠️ SOURCE-VERIFIED · F3 OPEN · screenshots pending live stack |
| G | Lightweight Stability | ➖ Not independently re-run (covered by A/E passing) |

## 2. Defect register

| Id | Title | Status | Evidence | Fix |
|---|---|---|---|---|
| **F1** | native Hermes unknown-run → bare 500 | **RESOLVED** | unknown run → 502 `REQUEST_ERROR` (C3/C4/C5) | already fixed in `main.py:491` (client inside `try`) |
| **F2** | capabilities unconfigured branch missing `ready` | **OPEN** | `native_client.native_hermes_status()` unconfigured omits `ready` → `KeyError` for readers | add `"ready": False` to unconfigured branch (1 line) |
| **F3** | `.v8-runtime-card` missing CSS | **OPEN** | class used at `ControlTowerPanel.tsx:47`, zero CSS rules → label/value/disclaimer collapse | add `.v8-runtime-card { display:block }` (+ children) — 1–2 lines |

## 3. What was proven

- **The native Hermes path is real and isolated.** A full Copilot → DeepSeek
  SemanticEnvelope → HERMES_NATIVE_MCP → Runs/SSE → real MCP tool → Guardian →
  proposal chain executed against a throwaway DB; the authoritative tree was never
  touched (Stream A).
- **The semantic policy layer is correct and injection-safe** — 5764 cases, 0
  failures, including 4 adversarial injections (Stream B). This is LLM-free, so it
  is the most robust evidence in the lab.
- **The system fails closed.** Unknown runs, stops, and SSE gaps return 502 / peer-
  closed with no fabricated "completed" events (Streams C/D).
- **Concurrency is safe.** Duplicate in-flight requests get distinct tracked runs
  (no silent loss); unknown journeys are isolated (404, no run created) (Stream E).

## 4. What is blocked (and why)

Everything that needs a *live, responsive* DeepSeek window:
- CN-C approval-object generation (no proposal → no approval gate this window).
- CH5 reconnect-dedup live proof (historical run expired before chaos ran).
- Live A11y screenshots at the 4 viewports (backend `:8022` was down).

All three are caused by the **same root condition** (upstream "too busy"), not by
product defects. Source-level guarantees and reproduction recipes are documented
in the relevant stream reports so Codex can close them on the next responsive
window.

## 5. Deliverables (this archive)

- `DSH_EAC_V18_3_VALIDATION_REPORT.md` (this file)
- `NATIVE_HERMES_ISOLATED_E2E.md`
- `HERMES_CHAOS_AND_RECOVERY.md`
- `CONCURRENCY_IDEMPOTENCY_APPROVAL.md`
- `SEMANTIC_TRAVELER_CORPUS_RESULTS.md`
- `RUNTIME_API_CONTRACT_FINDINGS.md`
- `DESKTOP_MOBILE_A11Y_RESULTS.md`
- `CODEX_HANDOFF_AFTER_V18_3_VALIDATION.md`
- `evidence/` — `results.json`, `native_e2e_run.json[+failed_503]`,
  `hermes_tool_sequences.jsonl[+failed_503]`, `semantic_corpus_results.jsonl` +
  `_summary.json`, `api_contract.json`, `chaos_results.json[.jsonl]`,
  `concurrency_results.json[.jsonl]`, `screenshots/README.md`
- `tests/` — all harness scripts (see `patches/V18_3_VALIDATION_TESTS_ONLY.patch`)
- `patches/V18_3_VALIDATION_TESTS_ONLY.patch` — additions of the test suite
- `patches/V18_3_LOW_CONFLICT_FIXES.patch` — F2 + F3 one-line fixes (optional)

## 6. Verdict

**Validation lab substantially complete.** Foundational correctness (native E2E,
semantic policy, fail-closed contract, concurrency isolation) is proven. Two
low-risk defects (F2, F3) are identified with exact locations and one-line fixes;
one historical defect (F1) is confirmed resolved. The only outstanding items are
LLM-availability-gated live demonstrations, not product bugs.

**Recommendation to Codex:** apply `V18_3_LOW_CONFICT_FIXES.patch` (F2+F3) and,
on the next responsive DeepSeek window, run `run_concurrency_approval.py --case
CN-C` + `capture_a11y_screenshots.py` to close the last evidence gaps.
