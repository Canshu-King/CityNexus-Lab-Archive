# Codex Handoff — After V19

**From:** WorkBuddy V19 capability red-team (adversarial traveller / QA / accessibility-truth / planner-correctness / runtime-truth)
**To:** Codex, working in `D:\moodle\CityNexus`
**Date:** 2026-09-15
**Nature of this document:** a fix plan with acceptance criteria. It proposes **no architecture rewrite**. Two of the three proposed changes are additive; the third is a one-line behaviour change.

---

## ⚠️ Update 11:38 — you already started this, and it is not finished

**Read `V19_FIX_DELTA.md` before acting on anything below.**

You landed `backend/app/capabilities.py` (10:53) and touched 12 core files at
10:56–11:19, after the 10:23 baseline this document is written against. The
shape is right — `HARD/STRONG/SOFT`, `TRAVELER/JOURNEY`,
`ACCESSIBILITY_VERIFIED/UNVERIFIED/CONFLICT`, a conservative extractor, a
class-correction rule. Six guards pass. Keep all of it.

Three things are still open, in priority order:

1. **P0 — the backend cannot import.** `app/main.py:66` imports
   `capability_payload`; `capabilities.py` never defines it. Five call sites
   (lines 66, 1843, 1849, 1895, 8152). Ports 8000/5173 are down because of this.
   Expected shape: `capability_payload(session, traveler_id, journey_id=None) -> list[dict]`
   returning `CapabilityItem.as_dict()` rows.
2. **The capability layer is not connected to the gate.** It projects
   `STEP_FREE_REQUIRED` / `AVOID_STAIRS` as `rule_code`, and
   `evaluate_feasibility()` implements none of them, so **82 of 494 cases fail
   closed** with `UNSUPPORTED_HARD_CONSTRAINT`. `accessibility_state()` is
   imported into `feasibility.py` and never called.
3. **Both safety guards are inverted.** `canonicalize_capabilities()` only
   preserves `HARD` when the caller already said `HARD` (18/24 attack cells
   accept a downgrade), and `extract_capabilities_from_text()` returns `()`
   whenever *any* negation marker appears anywhere in the sentence — so
   `没有例外` erases a real need while `I don't need a wheelchair, I can walk`
   creates a fake HARD one and blocks the Journey.

`patches/V19_POSTFIX_CAPABILITY_CONTRACT_TESTS.patch` adds
`tests/test_v19_postfix_capability_contract.py`: **23 fail, 7 pass** against the
current tree. Every failure is one behaviour from the list above.

---

## 0. Read this first

**Nothing in `D:\moodle\CityNexus` was modified.** All work happened in `D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915` against a read-only snapshot (`repo_copy/`, 409 files). The lab ran on ports 8040 / 4193 with its own SQLite database. Ports 8000 / 5173 and the main `citynexus.db` were never touched.

The regression suite is **tests-only** and applies cleanly:
`patches/V19_CAPABILITY_TESTS_ONLY.patch` → `backend/tests/test_v19_capability_redteam.py` (40 tests).

**37 pass, 3 skip** in the red-team environment. The 3 skips are for surfaces this build does not expose (constraint `PATCH`, commitments list, audit endpoint) — they will run once those exist.

**Read the test names before reading anything else.** They encode the findings:

- `test_v19_guard_*` — behaviour that is **correct** and must not regress. A failure here is a real bug.
- `test_v19_char_*` — behaviour that is **defective**. These pass today *on purpose*. When you fix a defect, the matching characterisation test will fail, and that failure is the signal to delete/replace it. **Do not revert the fix to make a characterisation test pass.**

---

## 1. The one-paragraph summary

The product has no traveller-capability domain. There is exactly one accessibility requirement in the 138-item baseline (`NFR-014`) and it is about UI colour and keyboard labels; `step_free` / `wheelchair` / `stroller` / `accessib*` appear **zero** times in `backend/app` and `frontend/src`. The semantic compiler *does* extract capabilities correctly — the live model discriminated hard from soft in **167/167** pairs — but `apply_semantic_policy` never reads `envelope.constraints`, so **85 of 167 pairs collapse** and `capability_path_exists` is `false` for **494/494** live cases. Because no capability rule code is interpretable, the fail-closed gate refuses everything: **98 of 98** field-simulation flows that declared an accessibility need produced no plan, all with the identical message. A capability cannot be declared mid-trip at all, and the only way to lift one is to delete the row.

---

## 2. What must NOT change

Three guards hold today. Each has a lock test. Breaking any of them makes the product worse, not better.

