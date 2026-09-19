# Codex Merge Guide — V19 Capability Experience

## 1. Patch inventory

| Patch | Adds | Merge disposition |
| --- | --- | --- |
| `01_CAPABILITY_TYPES_ADAPTER.patch` | `types.ts`, `copy.ts`, `evidence.ts`, `adapter.ts`, `recordedFixture.ts`, shared CSS, README | **Can merge now.** New files only; no runtime wiring. |
| `02_SETUP_AND_CONFIRMATION_UI.patch` | `EvidenceBadge`, `JourneySetupNeeds`, `CopilotNeedsConfirmation` | **Can merge now.** New files only; components are controlled and caller-owned. |
| `03_PLAN_RECOVERY_CAPABILITY_UI.patch` | `CapabilityPlanExplanation`, `RecoveryDiffCapability` | **Can merge now; wire only after backend contract or with fixture-lab gating.** |
| `04_TWIN_MOBILE_MAP_OPTIONAL.patch` | `TwinCapabilitySummary`, `MobileCapabilityShield`, `CapabilityMapOverlay` | **Can merge; Map/Twin integration should wait for backend capability fields or remain behind a reference flag.** |

No patch replaces `main.tsx`, `router`, `LocaleProvider`, `MapPanel`, or any
existing product component.

## 2. Apply commands

From `D:\moodle\CityNexus`:

```bat
git apply --check patches\01_CAPABILITY_TYPES_ADAPTER.patch
git apply patches\01_CAPABILITY_TYPES_ADAPTER.patch
git apply patches\02_SETUP_AND_CONFIRMATION_UI.patch
git apply patches\03_PLAN_RECOVERY_CAPABILITY_UI.patch
git apply patches\04_TWIN_MOBILE_MAP_OPTIONAL.patch
```

Set `\path\to\patches` to the delivered `patches/` directory. Apply in order.

## 3. Integration rule

Merge authority by category:

### Can be merged directly

- Type and adapter files.
- Evidence badge and evidence summary primitives.
- Journey setup component.
- Copilot detected-needs confirmation component.
- Plan/recovery/Twin/mobile/map presentational components.

They add no modules, mutate no globals, and do not write persistence.

### Must wait for backend contract

- Real `TravelerCapability[]` data on setup save.
- `CapabilityConfirmationDecision` mutation/confirmation endpoint.
- Live plan capability explanation.
- Live recovery diff.
- Live map evidence markers tied to actual provider geometry.

Until then, use `createRecordedFixtureAdapter()` and display
`RECORDED_FIXTURE`. The live adapter returns
`CapabilityAdapterNotConfiguredError` when the route is absent.

### Reference only

- `reference-app/` — an isolated Vite lab for visual/manual review.
- `tests/` — Playwright spec/config for the lab.
- `evidence/` — screenshots and command results.
- `patchwork/` — internal patch generation staging; exclude from release if
  desired.

### Do not merge

- Any change that writes capability state to `localStorage` and presents it as
  planning authority.
- Any unknown evidence rendered as a green check or "accessible".
- Any HARD need silently persisted to `FUTURE_JOURNEYS` or `TRAVELER`.
- Any confidence progress bar on an explicit HARD accessibility need.

## 4. Minimal wiring example

```tsx
import { useEffect, useState } from "react";
import type { TravelerCapability } from "../features/capability-experience/types";
import { createRecordedFixtureAdapter } from "../features/capability-experience/recordedFixture";
import { JourneySetupNeeds } from "../features/capability-experience/components/JourneySetupNeeds";
import { CopilotNeedsConfirmation } from "../features/capability-experience/components/CopilotNeedsConfirmation";

const adapter = createRecordedFixtureAdapter();

export function CapabilitySurface() {
  const [capabilities, setCapabilities] = useState<TravelerCapability[]>([]);
  useEffect(() => {
    void adapter.fetchCapabilities("traveler-id").then(setCapabilities);
  }, []);
  return (
    <>
      <JourneySetupNeeds
        value={{ quickNeedIds: [], advanced: {}, note: "" }}
        onChange={() => undefined}
        onSave={(draft) => {
          // Submit draft to backend when the contract exists.
          // Do not persist client-side as planning authority.
        }}
      />
      <CopilotNeedsConfirmation
        confirmations={[]}
        onDecision={(decision) => {
          // Submit decision to backend when the contract exists.
        }}
      />
    </>
  );
}
```

## 5. CSS

Each component imports `../styles/capability-experience.css`. Codex does not
need to edit a global stylesheet. The classes are prefixed `cne-` to reduce
collision risk.

## 6. Backend contract checklist

When the backend is ready, implement routes in
`CAPABILITY_UI_CONTRACT.md` and map responses through **adapter.ts** only. Keep
unknown values as `NEEDS_LIVE_EVIDENCE`; do not infer `VERIFIED` from route
presence, opening hours, or soft TravelerTwin dimensions.

## 7. Risk notes

- Patch 02+ depend on patch 01 for types and shared CSS. Apply in order.
- Evidence state normalisation is deliberately conservative.
- `UNKNOWN_CAPABILITY` and unknown future fields are retained in `extra`;
  consumers should not crash on them.
- C4 commitments are intentionally rendered separately from ordinary capability
  impacts.
