# Shadow Integration Results

## 1. Isolated snapshot

| Item | Value |
| --- | --- |
| Main worktree | `D:\moodle\CityNexus` (read-only) |
| Snapshot | `snapshot/main-tree-20260915T1220` |
| Working copy | `lab/runtime` |
| Backend port | `8052` |
| Frontend port | `4202` |
| Database | isolated SQLite files under `lab/runtime/backend` |
| Python runtime | existing read-only venv, `PYTHONDONTWRITEBYTECODE=1` |

No main-tree file was written.

## 2. Live integration result

The current V19 backend had a P0 import blocker at snapshot time.  The isolated
copy fixes the import and successfully serves the current capability contract.

Actual routes exercised:

- traveler and journey capabilities list;
- traveler and journey capability confirm;
- TravelerTwin explicit capabilities;
- capability plan impact;
- place and journey accessibility evidence;
- bounded text extraction;
- capability audit;
- capability catalog.

Runtime OpenAPI capture: `evidence/api_contract.json`.

## 3. Source modes

| Mode | Behavior |
| --- | --- |
| `LIVE_SHADOW` | only isolated live backend responses |
| `RECORDED_FIXTURE` | visibly labelled fixture capabilities |
| `OFFLINE_STALE` | last-known data + `staleAt`, never relabelled live |

Failure behavior:

- live failure + cache → `OFFLINE_STALE`;
- live failure + no cache → `LIVE_SHADOW` source with
  `CONTRACT_NOT_AVAILABLE` error, no fixture substitution;
- fixture mode never changes the live cache label.

## 4. UI integration

`CapabilityShadowExperience` renders:

- Journey Setup with real confirmation calls;
- Copilot-style confirmation for unconfirmed live capability rows;
- TravelerTwin capability summary;
- Mobile capability shield;
- provider evidence panel;
- capability-aware plan impact;
- recovery diff derived from the live plan-impact gate.

`shadow-app/` is the isolated Vite app that consumes these APIs.  It does not
replace the main frontend.

## 5. Eight flows

`tools/v19_1_shadow_flows.py` seeds the isolated DB, confirms capabilities,
generates a baseline plan, evaluates the actual deterministic gate, and calls
the provider evidence endpoint.

Results: `evidence/shadow_e2e_results.jsonl`.

Observed statuses:

- `PASS` for ordinary soft preference;
- `NEEDS_EVIDENCE` for unknown/partial provider evidence;
- `FAIL_EXPECTED_CONFLICT` for explicit stairs/wheelchair conflict;
- `FAIL_EXPECTED_CONFLICT_WITH_GAP` when a hard conflict and an evidence gap
  coexist.

No flow was recorded as a fabricated accessibility pass.

## 6. Repro commands

From the workspace root:

```powershell
# backend focused tests
cd lab\runtime\backend
$env:CITYNEXUS_DATABASE_URL="sqlite:///./v19_1_focused.db"
& "D:\moodle\CityNexus\.venv\Scripts\python.exe" -m pytest -q tests/test_v19_1_capabilities.py tests/test_v19_1_accessibility_evidence.py

# shadow flows
& "D:\moodle\CityNexus\.venv\Scripts\python.exe" ..\..\..\tools\v19_1_shadow_flows.py

# frontend/type/build
cd ..\..\..
node_modules\.bin\tsc -p lab\runtime\frontend\tsconfig.v19_1_feature.json --noEmit
npx vite build --config shadow-app\vite.config.ts

# browser suite
npx playwright test --config tests\playwright.config.ts
```