| Guard | Test | Why it matters |
|---|---|---|
| Uninterpretable HARD rules fail closed | `test_v19_guard_f2_*` | the only reason no capability is silently scored away |
| `LEARNED_SOFT` never escalates to a constraint | `test_v19_guard_f13_*` | the twin cannot invent a disability |
| Agent commands and Copilot never mutate constraints | `test_v19_guard_f15_*`, `test_v19_guard_copilot_*` | injection cannot weaken a need |
| Mission preferences stay journey-scoped | `test_v19_guard_f12a_*` | the one scope model that works |
| A paid commitment survives a capability conflict | `test_v19_guard_f7a_*` | money is not silently discarded |

### The trap in the obvious fix

The tempting fix is to add capability codes to the interpreted set in `feasibility.py`:

```python
# DO NOT DO THIS
elif code in {"STEP_FREE_REQUIRED", "MAX_WALKING_PER_LEG_M", ...}:
    ...  # now it passes the gate
```

That converts a **safe refusal** into an **unsafe approval** — because the venue data has no accessibility facts to check against, so the gate would have nothing to evaluate and would pass. **A capability code may only become interpretable once an evidence model exists to interpret it against.** This is the single most important sentence in this document.

---

## 3. Fix plan

Ordered by traveller harm. Each item has a concrete acceptance criterion.

### P0-1 — Introduce a canonical capability concept with an explicit evidence state

**Closes:** F1, F8, F11, and the `capability_path_exists: false` result.

**The core insight:** the missing piece is not a rule code, it is an **evidence state**. The product must be able to say *"this traveller requires step-free access; their evidence for this requirement is UNKNOWN"* — a statement that is different from both *"verified step-free"* and *"no requirement"*.

Minimum shape (names are yours to choose):

```
CapabilityRequirement
  journey_id
  subject            # SELF | COMPANION | CHILD | PARTY
  kind               # STEP_FREE | MAX_WALKING_M | REST_WINDOW | NAP_WINDOW |
                     # QUIET_ENV | LUGGAGE | STROLLER | TOILET_ACCESS
  value              # typed: int metres, {start,end}, bool
  hardness           # HARD | SOFT
  evidence_state     # VERIFIED | UNKNOWN | CONTRADICTED
  evidence_source    # USER_STATED | PROVIDER_FACT | LEARNED_SOFT
  scope              # JOURNEY | TRAVELLER
  active
```

Three things must follow from it:

1. **`apply_semantic_policy` reads `envelope.constraints`.** A constraint-bearing envelope and an otherwise identical constraint-free envelope must not produce the same `SemanticPolicyDecision`. (`test_v19_char_f8b` currently locks the opposite and will fail — that is the intended signal.)
2. **`hardness` is a required, structured field**, not inferred from vocabulary. Today only 14 of 535 model-emitted constraints carried an explicit hardness flag, because `SEMANTIC_ENVELOPE_SCHEMA.constraints` is `additionalProperties: true` with no required slot. Tighten the schema so hardness is a required enum.
3. **`evidence_state` is never defaulted to `VERIFIED`.** Absence of evidence is `UNKNOWN`, and `UNKNOWN` must behave differently from `VERIFIED` and from "no requirement".

**Acceptance:** on the 494-case corpus, `server_canonical_capability` is non-null for at least the 307 cases where the envelope names a capability term (today: 0/494), and pair discrimination rises above 49.1 % toward the model's 100 %.

---

### P0-2 — Make a capability declarable mid-trip

**Closes:** F5 — the traveller-stranding bug. This is the highest-severity item.

Today, on an `ACTIVE` journey:

```
POST /constraints {STEP_FREE_REQUIRED, HARD}
→ 422 Constraint would make the selected plan infeasible:
      UNSUPPORTED_HARD_CONSTRAINT:STEP_FREE_REQUIRED
→ journey stays ACTIVE, plan unchanged, replan candidate_count: 0
```

The traveller is mid-trip, has just disclosed a real need, and has no way forward. The 422 is not even about accessibility — it is about "the selected plan".

**Required behaviour:** a capability disclosed mid-trip is accepted, and the product either (a) produces a re-planned itinerary that satisfies it, or (b) returns an explicit, capability-named conflict naming the obstructing activity. Never a bare 422, and never a silent empty proposal.

**Acceptance:** `test_v19_char_f5_capability_cannot_be_declared_mid_trip` fails (the add is accepted), and a new test asserts that the outcome names the capability.

---

### P0-3 — Surface capability ↔ commitment conflicts explicitly

**Closes:** F7 — including the worst case in the whole red-team.

Measured today:

