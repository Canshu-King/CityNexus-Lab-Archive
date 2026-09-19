# SNAPSHOT_B_RESULTS.md

**Snapshot B:** taken `2026-09-15 13:05:57` (re-taken; first attempt `12:59:23`)
**Path:** `snapshot_b/` (narrow include-list copy of `D:\moodle\CityNexus`, read-only)
**Manifest:** `evidence/snapshot_b.json` (earlier take preserved as `evidence/snapshot_b_prev.json`)
**Delay after Snapshot A:** ~28 minutes

| Property | Value |
|---|---|
| Files copied | 341 |
| `import app.main` | **OK** (`import_status.ok: true`, `missing_symbols: {}`) |
| `app/capabilities.py` sha256_16 | `7e3ff4cb3a85b7b6` — **byte-identical to Snapshot A** |
| Backend test files present | 89 |
| Focused contract suite | **28 passed / 79 failed** — **identical to Snapshot A** |
| OpenAPI parity | **137 / 137, missing 0, extra 0 → `parity_ok = true`** |

---

## 1. The moving baseline produced exactly one delta

A byte-level comparison of the 20 capability-relevant watched paths plus a full file-index
diff:

| File | Change |
|---|---|
| `backend/app/stay_mobility.py` | **changed** — Codex added `traveler_snapshot = refresh_snapshot(...)` and bound `traveler_twin = snapshot_payload(traveler_snapshot)` at line 854, fixing the `NameError` from Snapshot A |
| `backend/citynexus.db` | changed (gitignored, irrelevant) |
| `backend/tests/*` | changed by this lab's own `tools/sync_tests.py` |
| everything else | **byte-identical** |

`backend/app/main.py` was **unchanged** between A and B (mtime `12:37:09`), as was
`app/capabilities.py`, `app/replanning/feasibility.py`, `app/services.py` and
`app/integrations/ai/semantic_compiler.py`.

Snapshot B was re-taken at `13:05:57` (from `12:59:23`) after adding
`frontend/vite.config.ts` to the include list. Before re-taking, the backend and `data/`
trees were verified byte-identical to the 12:59 take, so no measurement was invalidated.

---

## 2. The single most important result of this round

**The `/experience` 500 found at Snapshot A is fixed at Snapshot B.**

| Surface | Snapshot A | Snapshot B |
|---|---|---|
| `GET /journeys/{id}/experience` | **500** (`NameError: traveler_twin`) | **200** |
| `experience_keys` | — | includes `traveler_twin` |
| `experience_mentions_capability` | — | `true` |
| `experience_mentions_review` | — | `false` |

This is the concrete payoff of the two-snapshot protocol: a single-snapshot audit at 12:38
would have filed a P0 that no longer existed 28 minutes later. **Every finding in this round
is reported with the snapshot it was measured against.**

---

## 3. Focused contract suite — unchanged

```
28 passed / 79 failed   (Snapshot A)
28 passed / 79 failed   (Snapshot B)   <- identical outcomes, identical test bytes
```

`tools/sync_tests.py` copies `tests/*.py` into `snapshot_<label>/backend/tests/` and prints a
per-file sha256, so both snapshots execute the *same byte stream*. The identical result
confirms the 79 failures are code properties, not snapshot artefacts.

---

## 4. NEW at Snapshot B — the OpenAPI contract reached parity

| Target | Runtime `(path, method)` | Contract pairs | Missing | Parity |
|---|---|---|---|---|
| `snapshot_a` | 137 | 131 | **6** | FAIL |
| `snapshot_b` | 137 | 137 | **0** | **OK** |
| `main_tree` | 137 | 137 | 0 | OK |

Between A and B the checked-in `contracts/openapi.yaml` gained the 6 capability routes and
closed the gap. `FIXED_IN_CURRENT`. Full detail in `OPENAPI_DRIFT_RESULTS.md`.

---

## 5. A/B probe diff — every delta is the one fix

| Probe | Identical leaves | Differing | Where the differences are |
|---|---|---|---|
| `canonicalization` | 494 / 495 | 1 | `snapshot` metadata only |
| `boundaries` | 661 / 662 | 1 | `snapshot` metadata only |
| `gate_codes` | 110 / 111 | 1 | `snapshot` metadata only |
| `c4_start` | 5 / 7 | 2 | traceback text |
| `c4_gate` | 26 / 28 | 2 | `booking_body` trace id |
| `lifecycle` | — | **11** | **all `experience_*` keys** |
| `commitment_conflict` | — | **12** | **all `experience` surface** |

So: 28 minutes of Codex activity changed exactly one behaviour, on exactly one surface, and
the change was an improvement. Nothing regressed.

---

## 6. Snapshot B is the current tree

`snapshot_b` and the live `D:\moodle\CityNexus` agree on every measurement taken:

- `app/capabilities.py` sha16 `7e3ff4cb3a85b7b6` in both.
- OpenAPI: 137 / 137 pairs, `parity_ok = true` in both.
- Capability / accessibility route surface: `snapshot_b` vs `main_tree` delta = **`[]`**.

**Therefore the label `CODEX_V19_1_IF_AVAILABLE` resolves to the same code as `FINAL_V19`
for every capability-surface finding in this round.** Codex V19.1 did not introduce a new
capability interpreter; it fixed `stay_mobility.py` and the OpenAPI contract. This is stated
explicitly wherever the two labels appear, so no reader mistakes them for independent
observations.

---

## 7. Snapshot B findings that persist

Everything in the delta-target table is unchanged from Snapshot A:

| Target | `STILL_REPRODUCIBLE` at B |
|---|---|
| D1 HARD downgrade guard | 19 |
| D2 clause-local negation / history | 18 |
| D3 duplicate capability codes | 8 |
| D4 walking / rest numerics | 19 |
| D5 rest / nap windows | 6 |
| D6 gate interprets capability | 1 |
| D7 TRAVELER scope | 7 |

Plus the structural findings measured live at B: the C4 generate/select/booking split
(3 code paths, 2 definitions of feasibility), the ARRIVAL-anchored `start` 500, the
"enforced but never compared" numeric limits, the `REST_EVERY_MIN` parameter-key contract
(`{"max_min": 30}` → 201 accepted-but-unenforced vs `{"every_min": 30}` → 422), the
asymmetric evidence semantics (STROLLER/LARGE_LUGGAGE fail open, STEP_FREE_REQUIRED fails
closed), and the single generic client message for every gate reason.
