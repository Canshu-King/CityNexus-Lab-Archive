# Codex Merge Guide — V19.1 Autonomous Product Lab

## 1. Patch inventory

| Patch | Concern | Merge disposition | Risk |
| --- | --- | --- | --- |
| `01_LIVE_CAPABILITY_ADAPTER.patch` | import blocker fix, capability contract hardening, live shadow client/source modes | **Can merge now** | Low; mostly new files plus a targeted import fix |
| `02_ACCESSIBILITY_EVIDENCE_REFERENCE.patch` | OSM/provider accessibility adapter, frozen fixtures, evidence endpoints, UI panel | **Can merge now** | Low/medium; new module + additive routes |
| `03_CAPABILITY_EXPERIENCE_INTEGRATION.patch` | `CapabilityShadowExperience`, plan-impact adapter, live source UI | **Merge after/reference** | Medium; additive feature surface |
| `04_PERFORMANCE_PWA_A11Y.patch` | shadow-app PWA config, CSS, Playwright/viewport/a11y gates | **Reference / optional merge** | Low; shadow-app only |
| `05_AUTONOMOUS_IMPROVEMENTS.patch` | extract, audit, catalog endpoints + tests | **Can merge now** | Low; additive endpoints |

Patches are new-file-heavy.  The only baseline edits are:

- `backend/app/main.py` import/route additions and the `Mapping` import;
- `backend/app/capabilities.py` guard/negation/numeric fixes;
- `backend/app/replanning/feasibility.py` provider-tag bridge;
- `backend/app/schemas.py` extraction request model;
- `shadow-app/*` for the isolated reference app.

No patch replaces `main.tsx`, `router`, `LocaleProvider`, or any existing
frontend component.

## 2. Apply order

From `D:\moodle\CityNexus`:

```bat
git apply --check path\to\patches\01_LIVE_CAPABILITY_ADAPTER.patch
git apply path\to\patches\01_LIVE_CAPABILITY_ADAPTER.patch
git apply path\to\patches\02_ACCESSIBILITY_EVIDENCE_REFERENCE.patch
git apply path\to\patches\03_CAPABILITY_EXPERIENCE_INTEGRATION.patch
git apply path\to\patches\04_PERFORMANCE_PWA_A11Y.patch
git apply path\to\patches\05_AUTONOMOUS_IMPROVEMENTS.patch
```

Apply in order; later patches depend on the capability vocabulary and adapter
introduced by patch 01.

## 3. Must merge

- `capability_payload` import fix.  Without it `app.main` cannot load.
- HARD downgrade guard fix and duplicate-capability resolution.
- Clause-scoped negation/history and numeric capability parsing.
- Provider-tag bridge in feasibility, so actual OSM facts are interpreted by
  the gate instead of being ignored.

## 4. Can merge after backend review

- Accessibility evidence endpoints may be merged only if
  `GET /journeys/{id}/accessibility-evidence` continues to return
  `ROUTE_STEP_FREE = NEEDS_LIVE_EVIDENCE`.  Do not change it to a pass.
- Capability plan-impact endpoint is deterministic and derived from actual
  gate failures.  Keep `CONTRACT_NOT_AVAILABLE` when no plan evidence exists.
- Text extraction endpoint is candidate-only.  Do not persist its output.

## 5. Reference only

- `lab/runtime` isolated working copy.
- `shadow-app` isolated Vite lab.
- `tests/v19_1_shadow.spec.ts`.
- `tools/v19_1_shadow_flows.py`.
- `evidence/` artifacts.

These are useful for validation but should not be merged as product surface
unless the product intentionally adopts the isolated lab.

## 6. Do not merge

- Any change that treats `wheelchair` tag absence as accessible.
- Any inference from route distance, building type, or category.
- Any UI that writes `localStorage` capability state as planner authority.
- Any live failure that silently substitutes fixture data.
- Any HARD capability silently persisted to `TRAVELER` scope.

## 7. Contract gaps to respect

- No direct recovery capability-diff endpoint yet.
- No route-level step-free provider evidence yet.
- `contracts/openapi.yaml` is stale relative to runtime; regenerate or overlay
  it separately.

## 8. Verification commands

```powershell
# FastAPI import
cd lab\runtime\backend
& "D:\moodle\CityNexus\.venv\Scripts\python.exe" -c "import app.main; print('IMPORT_OK')"

# Focused backend tests
$env:CITYNEXUS_DATABASE_URL="sqlite:///./v19_1_focused.db"
& "D:\moodle\CityNexus\.venv\Scripts\python.exe" -m pytest -q tests/test_v19_1_capabilities.py tests/test_v19_1_accessibility_evidence.py

# Frontend type/build/tests
cd ..\..\..
node_modules\.bin\tsc -p lab\runtime\frontend\tsconfig.v19_1_feature.json --noEmit
npx vite build --config shadow-app\vite.config.ts
npx playwright test --config tests\playwright.config.ts
```