| Case | Result |
|---|---|
| paid cruise + HARD `STEP_FREE_REQUIRED` | generic 422; commitment correctly survives; **conflict never mentioned** |
| paid cruise + **SOFT** `STEP_FREE_REQUIRED` | **201, 3 plans, cruise still in all 3, nothing said** |

The SOFT case is the dangerous one: the traveller is handed three confident itineraries containing a paid activity they physically cannot reach, and discovers it at the pier.

**Required behaviour:** a capability that conflicts with a `C4_Anchored` commitment produces a response naming **both** — the capability and the commitment. `experience` and `twin` must expose it (`risk_reason_codes` is currently `[]`). The traveller decides; the product does not choose for them.

**Useful precedent in your own codebase:** `"closed activity is protected and cannot be replaced automatically"` is the best error message in the product — it names the *reason*, not just the outcome. The architecture can already explain a protected-commitment conflict. It just has no capability dimension to add.

**Acceptance:** `test_v19_char_f7b_*` and `test_v19_char_f7c_*` fail; new tests assert both names appear.

---

### P1-1 — Read the numeric values

**Closes:** F3. **63 variants → 1 outcome.**

`MAX_WALKING_PER_LEG_M` with `0, 1, 100, 499, 500, 501, 1000, 10 000 000, -5, "500", "500m", null, absent, wrong key, km key` all return the identical 422. Same for `MIDDAY_REST_WINDOW`, `INFANT_NAP_WINDOW`, `MAX_CONTINUOUS_WALKING_MIN`, `REST_EVERY_MIN` across 48 window variants.

Two distinct problems:

- **Values are not read** — the planner cannot tell a 100 m budget from a 10 km one.
- **Types are not validated** — `"500m"`, `null` and a missing key are accepted at `POST /constraints` with `201` and fail only later. A typo and an impossible constraint are indistinguishable.

**Acceptance:** 100 and 10 000 produce different outcomes; malformed values are rejected at add time with a validation error naming the field.

---

### P1-2 — Audit every capability mutation

**Closes:** F6, F16.

The only constraint-adjacent audit action is `constraint.created`. Yet `DELETE` returns `204` and restores planning, and `active=0` silences a HARD capability — both unaudited, both unmentioned in any UI surface. An accessibility requirement can appear, be silenced, or disappear with no reviewable trace.

**Acceptance:** `created` / `updated` / `deactivated` / `deleted` entries naming the capability; `test_v19_char_f6b_*` and `test_v19_char_f16_*` fail.

---

### P1-3 — Resolve negation and history

**Closes:** F9.

Of 56 negated/historical cases the model flagged only 10, none carried a resolved-status constraint, and 25 routed to `PERSONAL_ASSISTANCE`. Even when the flag is right, the policy returns route `UNKNOWN` with no action — a dead end. So a stale HARD capability can never be lifted by language: not *"I don't need the wheelchair any more"*, not *"forget my leg, it's fine this trip"*.

**Acceptance:** `test_v19_char_f9_*` fails; a negation produces an explicit removal action.

---

### P1-4 — Give the traveller a journey-scoped preference surface

**Closes:** F12.

`preferences` has no `journey_id`, and `UNIQUE(traveler_id, category, preference_key)` means a "this trip only" statement does not merely go global — it **overwrites** the traveller's previous value for that key, permanently, for every journey.

**Acceptance:** `test_v19_char_f12b_*` fails; a language-expressed journey-scoped preference is stored with a `journey_id`.

---

### P2-1 — Open a read-only capability channel to the agent

**Closes:** F14b — "Hermes inventing accessibility evidence".

The agent surface is capability-blind in **both** directions. The write direction being closed is **correct** — keep it. The read direction being closed is the problem: an agent asked *"is this trip suitable for my mother who uses a wheelchair?"* has no capability field in `inspect_journey` or `inspect_twin`, so its options are to refuse, to say it doesn't know, or to guess. A capable model with no evidence and a direct question will very often guess.

**Acceptance:** a read-only capability block on an existing tool (or a new `inspect_capability`), returning needs **with their evidence state**. No write tool. Lock the write boundary with a test.

---

### P2-2 — Fix the two agent contract mismatches

**Closes:** F17.

- `MCPToolCall.__init__() missing 1 required positional argument: 'agent_id'` — the object cannot be constructed from its call path.
- `POST /api/v1/agent/tools/v2/{tool}` rejects the documented `{request_id, arguments}` payload with `"Extra inputs are not permitted"`. All three tools tried (`request_replan`, `request_commitment_change`, `inspect_twin`) failed identically.

**Acceptance:** `MCPToolCall` is constructible; the documented payload is accepted, or the descriptor is corrected to match the endpoint.

---

## 4. Fix order, and why

