# TEST_RESULTS.md — CityNexus V19.2.5 C4 Interior-Truth Hotfix

Every number is copied from real output produced by this round.

## Environment

| Item | Value |
| --- | --- |
| Repository | `D:\moodle\CityNexus` |
| Snapshot G | `CityNexus-EAC-V19.2.4-FinalTruth-CodeGate-20260915.zip`, SHA-256 `b6c521c1163791146bdf0989bca0d40f61c2c865862eabe6156274a7eeb0b017` (matches the independent review) |
| Baseline for the hotfix patch | Snapshot G |
| Python / pytest | 3.12.14 / 8.4.2, `-p no:cacheprovider` |
| AI | `CITYNEXUS_AI_ENABLED=false`; no canary (no semantic code touched) |

## 1. Gate suites — PASS

```
tests/test_v192_shadow_trial_gate.py    61 passed   (V19.2 contract)
tests/test_v1923_final_code_gate.py     13 passed   (V19.2.3 closure)
tests/test_v1924_final_truth_gate.py    12 passed   (V19.2.4 truth)
tests/test_v1925_c4_interior_truth.py    7 passed   (V19.2.5 hotfix)
                                       -----------
                                        93 passed
```

Evidence: `evidence/gate_suites_run.txt`.

## 2. Shared-gate probes — PASS

| Probe | Result |
| --- | --- |
| `v1925_c4_interior_probe.py` | **5/5 PASS**, exit 0 |
| `v1924_truth_probe.py` (regression) | **4/4 PASS**, exit 0 |

Evidence: `evidence/v1925_c4_interior_probe.json`,
`evidence/v1924_truth_probe_regression.json`.

## 3. Authoritative broad backend regression — PASS

Command: `python -m pytest tests/ -q -p no:cacheprovider`.

| Run | Result |
| --- | --- |
| Snapshot G (V19.2.4) | 2 failed, 696 passed, 15 skipped |
| V19.2.5 | **2 failed, 703 passed, 15 skipped** |

```
new regressions : 0
net change      : +7 passing (the new V19.2.5 tests)
remaining       : 2 (the same pre-existing contradictory pairs)
```

Evidence: `evidence/broad_regression_head.txt`,
`evidence/broad_regression_failures.txt`.

### 3.1 The two remaining failures

Unchanged and pre-existing on the untouched V19.2.1 baseline:

* `test_v191_eac_defect_nonsense_walking_limit_is_rejected[走路不能超过 0 米]`
  versus `test_v191_defect_d4_walking_limit_is_parsed_with_its_value[走路不能超过 0 米-0]`
  — mutually exclusive on one input.
* `test_v19_char_d6b_hard_accessibility_need_does_not_block_planning` versus the
  V19/V19.2 evidence-negative guards — mutually exclusive on one fixture.

Production truth was not weakened to satisfy them.

## 4. Patch portability — PASS

```
git apply --check V19_2_5_HOTFIX.patch   # against reconstructed exact Snapshot G
-> exit 0, no excluded paths
git apply -> clean
post-apply file -> byte-identical to the working tree
```

Evidence: `evidence/patch_verification.txt`.

## 5. Deliberately not run

Per the EAC task this is a one-file backend gate hotfix:

* **frontend build** — not re-run (no frontend file changed)
* **OpenAPI parity** — not re-run (no endpoint or schema changed)
* **mobile UI flows** — not re-run (no UI file changed)
* **DeepSeek canary** — not run (no semantic/AI code changed)

The task explicitly said not to spend time on these unless the hotfix changed
them, and it does not.

## 6. Not performed / not claimed

* **No real payment.**
* **No physical-device testing.** The OPPO plumbing precheck (HTTPS/PWA/GPS/SSE)
  is a separate parallel activity performed by the user and is not claimed here.
* A full multi-anchor outdoor Shadow Journey must not be called accepted until
  the independent Snapshot-G/H delta gate agrees.
