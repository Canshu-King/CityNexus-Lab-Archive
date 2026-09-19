# Evidence manifest — V19.2 Real-Phone Shadow-Trial Gate

Every artifact below was produced by a script in `tools/` against a byte-copy of the main tree.
Nothing in this list required write access to `D:\moodle\CityNexus`.

## Snapshots

| Path | Taken | Contents |
|---|---|---|
| `snapshot_a/` | 2026-09-15 **17:29:11** | 341 files, `import app.main` OK, `capabilities.py` `23,668 B` / `9b68b17997f4cf4e` |
| `snapshot_b/` | 2026-09-15 **17:50:44** | 341 files, `capabilities.py` byte-identical to A |

Produced by `python tools/snapshot.py A` / `python tools/snapshot.py B`.
The per-file hash ledger is `evidence/snapshot_a.json` and `evidence/snapshot_b.json`; the drift
analysis is `SNAPSHOT_AND_DELTA_RESULTS.md`.

## Capability-layer probes (pure, no HTTP)

| Artifact | Command | Read by |
|---|---|---|
| `evidence/capability_semantics_a.json` | `python tools/v192_probe_capability_semantics.py A` | `CAPABILITY_SEMANTICS_RESULTS.md`, `P0_GATE_TABLE.md` groups 3–5 |
| `evidence/p0_numeric_a.json` | `python tools/v192_probe_p0_numeric.py A` | `NUMERIC_TIME_BOUNDARY_RESULTS.md`, gates 3.3 / 5.1 / 5.2 |
| `evidence/_cross/p0_numeric_b.json` | `V192_LAB=… V192_EVID=… python tools/v192_probe_p0_numeric.py B` | cross-snapshot comparison |
| `evidence/_cross/p0_numeric_c.json` | same, against the V19.1 lab | before/after delta |
| `evidence/cross_snapshot_numeric.json` | `python tools/v192_cross_snapshot_numeric.py` | `NUMERIC_TIME_BOUNDARY_RESULTS.md` |
| `evidence/corpus_delta_c_to_a.json` | `python tools/v192_corpus_delta.py` | `REGRESSION_LIST.md` (120-case differential) |
| `evidence/_cross/lifecycle_c.json` | `V192_LAB=… python tools/v191_probe_lifecycle.py C` | V19.1 baseline for the over-filtering regressions |

Root-cause traces (supporting, not referenced by a gate):

| Command | What it isolates |
|---|---|
| `python tools/v192_probe_km_anomaly.py` | `1.5 km` → `max_m: 1` in isolation |
| `python tools/v192_probe_km_trace.py` | the clause split that destroys `1.5` before the parser sees it |

## HTTP lifecycle probes (in-process `TestClient`, throwaway SQLite)

| Artifact | Command | Read by |
|---|---|---|
| `evidence/c4_lifecycle_a.json`, `_b.json` | `python tools/v192_probe_c4_lifecycle.py A\|B` | `C4_ANCHOR_AND_IDEMPOTENCY_RESULTS.md`, gates 1.2 / 1.3 / 2.x |
| `evidence/c4_start_a.json` | `python tools/v191_probe_c4_start.py A` | the 6-case anchor matrix in the main report §3 |
| `evidence/stale_candidates_a.json`, `_b.json` | `python tools/v192_probe_stale_candidates.py A\|B` | `MIDTRIP_AND_STALE_LIFECYCLE_RESULTS.md`, gates 7.3 / 7.4 |
| `evidence/feasibility_truth_a.json`, `_b.json` | `python tools/v192_probe_feasibility_truth.py A\|B` | `FEASIBILITY_TRUTH_RESULTS.md`, gate 1.1 |
| `evidence/lifecycle_a.json` | `python tools/v191_probe_lifecycle.py A` | gates 3.1 / 6.1–6.4, 4.6 |

The throwaway databases live in `evidence/_db/` (`snapshot_a.db`, `snapshot_b.db`,
`web_lab_a.db`). They are lab artifacts and are excluded from the deliverable zip.

## Contract

| Artifact | Command | Result |
|---|---|---|
| `evidence/openapi_drift.json` | `python tools/v191_probe_openapi_drift.py` | 4 targets; V19.2 snapshot and the live main tree both `parity_ok=True`, `missing=0 extra=0` |

## Mobile / web trial flow

| Artifact | Command | Contents |
|---|---|---|
| `evidence/web_mobile_results.json` | `node tools/v191_web_mobile.mjs` | 8 routes × 4 viewports × 2 reduced-motion = 64 cells, 0 page errors, 0 horizontal overflow |
| `evidence/web_mobile_summary.json` | (written by the same run) | aggregate counts |
| `evidence/web_mobile_zoom200.json` | same run | 200% zoom pass over all 8 routes |
| `evidence/web_mobile_focus.json` | same run | focus-ring visibility, colour-only-state check |
| `evidence/web_mobile_capability.json` | same run | capability probe driven through the real backend (`declare_hard_unknown_evidence` → 200, `items=1 hard=1`) |
| `evidence/web_mobile_bootstrap.json` | same run | lab bootstrap record |
| `evidence/screenshots/` | same run | 72 PNG — the 64-cell matrix plus 8 at 200% zoom |

Requires the lab servers on `127.0.0.1:8060` (uvicorn) and `127.0.0.1:4213` (Vite), started by
`tools/start_web_lab.py`. Read `WEB_MOBILE_RESULTS.md` for the a11y gap counts
(248 nameless status nodes, 40 unlabelled controls, 24 clipped text nodes — none trial-blocking).

## Test suites

| Command | Result |
|---|---|
| `cd backend && pytest tests/test_v191_capability_contract.py tests/test_v19_postfix_capability_contract.py tests/test_v191_eac_evidence_scope.py -q` | 14 failed / 161 passed / 13 skipped |
| `cd backend && pytest tests/test_v192_shadow_trial_gate.py -q` | **24 failed / 37 passed** (all failures are `test_v192_defect_*`) |
| both together | 38 failed / 198 passed / 13 skipped |

Test sources are synced into the snapshots with `python tools/sync_tests.py A|B`, so the identical
bytes run against every snapshot.

## Patch

| Artifact | Command |
|---|---|
| `patches/V19_2_TESTS_ONLY.patch` | `python tools/v192_make_tests_patch.py` |
| apply check | `cd _scratch/patchcheck_v192b && git -c core.autocrlf=false apply --check ../../patches/V19_2_TESTS_ONLY.patch` → **PASS** |

## Method notes (also in `SNAPSHOT_AND_DELTA_RESULTS.md`)

1. `importlib.import_module` caches by dotted name — loading three snapshots in one process returns
   the **same** module unless `sys.modules` is cleared first. `v192_cross_snapshot_numeric.py`
   clears `app` / `app.*`, asserts `__file__` is under the intended snapshot, and pins the module to
   keep it alive.
2. Every Python invocation carries `PYTHONDONTWRITEBYTECODE=1`; a read-only snapshot is verified
   against the main tree by hash, not by timestamp.
3. Two snapshots may only be compared on files present in **both**.
4. `curl` against `127.0.0.1` needs `--noproxy '*'` on this host (system proxy intercepts loopback);
   Playwright is forced direct.
5. The lab's own servers are independent long-running background tasks — a launcher process exiting
   takes its children with it.