```
P0-1  canonical capability + evidence state     ← everything else depends on this
  ↓
P0-2  mid-trip declaration                      ← stops the stranding
  ↓
P0-3  conflict disclosure                       ← stops the dangerous SOFT case
  ↓
P1-1  typed values          P1-2  audit         ← parallel; both feed P0-1
P1-3  negation resolution   P1-4  journey scope
  ↓
P2-1  agent read channel    P2-2  contract fixes
```

Do **not** start at P0-2 or P0-3. Without P0-1 there is no `hardness` field and no `evidence_state`, so a mid-trip re-plan would have nothing to satisfy and a conflict report would have nothing to name.

---

## 5. Requirement baseline gap

The fix cannot be verified against the current baseline, because the baseline does not ask for it. `NFR-014` is the only accessibility requirement and it is about UI colour and keyboard labels. There is **no** requirement for step-free routing, walking limits, rest windows, infant naps, strollers, luggage, quiet environments, toilet access, or conflicting family needs.

**Recommendation:** add the capability requirements before or alongside the code. Without them there is no acceptance criterion to test against, and no way to tell a correct implementation from a plausible one. Suggested shape (IDs are illustrative):

- `FR-062` Traveller capability declaration with evidence state
- `FR-063` HARD capability feasibility enforcement
- `FR-064` SOFT capability deviation disclosure
- `FR-065` Capability ↔ commitment conflict disclosure
- `FR-066` Mid-trip capability change and recovery
- `NFR-017` Capability evidence provenance and audit
- `NFR-018` Capability scope (journey vs traveller)

All 138 existing requirements are `status: proposed`. Whatever you add will be the first capability requirement in the project.

---

## 6. Suggested minimal first commit

If you want the smallest change that reduces traveller harm today:

1. `apply_semantic_policy` reads `envelope.constraints` and sets `verify_evidence = True` whenever a constraint names an accessibility term with no evidence. This alone stops the Copilot from calling a wheelchair requirement "a preference request".
2. Add `hardness` as a **required** enum on the constraint schema (no new domain model needed).
3. Return the capability rule code in the generate-time 422 message.

None of these touch the fail-closed gate, and none require the capability domain to exist yet.

---

## 7. Environment notes for reproducing the run

| Item | Value |
|---|---|
| Lab root | `D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915` |
| Snapshot | `repo_copy/` (read-only copy; `BASELINE_SOURCE.txt` records the source) |
| Backend | port **8040**, `CITYNEXUS_DATABASE_URL=sqlite:///…/v19_redteam.db` |
| Frontend | port **4193**, `vite.v19-local.config.ts`, `cacheDir` in `%TEMP%` |
| Servers | `tools/start_lab_servers.py` (note: children die if the launching process exits — start them as persistent background tasks) |
| Tests | `CITYNEXUS_DATABASE_URL=sqlite:///…/v19_tests.db pytest tests/test_v19_capability_redteam.py` |
| Corpus | `tools/v19_semantic_corpus.py` → 494 cases |
| Live run | `tools/v19_run_semantic_live.py` (reads the credential from `HKCU\Environment` via `winreg`; never prints it) |
| Field sim | `tools/v19_field_simulation.py` → 168 flows, ~19 min |
| Runtime | `tools/v19_web_mobile_truth.mjs` → 64 cells + axe |

### Two traps worth knowing

1. **The host runs a system proxy** (U1S1 Cloud on `127.0.0.1:7892`). Playwright's Chrome inherits it and routes loopback requests through it, which hangs or returns 502. Launch with `proxy: { server: "direct://" }` and `--no-proxy-server`.
2. **`/v8/<route>` renders the onboarding form until a journey is selected.** The selection lives in `localStorage` (`citynexus.v8.journey_id`). Without seeding it first, all 8 routes render the same screen and a runtime review measures nothing. The script now bootstraps via the "Use the sealed Tianjin demo" button and reuses `storageState`.

---

## 8. Honest limitations of this red-team

- **Hermes was not live** (`configured: false, ready: false`). F14 and F17 are structural findings that need a live run to confirm.
- **`candidate_count` was `0` on every replan**, including the control case with a supported HARD constraint. The recovery engine produced nothing in this environment, so the *quality* of a recovery proposal could not be assessed — only its absence.
- **No accessibility requirement exists to test against**, so every capability finding is "the product does X", not "the product should have done Y". The baseline is the missing yardstick (§5).
- **11 of the 12 destinations have no place catalog** in this environment, so their flows exercise the refusal path. That is itself a result, but it means cross-city planning quality was not assessed.
- **The 3 skipped tests** cover surfaces this build does not expose; they will run once those exist.
