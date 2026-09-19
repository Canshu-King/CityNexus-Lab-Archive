# TEST_RESULTS.md — CityNexus V19.2.3 Final Shadow-Trial Code Gate

Every number below is copied from real output produced by this round.
No status prose is carried over from any earlier package.

## Environment

| Item | Value |
| --- | --- |
| Repository | `D:\moodle\CityNexus` |
| Branch | `eac/v19.2.2-realphone-codegate` (continues; no new branch needed) |
| Snapshot E | `CityNexus-EAC-V19.2.2-RealPhone-CodeGate-Final-20260915.zip`, frozen with a SHA-256 manifest (`evidence/SNAPSHOT_E_MANIFEST.json`, 47 files) |
| Declared baseline | V19.2.1 package, **line endings normalised to LF** before diffing (see `PATCH_RESULTS.md`) |
| Python | 3.12.14 (`D:\moodle\CityNexus\.venv`) |
| pytest | 8.4.2, `-p no:cacheprovider` |
| AI | `CITYNEXUS_AI_ENABLED=false` for every deterministic run; one live canary is reported separately |

## 1. Gate suites — PASS

```
tests/test_v192_shadow_trial_gate.py   61 passed   (the V19.2 contract, unchanged)
tests/test_v1923_final_code_gate.py    13 passed   (new closure regression tests)
                                       -----------
                                       74 passed
```

Evidence: `evidence/v1923_gate_run.txt`.

## 2. Authoritative broad backend regression — PASS

Command: `python -m pytest tests/ -q -p no:cacheprovider` (authoritative
`backend/tests` root only).

| Run | Result |
| --- | --- |
| V19.2.2 (Snapshot E) | 2 failed, 671 passed, 15 skipped |
| V19.2.3 (this round) | **2 failed, 684 passed, 15 skipped** |

```
new regressions vs V19.2.2 : 0
net change                 : +13 passing (the new V19.2.3 tests)
remaining failures         : 2 (both pre-existing contradictory pairs)
```

Evidence: `evidence/broad_regression_head.txt`,
`evidence/broad_regression_v1922_failures.txt`,
`evidence/broad_regression_v1923_failures.txt`.

### 2.1 The two remaining failures are the same contradictory pairs

Unchanged from the V19.2.2 review, and both fail on the untouched V19.2.1
baseline:

* `test_v191_eac_defect_nonsense_walking_limit_is_rejected[走路不能超过 0 米]`
  requires `max_m is None or >= 1`; `test_v191_defect_d4_walking_limit_is_parsed_with_its_value[走路不能超过 0 米-0]`
  requires `max_m == 0`. Mutually exclusive on one input. The upstream V19.2
  contract is satisfied by keeping the parsed value with
  `needs_clarification = true` at `STRONG` severity.
* `test_v19_char_d6b_hard_accessibility_need_does_not_block_planning` requires
  the gate to pass on a Place with **no** accessibility evidence, which
  contradicts `test_v19_traveler_capability.py::test_feasibility_blocks_unknown_and_conflicting_step_free_evidence`
  and the V19.2 route-evidence guards. Production truth was not weakened.

Per the Road-Prep guidance these obsolete expectations are **not** "fixed" by
changing production truth; they remain a documented test-maintenance item.

## 3. OpenAPI

```
OpenAPI 3.1.0; formal 138; runtime 138; missing 0; extra 0
```

Path parity holds with the new governed-acknowledgement endpoint registered.
Evidence: `evidence/openapi_parity.txt`.

## 4. Frontend build

```
npm run build   -> ✓ built (vite 7.3.6), no errors
openapi-typescript regenerated src/generated/api.ts from the updated contract
```

## 5. Focused mobile trial — 390x844 and 430x932

18 flow runs (2 viewports × 9 flows). **0 page errors, 0 horizontal overflow.**

| Flow | 390x844 | 430x932 |
| --- | --- | --- |
| ARRIVAL boundary | no flexible activity before arrival | same |
| DEPARTURE boundary | no flexible activity after departure | same |
| Mid-trip HARD recovery | panel visible, governed label | same |
| Acknowledge warning | backend 200, `resolved=false`, banner still visible, `needs_review=true` | same |
| No alternative | `RECOVERY_REQUIRED_NO_ALTERNATIVE`, `replan_attempted=true` | same |
| Feasible replacement resolves | recovery `null`, `needs_review=false`, panel gone | same |
| Stale candidate warning | `stale=true`, `selectable=false`, start 409, panel visible | same |
| GPS allowed | rendered, no overflow | same |
| GPS denied | rendered, no overflow | same |

Evidence: `evidence/mobile_v1923_d.json`.

## 6. Live DeepSeek semantic canary — PASSED

One bounded live canary through the real primary semantic compiler, using the
`DEEPSEEK_API_KEY` present in the user's environment. The key was never printed
and is not present anywhere in this package.

| Input | Live result | Local fallback |
| --- | --- | --- |
| `I don't need a wheelchair, I can walk.` | no capability, assertion `NEGATED` | no capability |
| `I need step-free access for this trip.` | `STEP_FREE_REQUIRED` HARD | identical |
| `走路不能超过 1.5 公里。` | `MAX_WALKING_PER_LEG_M` `max_m=1500` | identical |

Live and local fallback agree on all three. Evidence:
`evidence/live_deepseek_canary.json`.

## 7. Not performed / not claimed

* **No real payment** was executed.
* **No physical-device testing** was performed. All mobile evidence is emulated
  viewports in headless Chrome and does not establish real-phone behaviour.
* The live canary is one bounded semantic call, not a full live-provider trial.
