# CODEX_MERGE_AFTER_V15

Handoff for the Codex session working in `D:\moodle\CityNexus`.
Written so you can act **without reading the WorkBuddy chat transcript**.

WorkBuddy isolated workspace:
`D:\moodle\CityNexus-Tools\WorkBuddy-V15-NightLab-20260914`
Baseline used: the V14 Trial-Readiness snapshot
(`_v14_trial_release_stage_20260914_012126`, 2026-09-14 01:21).
The main worktree was **never modified**.

---

## 1. Findings already stably reproduced by tests

All of these are green-on-arrival `xfail` rows in
`backend/tests/test_v15_copilot_v14_gaps.py` and
`backend/tests/test_v15_cross_city_genericity.py`. Each has a named reason
string, so `pytest -rxX` lists them as the V15 worklist.

| # | Finding | Evidence | Test |
|---|---|---|---|
| G1 | Every free-text command ≥8 chars fabricates a `WEATHER` Event, whatever the intent | `evidence/v14_command_probe.json` | `test_{explain,discover,preference,hypothetical,override}_*_creates_no_event` |
| G2 | `command: min_length=8` rejects short Chinese outright — including **real** disruption reports (`前方封路了。`, `现在正在下雨。`) | same | `test_short_*_is_accepted / _is_not_dropped` |
| G3 | The traffic token list misses `封闭`/`道路封闭`, so a real closure becomes `WEATHER` | same | `test_road_closure_is_traffic_not_weather` |
| G4 | zh and en expressions of the same intent diverge (zh 422, en fabricates an event) | same | `test_zh_and_en_preference_have_the_same_event_decision` |
| G5 | Copilot locale = `"zh" if timezone.startswith("Asia/") else "en"` → Singapore (SGD/en) and Tokyo (JPY/ja) get **Chinese** replies | `evidence/cross_city_probe.json` | `test_non_chinese_asian_journey_does_not_get_a_chinese_reply` |
| G6 | `affected_place_hint` injects the Tianjin literal `海河沿线` into **any** journey containing "river" | same | `test_london_journey_does_not_receive_a_tianjin_place_hint` |
| G7 | `_MONEY_PATTERN` misses the English word "budget"; the currency suffix is optional and CNY-only | same | `test_english_budget_keyword_is_recognised` |
| G8 | Mission budget bound is a currency-less int scaled ×100 → 100× inflation for JPY | `backend/app/agent/mission.py` | `test_mission_cost_bound_carries_a_currency`, `test_jpy_bound_is_not_scaled_as_if_it_had_two_decimals` |

Frontend (not covered by pytest, see `FRONTEND_UX_REVIEW.md`):
one AI-desk message creates **2 missions + 1 fake event**; `money()` always
divides by 100 and ~15 call sites hardcode `"CNY"`; `AgentComposer` disables
submit below 8 characters; only `en`/`zh-CN` locales exist; no confirmation UI.

A **live browser trial** (Chromium, real backend, isolated on 8013/4173 — see
`FRONTEND_UX_REVIEW.md` Part 2) confirmed the two headline items in the actual UI
and added four cheap fixes:

* **Duplicate language control.** `V8Experience.tsx:678` and `:924` both render an
  unconditional language button, both with `aria-label="Switch language"`. On the
  Journey Hub at desktop width the user sees two identical "中文" buttons, and a
  screen reader sees two controls with the same accessible name.
* **`trigger_event_id` is `null`** on a mission whose triggering message did
  produce a matching Event, so the audit chain event → mission is broken.
* **A statement is compiled into a preference.** `现在正在下雨了。` yields
  `preferences: { indoor: true }`. Reasonable as an inference, but it means a
  disruption report and a comfort preference become the same object.
* **`confidence: 1.0` from a deterministic fallback**
  (`compiler.provider_key: "deterministic"`, `model_key: "mission-compiler-v2-fallback"`).
  A fallback should not advertise certainty.
* **No `tsconfig.json` anywhere**, no `typecheck` script, and `build` is
  `vite build` (esbuild strips types without checking). 41 TS/TSX files are
  therefore never type-checked. Adding a tsconfig plus `tsc --noEmit` in front of
  `build` is the cheapest way to catch this whole class of bug.

