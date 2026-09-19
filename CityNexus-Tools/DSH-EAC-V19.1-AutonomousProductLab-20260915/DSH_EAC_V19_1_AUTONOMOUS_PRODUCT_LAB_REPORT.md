# CityNexus DSH EAC V19.1 Autonomous Product Lab Report

Date: 2026-09-15
Workspace: `D:\moodle\CityNexus-Tools\DSH-EAC-V19.1-AutonomousProductLab-20260915`
Read-only baseline: `D:\moodle\CityNexus` (never modified)
Snapshot: `snapshot/main-tree-20260915T1220`
Working copy: `lab/runtime`
Shadow runtime: backend `127.0.0.1:8052`, frontend `127.0.0.1:4202`

## 1. Executive summary

V19.1 moved beyond the prior fixture-only capability UX. The lab now contains:

- a timestamped read-only snapshot of the moving V19 baseline;
- an isolated backend copy with an isolated SQLite database;
- a fixed V19 backend import blocker that prevented `app.main` from loading;
- deterministic capability contract hardening and tests;
- a conservative Accessibility Provider Evidence adapter over actual OSM tags;
- real isolated API routes for place/journey accessibility evidence and
  capability plan impact;
- a live shadow client with honest `LIVE_SHADOW`, `RECORDED_FIXTURE`, and
  `OFFLINE_STALE` source modes;
- eight complete traveler shadow flows recorded in JSONL;
- performance/PWA/offline/accessibility validation;
- three self-directed product/engineering improvements.

The main worktree was never modified. All changes are in the isolated lab and
the generated patches are additive/low-conflict by concern.

## 2. Baseline finding: backend import blocker

At snapshot time, `backend/app/main.py` imported `capability_payload` from
`app.capabilities`, but that symbol lives in
`app.execution.traveler_twin`.  Importing `app.main` failed with:

```text
ImportError: cannot import name 'capability_payload' from 'app.capabilities'
```

The isolated lab fix imports `capability_payload` from
`app.execution.traveler_twin` and keeps `CAPABILITY_CODES`,
`canonicalize_capabilities`, and `summarize_capabilities` from
`app.capabilities`.  This is a P0 correction and is included in
`patches/01_LIVE_CAPABILITY_ADAPTER.patch`.

## 3. Capability contract hardening

The isolated copy also fixes the known moving-baseline defects:

1. **HARD downgrade guard** — hard accessibility codes can no longer be
   downgraded to `SOFT`.  A `needs_confirmation` candidate is capped at
   `STRONG` until the explicit confirmation endpoint persists it.
2. **Duplicate capability codes** — duplicates now merge parameters
   deterministically and the strongest severity wins (`HARD > STRONG > SOFT`).
3. **Clause-scoped negation/history** — negation and history markers apply to
   the clause that contains them, so "以前不能走，现在想少走路" keeps the
   current low-walking candidate.
4. **Numeric parsing** — common shapes such as "每段不超过300米",
   "连续走15分钟", "每45分钟休息", and "中午12点到14点午休" are parsed
   without inventing provider evidence.
5. **Provider metadata bridge** — feasibility now reads the same
   `metadata["tags"]` OSM facts as the accessibility evidence adapter instead
   of requiring a second nesting.

All are covered by `backend/tests/test_v19_1_capabilities.py`.

## 4. Accessibility Provider Evidence Lab

Created `backend/app/integrations/accessibility/osm.py` plus frozen fixtures and
tests.  The adapter never infers accessibility:

| Provider fact | Normalized consequence |
| --- | --- |
| `wheelchair=yes` | `ACCESSIBILITY_VERIFIED` at `PLACE` |
| `entrance:wheelchair=yes` | `ACCESSIBILITY_VERIFIED` at `ENTRANCE` |
| `wheelchair=no` | `ACCESSIBILITY_CONFLICT` |
| `highway=steps`, `steps=yes`, `step_count>0` | `ACCESSIBILITY_CONFLICT` |
| `wheelchair=limited` | `ACCESSIBILITY_UNVERIFIED` |
| `ramp=yes`, `elevator=yes`, `kerb`, `tactile_paving` | `ACCESSIBILITY_UNVERIFIED` partial facts |
| missing tags | `NEEDS_LIVE_EVIDENCE` |
| positive + explicit stairs | `ACCESSIBILITY_CONFLICT` with `CONFLICTING_TAGS` |

Every fact carries provider, source key, raw key/value, place/city identity,
captured timestamp, confidence type, and provenance.

New isolated endpoints:

- `GET /api/v1/places/{place_id}/accessibility-evidence`
- `GET /api/v1/journeys/{journey_id}/accessibility-evidence`

The journey endpoint explicitly adds `ROUTE_STEP_FREE =
NEEDS_LIVE_EVIDENCE` because the current provider contract cannot prove a
route-level step-free path.  It does not substitute distance, category, or a
modern-building assumption.

## 5. Live / fixture / offline source modes

`lab/runtime/frontend/src/features/capability-experience/liveShadowAdapter.ts`
implements:

- `LIVE_SHADOW`: only data returned by the isolated live backend.
- `RECORDED_FIXTURE`: visibly labelled fixture data.
- `OFFLINE_STALE`: last-known authoritative data plus `staleAt`.

Rules enforced:

1. no source silently falls through to another while keeping the old label;
2. live disconnect preserves last-known data and marks it stale;
3. no fixture data is substituted into a live failure;
4. unknown evidence remains unknown.

The shadow app `shadow-app/` renders the real integration and exposes source
mode controls, live IDs, provider evidence, plan impact, mobile shield, and
Twin capability state.

## 6. Eight shadow traveler flows

`tools/v19_1_shadow_flows.py` ran eight complete flows against the isolated
backend and wrote `evidence/shadow_e2e_results.jsonl`:

| Flow | Result |
| --- | --- |
| A elderly + walking + midday rest | FAIL_EXPECTED_CONFLICT_WITH_GAP |
| B wheelchair + verified place | NEEDS_EVIDENCE |
| C wheelchair + unknown place | NEEDS_EVIDENCE |
| D wheelchair + conflict place | FAIL_EXPECTED_CONFLICT |
| E infant + nap + stroller | FAIL_EXPECTED_CONFLICT_WITH_GAP |
| F large luggage | NEEDS_EVIDENCE |
| G normal soft preference | PASS |
| H conflicting family needs | FAIL_EXPECTED_CONFLICT_WITH_GAP |

Key outcomes:

- verified place evidence does not imply route-level step-free evidence;
- missing tags remain `NEEDS_LIVE_EVIDENCE`;
- explicit `wheelchair=no` / stairs produce conflict, never a softened pass;
- soft preferences remain ranking/explanation context;
- family conflicts surface hard conflict and evidence gaps separately.

## 7. Validation summary

| Gate | Result | Evidence |
| --- | --- | --- |
| TypeScript feature package | PASS | `evidence/build_results.txt` |
| Shadow production build | PASS | `evidence/build_results.txt` |
| Playwright shadow suite | 7/7 passed | `evidence/playwright_results.txt` |
| Axe shadow scan | 0 violations | `evidence/playwright_results.txt` |
| Focused backend suite | 33 passed | `evidence/backend_test_results.txt` |
| Shadow flows | 8/8 recorded, no fabricated pass | `evidence/shadow_e2e_results.jsonl` |
| Bundle analysis | 330,337 bytes / 96,842 gzip bytes | `evidence/bundle_analysis.json` |
| PWA | `vite-plugin-pwa` generateSW, 5 precache entries | `evidence/build_results.txt` |

## 8. Performance / PWA / A11y

- The shadow first-paint bundle contains no MapLibre/WebGL module.
- `vite-plugin-pwa` is the only PWA generator used; no second service worker
  framework was introduced.
- API responses use NetworkFirst runtime caching; UI still labels stale data.
- Playwright covers 320, 390, 430, 1280, 1440 widths, keyboard mode controls,
  reduced motion, long bilingual copy, and an axe scan.
- Critical states use glyph, shape, text, and colour; unknown evidence never
  uses a green check.

## 9. Self-directed work

After mandatory work, three high-value improvements were selected using
`user value × frequency × confidence ÷ merge risk`:

1. **Capability text extraction endpoint** for setup/Copilot confirmation.
2. **Capability audit trail endpoint** for transparency/debuggability.
3. **Capability catalog endpoint** for UI/Copilot vocabulary consistency.

Details and ranking are in `AUTONOMOUS_BACKLOG_DECISIONS.md`.

## 10. Honest boundaries

- No live internet provider call was required.  The lab used existing/frozen
  provider architecture and actual OSM tag shapes.
- Route-level step-free evidence is still `NEEDS_LIVE_EVIDENCE`; the current
  provider contract cannot prove it.
- The shadow app is an isolated reference app.  Product integration patches are
  additive and do not replace `main.tsx`, `router`, or `LocaleProvider`.
- The main worktree was used read-only.  No main-tree file was modified.
- The moving V19 baseline may continue to change; the final delta check should
  be re-run by Codex before applying patches.
