# DSH EAC V19 Capability Experience Report

Date: 2026-09-15
Workspace: `D:\moodle\CityNexus-Tools\DSH-EAC-V19-CapabilityExperience-20260915`
Main worktree: `D:\moodle\CityNexus` (read-only reference; not modified)

## 1. Outcome

Built a production-mergeable, additive Web + Mobile experience kit for Traveler
Capability / Accessibility. The kit is split into four low-conflict patches that
add files under `frontend/src/features/capability-experience/` only. No patch
replaces `main.tsx`, `router`, `LocaleProvider`, or any existing CityNexus file.

The package is honest about its current authority:

| Area | Delivered | Authority |
| --- | --- | --- |
| Capability types / adapter | `types.ts`, `adapter.ts`, `evidence.ts` | UI contract only; backend remains planning authority |
| Recorded scenarios | `recordedFixture.ts` (A–E) | `RECORDED_FIXTURE`, explicitly labelled |
| Live adapter | `createLiveCapabilityAdapter()` | Proposed routes; throws `CAPABILITY_CONTRACT_NOT_AVAILABLE` on 404 instead of fabricating data |
| Setup UX | `JourneySetupNeeds` | UI draft; no `localStorage` authority |
| Copilot confirmation | `CopilotNeedsConfirmation` | Caller-owned decision callback; HARD needs cannot be silently persisted |
| Plan / recovery UX | `CapabilityPlanExplanation`, `RecoveryDiffCapability` | Explanations, rejected candidates, unknowns, C4 separation |
| Traveler Twin | `TwinCapabilitySummary` | Explicit capability/preference and learned soft preference are distinct; HARD needs never use a confidence bar |
| Mobile / map | `MobileCapabilityShield`, `CapabilityMapOverlay` | Compact shield + evidence markers; unknown is never rendered as available |

## 2. Critical honesty rules

1. `UNKNOWN != ACCESSIBLE`. Missing, unrecognised, stale, or conflicting evidence
   normalises to `NEEDS_LIVE_EVIDENCE` or `CONFLICT`.
2. No UI surface renders a green check for unknown evidence.
3. No component writes `localStorage`. The adapter does not mutate backend state.
4. HARD accessibility needs are never persisted silently. The confirmation card
   requires explicit acknowledgement for future journeys or `This Journey only`.
5. Learned soft preferences may show strength/confidence. HARD accessibility
   needs do not show confidence progress bars.
6. Recorded fixtures are always labelled `RECORDED_FIXTURE`. Live adapter calls
   report unavailable states rather than falling back silently.

## 3. Reference scenarios

| ID | Scenario | Core demonstration |
| --- | --- | --- |
| A | Older adult / knee pain | HARD walking limit, STRONG midday rest, unknown step-free evidence, recovery diff |
| B | Wheelchair / step-free | Verified step-free entrance, unverified Candidate B, known stairs conflict |
| C | Family with infant | Stroller, nap window, care requirement states, unknown elevator evidence |
| D | Large luggage | Trip context + HARD avoid stairs, rejected transfer, unknown taxi availability |
| E | Ordinary soft preference | No HARD need; UI still refuses to claim accessibility from unknown/default state |

Each scenario contains setup state, Copilot detected needs, plan explanation,
recovery state, mobile shield state, and map markers.

## 4. Engineering results

| Gate | Command | Result |
| --- | --- | --- |
| TypeScript (`tsc`) | `npx tsc -p tsconfig.capability.json --noEmit` | PASS (feature package; ambient React shim because the copied frontend snapshot lacks `@types/react`) |
| Production build | `npx vite build --config reference-app/vite.config.ts` | PASS |
| Playwright desktop/mobile keyboard/a11y/live-source | `npx playwright test --config tests/playwright.config.ts` | 7 passed |
| Patch apply check against main tree | `git apply --check patches/*.patch` | PASS for all four patches; main tree untouched |
| Axe automated scan | Playwright + `@axe-core/playwright` | Zero violations on the reference lab at 1280×900 |

Evidence files:

- `evidence/playwright-results.txt`
- `evidence/build_results.txt`
- `evidence/screenshots/*.png`
- `patches/*.patch`

## 5. Known boundary

- The V19 backend capability contract does not yet expose
  `/travelers/{id}/capabilities`, `/journeys/{id}/capability-plan`, or
  `/journeys/{id}/recovery/capability-diff`. Those routes are proposed in
  `CAPABILITY_UI_CONTRACT.md`.
- Until the backend contract is implemented, the package uses
  `RECORDED_FIXTURE` data and a live adapter that fails honestly.
- Existing TravelerTwin data has explicit preferences and learned soft
  preferences but no hard accessibility classification. The adapter maps those
  conservatively to soft/explicit preference context and never infers a hard
  accessibility need from soft data.
- Automated axe covers detectable issues. It does not replace manual screen
  reader, touch, or low-bandwidth validation.

## 6. Main tree protection

The main worktree was used read-only to inspect types, routes, components, and
test conventions. All work was performed in the isolated workspace. The four
patches are new-file diffs generated against `frontend/` paths and pass
`git apply --check` in the main tree without writing anything.

## 7. Noon continuation result

At 2026-09-15 12:00 +08 the scheduled task
`CityNexus_DSH_EAC_V19_Noon_Continuation` ran.

- Deterministic TypeScript, production build, Playwright 7/7, and all four
  patch apply checks passed.
- Final ZIP created at
  `D:\moodle\CityNexus-Tools\CityNexus-DSH-EAC-V19-CapabilityExperience-20260915.zip`.
- The optional `codex exec` continuation did not start because the external
  user-level Codex CLI config contains `model_reasoning_effort = "max"`, which
  the installed CLI rejects. This is documented in
  `evidence/codex_cli_blocker.md` and `evidence/noon_codex_notes.md`.
- The deterministic package does not depend on that external CLI continuation.