| G9 | `/api/v1/health` hardcodes `"ai": "disabled"` regardless of configuration — the field cannot be used as a readiness probe | `backend/app/main.py:440` | not covered; one-line fix |

G9 is small but worth taking while you are in the file: a deployment that has
`CITYNEXUS_AI_API_KEY` set still reports `ai: disabled`, so nothing can tell a
working Copilot from a dead one without making a real request. The health
endpoint already has the real signal available (`settings.ai_api_key`,
`settings.ai_enabled`) — it just does not consult it.

## 2. `V15_COPILOT_TESTS_ONLY.patch` — what it touches, and conflict risk

```
backend/tests/_v15_semantic_cases.py                    | 143 +
backend/tests/v15_copilot_helpers.py                     |  89 +
backend/tests/test_v15_copilot_semantic_contract.py      | 205 +
backend/tests/test_v15_copilot_authority_boundary.py     | 146 +
backend/tests/test_v15_copilot_v14_gaps.py               | 172 +
backend/tests/test_v15_cross_city_genericity.py          | 168 +
backend/tests/test_v15_semantic_contrast.py              | 233 +
7 files changed, 1156 insertions(+)
```

**Conflict risk: none.** Every hunk is a new file (`new file mode` ×7,
`--- /dev/null` ×7). No existing file is touched, so the patch cannot collide
with any edit you have made in the main worktree.

Verified twice:

1. `git apply --check` against a pristine copy of the V14 baseline → clean, 7/7.
2. Applied to a full pristine copy of `backend/`, then ran the suite:
   * with **no** router present → **`27 passed, 2 skipped, 18 xfailed`**
     (the 2 skips are the two `importorskip` modules);
   * with the optional router also applied → **`118 passed, 2 skipped, 18 xfailed`**.
   Green either way, with **no** V15 product code required.

```bash
# from the repo root
git apply patches/V15_COPILOT_TESTS_ONLY.patch
cd backend && python -m pytest tests/test_v15_copilot_*.py tests/test_v15_cross_city_genericity.py tests/test_v15_semantic_contrast.py -q -rxX
```

### 2b. Why there is a 7th file: `test_v15_semantic_contrast.py`

The 213-case benchmark measures *absolute* accuracy, and absolute accuracy hides
a specific failure mode. A router can score 99 % overall while collapsing the two
cases the V15 brief explicitly names. So this file asserts **deltas**: each of its
20 pairs shares almost all of its surface form and differs only in the feature
that decides whether the traveller is asking a question or reporting a fact.

It caught a real semantic error that the 213-case benchmark had missed:

> `游船取消了。` → `REPLAN_REQUEST` instead of `DISRUPTION_REPORT`.

`取消` sits in both the replan and disruption vocabularies, and the Chinese
perfective particle `了` was not treated as evidence that something has actually
happened. This is the wrong side of the Guardian boundary — a *report* may open a
mission, a *request* may not — so it is worth a deterministic rule rather than a
wider vocabulary. See §4 for the exact change.

Because the pairs are inline constants, this file has **no data dependency** on
the benchmark JSONL and will run in your worktree unchanged.

## 3. Which tests will pass / fail on your current implementation

| group | file | today |
|---|---|---|
| Guarantees V14 already honours (12 tests) | `test_v15_copilot_authority_boundary.py` | **pass** |
| Contract for the not-yet-existing router (48 tests) | `test_v15_copilot_semantic_contract.py` | **skip** — `pytest.importorskip("app.agent.semantic_router")` |
| Minimal-pair deltas (45 tests) | `test_v15_semantic_contrast.py` | **skip** — same `importorskip` |
| V14 defects (12 tests) | `test_v15_copilot_v14_gaps.py` | **xfail**, named |
| Cross-city guarantees + leaks (10 + 6 tests) | `test_v15_cross_city_genericity.py` | **pass** / **xfail** |

Nothing in the patch fails red on arrival. When you fix a gap, its marker turns
into `XPASS`; promote that test into
`test_v15_copilot_authority_boundary.py` and delete the marker in the same commit.

The contract file starts exercising itself the moment `app.agent.semantic_router`
exists — no other change needed.

## 4. Optional reference patch — what to take, what to leave

`patches/V15_REFERENCE_IMPLEMENTATION_OPTIONAL.patch` adds one file:
`backend/app/agent/semantic_router.py` (575 lines).

