# CityNexus V19 Capability Experience package

Additive, low-conflict frontend package for Traveler Capability / Accessibility.
It does not replace `main.tsx`, `router`, or `LocaleProvider`.

## Import surfaces

- `types.ts`, `adapter.ts`, `recordedFixture.ts`: UI contract, normalisers, and explicitly labelled `RECORDED_FIXTURE` scenarios.
- `components/JourneySetupNeeds.tsx`, `components/CopilotNeedsConfirmation.tsx`: setup and detected-needs confirmation.
- `components/CapabilityPlanExplanation.tsx`, `components/RecoveryDiffCapability.tsx`: capability-aware plan/recovery explanation.
- `components/TwinCapabilitySummary.tsx`, `components/MobileCapabilityShield.tsx`, `components/CapabilityMapOverlay.tsx`: Twin, mobile shield, map markers.

## Honesty rules

1. `UNKNOWN != ACCESSIBLE`. Missing, unrecognised, stale, or conflicting evidence normalises to `NEEDS_LIVE_EVIDENCE` or `CONFLICT`.
2. `RECORDED_FIXTURE` is always rendered as recorded fixture. The live adapter throws `CapabilityAdapterNotConfiguredError` instead of silently substituting fixture data.
3. No component writes `localStorage`. Confirmations call caller-owned callbacks; the backend capability contract remains planning authority.
4. HARD needs are never silently persisted to future journeys. The confirmation surface requires explicit acknowledgement or `This Journey only`.
5. Learned soft preferences may show strength/confidence. HARD accessibility needs never show a confidence progress bar.

## Apply order

Apply `01` → `02` → `03` → `04`. Patch 02+ depend on the core types/evidence adapter in patch 01. All patches add new files only.
