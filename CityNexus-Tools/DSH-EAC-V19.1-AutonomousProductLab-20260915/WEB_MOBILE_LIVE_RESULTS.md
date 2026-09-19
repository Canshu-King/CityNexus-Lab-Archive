# Web / Mobile Live Results

## 1. Live shadow UI

`CapabilityShadowExperience` consumes the isolated V19 contract and renders:

- `JourneySetupNeeds` with real confirmation calls;
- `CopilotNeedsConfirmation` for unconfirmed live rows;
- `TwinCapabilitySummary` for explicit capability + learned soft context;
- `MobileCapabilityShield`;
- `ProviderEvidencePanel`;
- `CapabilityPlanExplanation` from the live plan-impact endpoint;
- `RecoveryDiffCapability` derived from the live gate.

Source label is always visible and never inferred from component presence.

## 2. Desktop behavior

Validated widths:

- 1280×720
- 1440×900

The desktop surface keeps provider evidence, plan impact, recovery, Twin, and
mobile preview visible.  Unknown/partial evidence uses dashed/dotted states and
text labels.  Plan impact shows actual gate failures or
`CONTRACT_NOT_AVAILABLE` when no plan evidence exists.

## 3. Mobile behavior

Validated widths:

- 320×720
- 390×844
- 430×932

The mobile capability shield keeps its primary action at least 44px tall and
inside the viewport.  Source mode controls stack at narrow widths.  Provider
evidence rows expose raw tag/value/captured timestamp without truncation of
critical text.

## 4. Live capability confirmation

- HARD traveler/journey capabilities cannot be staged without confirmation;
  the backend returns 409 on the unconfirmed PUT path.
- The shadow UI uses the explicit `/confirm` endpoints.
- Text extraction returns candidates only (`authority=UI_CANDIDATE_ONLY`) and
  never persists.
- The UI does not treat local setup state as planner authority.

## 5. Planner/recovery explainability

`GET /journeys/{id}/capability-plan-impact` returns actual deterministic gate
failures mapped to capability impacts:

- hard conflict → rejected/violated impact;
- missing provider evidence → unknown/needs-live impact;
- soft preference → ranking/explanation context only;
- C4/Journey boundary failures → separate protected-commitment view.

Recovery diff is derived from the current live plan-impact snapshot.  A dedicated
before/after recovery endpoint remains a clear contract gap and is documented in
`LIVE_CAPABILITY_CONTRACT_MAP.md`.

## 6. Evidence boundaries

- Verified provider place evidence is not promoted to verified route evidence.
- `wheelchair=yes` at one place does not make every candidate accessible.
- Unknown evidence is never rendered as `VERIFIED`.
- `RECORDED_FIXTURE` and `OFFLINE_STALE` remain clearly labelled.