**It is not a mandate. It does not need to replace anything you have written.**
It exists so the contract tests have something to run against, and to quantify a
design choice. Measured on the same 213-case benchmark:

| metric | DeepSeek V4 Flash alone | reference router |
|---|---|---|
| intent agreement | 92.5 % | 99.1 % |
| event-boundary agreement | 99.1 % | 100 % |
| authority-override escapes | 2 | 0 |

### Worth taking

* **`resolve_locale(context)`** — fixes G5 with a declared-locale → timezone-map
  → default chain. Small, self-contained, directly testable.
* **The deterministic policy split in `_resolve_policy`** — resolve the intent,
  then *recompute* `mutation_policy` / `requires_confirmation` /
  `creates_real_event` server-side, and re-assert them as hard guarantees at the
  end of `route()` so nothing upstream can bypass them. This is the single
  highest-value idea in the patch.
* **`detect_foreign_city(text, context)`** — a deterministic cross-journey check
  against `JourneyContext.city_code`. Cheaper and more auditable than trusting
  the model; the model already gets this right 7/7, so use it as a backstop.
  Note it compares against the **canonical** code (`CN-FUZHOU`), so any caller
  that passes a short alias silently downgrades the route — worth an assertion.
* **The `STRONG_PRESENT` / `CAUSAL` / `HARD_REPORT` framing split** — this is what
  separates `游船因为大风取消了。` (report) from `帮我取消游船。` (request) and
  from `prefer 室内，因为 may rain` (preference). Reuse the idea even if you
  rewrite the code.
* **`COMPLETED_ASPECT` (the Chinese perfective `了`).** Added late, and the most
  subtle rule in the file. `取消` is both "cancel it" and "it was cancelled"; the
  only surface difference is the completion particle. Without it, `游船取消了。`
  is read as a request to cancel, which is the wrong side of the Guardian
  boundary. If you take one rule from this file, take this one.
* **`REPLAN_PREFERENCE_COLLISIONS`.** `省钱` belongs to both vocabularies:
  `我想省钱一点。` is a preference, `我想省钱，但不想取消游船。` is a replan
  request. Resolve it by ignoring the colliding marker *unless some other,
  unambiguous replan marker is also present* — rather than by picking a winner
  and getting one of the two wrong.
* **Word-boundary matching for ASCII markers.** Plain substring matching made
  the marker `down` fire inside `breakdown`. CJK markers must stay
  substring-based. Two rules, not one — this cost 20 points of accuracy to find.

### Do not take

* **The marker vocabularies as a whole.** They are tuned to this 213-case
  benchmark and will not generalise. Treat them as a starting point and expect to
  replace them with a locale-aware vocabulary you own.
* **The `confidence` numbers.** They are hand-assigned constants, not calibrated
  probabilities. Do not gate any product behaviour on them.
* **The `route()` signature verbatim** if your V15 API already differs. The
  contract test documents the interface it expects; if you choose a different
  shape, update `test_v15_copilot_semantic_contract.py` in the same commit and
  keep the guarantees.
* **Any suggestion that this replaces the Guardian, the solver, the commerce
  layer or the recovery runtime.** It only classifies a message.

## 5. Cross-city timezone / currency / city leakage — confirmed

Yes, with reproducible evidence:

* **Locale (G5).** Singapore and Tokyo get Chinese copilot replies. London
  correctly gets English. Root cause is one line in `main.py`.
* **Tianjin place hint (G6).** A **London** journey reporting
  `The river is flooding near the pier.` gets `affected_place_hint = "海河沿线"`.
* **Currency (G7/G8 + UI).** Budget bounds are currency-less ints scaled ×100;
  the frontend hardcodes `"CNY"` at ~15 sites and always divides by 100, so a
  ¥80,000 Tokyo stay budget renders as `¥800`.
* **Not leaking:** `journey.timezone`, `journey.currency` and `journey.city_code`
  round-trip correctly for all five cities, and
  `wrong_city_replay_blocked` holds for every non-Tianjin city. The storage and
  discovery layers are fine; the copilot and presentation layers are not.

## 6. Where DeepSeek V4 Flash is stable, and where you need a deterministic guard

**Stable — let it decide, or trust it as a backstop:**

| behaviour | measured |
|---|---|
| separating a hypothetical from a real report | **29/29** |
| separating a preference from a disruption | **28/28** |
| detecting a real present-tense disruption | **27/27** |
| rejecting a wrong-journey reference | **7/7** |
| refusing a payment/cancel without confirmation | **6/7** |

**Unstable — server must own it:**

| behaviour | measured | required rule |
|---|---|---|
| classifying an authority-transfer phrase ("你觉得合适" / "you decide") | 21/23 | deterministic vocabulary → `REJECT_OVERRIDE` |
| deciding whether a budget change needs confirmation | 12/15 | deterministic: a budget change is always high impact |
| choosing between preference / replan / constraint-conflict | 42.9 % | **merge the handling** — treat all three as "propose options, mutate nothing" |
| emitting a JSON reply on a long prompt | — | `DeepSeekResponsesClient` never sets `max_output_tokens`; reasoning can consume the whole budget and return **empty text on HTTP 200**. Set it, and retry at a lower effort |

One more: when an override is rejected on a message that also carries a
high-impact verb, **keep `requires_confirmation=True`**. The model does this
(`CNX-V15-0183`); the reference router does not. The model's behaviour is better
— it leaves a legitimate gated path instead of a flat refusal.

## 7. Suggested merge order (8 items, highest value first)

1. **Delete the fabricated event.** In `run_agent_command`, stop constructing an
   `EventModel` for every free-text command. Route read-only intents to the
   existing `POST /copilot/messages` path, which already creates nothing.
   *Unblocks: G1, and every downstream symptom.*
2. **Replace the length gate.** `AgentCommandRequest.command: min_length=8` →
   "contains at least one letter or CJK character", and drop
   `command.trim().length < 8` in `AgentComposer.tsx`.
   *Unblocks: G2, G4, and Chinese input in general.*
3. **Fix the copilot locale** with a `resolve_locale`-style chain.
   *Unblocks: G5.*
4. **Delete the `海河沿线` literal.**
   *Unblocks: G6 — one line, highest damage-to-effort ratio in the list.*
5. **Carry currency with the budget bound** and scale by the currency exponent.
   *Unblocks: G7, G8.*
6. **Add the confirmation surface.** The approval API already exists; render it
   when the semantic layer says `requires_confirmation`. Do this *before* the
   policy starts emitting the flag, or the flag is dropped in the UI.
7. **Make the AI desk call one endpoint.** `submitMission` currently POSTs
   `/agent/commands` and PUTs `/guardian/mission` with the same text → 2 missions
   per message.
8. **Then** wire the semantic layer: deterministic-first, model for the ambiguous
   tail, policy always server-computed (§4).

## 8. What you do not need to redo

* No re-audit of V14 is needed. The baseline was used read-only and only the
  Copilot/Agent/Trial-genericity surface was inspected.
* No full-repo sweep. 643 files were copied, ~20 were read.
* No new provider integration, no OTP/GTFS work, no solver or Guardian changes,
  no Agent framework, no frontend redesign.
* The benchmark (`COPILOT_SEMANTIC_BENCHMARK.jsonl`, 213 cases) is reusable as-is
  for regression once the semantic layer lands. Point
  `CNX_V15_BENCHMARK` at it, or leave it at the repo root.

## 9. Artifact index

| file | what |
|---|---|
| `patches/V15_COPILOT_TESTS_ONLY.patch` | **primary deliverable** — 6 new test files |
| `patches/V15_REFERENCE_IMPLEMENTATION_OPTIONAL.patch` | optional reference router |
| `COPILOT_SEMANTIC_BENCHMARK.jsonl` | 213 benchmark cases |
| `COPILOT_BENCHMARK_RESULTS.md` | canary + router scores |
| `CROSS_CITY_GENERICITY_FINDINGS.md` | CC-1…CC-7 |
| `AUTHORITY_RED_TEAM_FINDINGS.md` | 30 authority cases |
| `FRONTEND_UX_REVIEW.md` | UX-1…UX-8 |
| `WORKBUDDY_V15_NIGHT_REPORT.md` | what was done, what was not |
| `evidence/test_results.txt` | raw pytest output |
| `evidence/scenario_summary.json` | machine-readable canary scoring |
| `evidence/*.json`, `evidence/*.jsonl` | raw probe + canary data |
| `tools/v15_benchmark/` | benchmark builder, canary runner, scorers, probes |
