# Capability UI Contract (V19)

Status: UI contract + adapter proposal. Backend planning authority remains with
the server. The UI may explain, collect confirmation, and display evidence, but
must not claim that local settings changed planning.

## 1. Capability taxonomy

`frontend/src/features/capability-experience/types.ts` defines:

- `HARD_ACCESSIBILITY_NEED`
- `CARE_REQUIREMENT`
- `PHYSICAL_LIMIT`
- `TRIP_CONTEXT`
- `SOFT_PREFERENCE`
- `PROTECTED_COMMITMENT`
- `UNKNOWN_CAPABILITY` (defensive fallback for future fields)

Unknown kinds are preserved as `UNKNOWN_CAPABILITY`, never silently treated as
soft or hard. They render with `NEEDS_LIVE_EVIDENCE`.

## 2. Evidence states

| State | UI meaning | Visual rule |
| --- | --- | --- |
| `VERIFIED` | Provider/source evidence exists | Solid badge, check glyph, explicit "Verified" text |
| `UNVERIFIED` | A source exists but planning evidence is not confirmed | Dashed badge, question glyph, explicit "Unverified" text |
| `CONFLICT` | Sources contradict, or a known conflict exists | Double border, exclamation glyph, explicit "Conflict" text |
| `NEEDS_LIVE_EVIDENCE` | Evidence is missing, stale, unknown, or not yet fetched | Dotted badge, hourglass glyph, explicit "Needs live evidence" text |

Normalisation is centralised in `adapter.ts:normalizeEvidenceState`. Any
unrecognised state formats to `NEEDS_LIVE_EVIDENCE`. `UNVERIFIED` and
`NEEDS_LIVE_EVIDENCE` never render a green check.

## 3. Core model

### TravelerCapability

| Field | Notes |
| --- | --- |
| `id`, `label`, `kind`, `strength`, `scope` | `strength` is `HARD`, `STRONG`, `SOFT`, or `AMBIGUOUS`; `scope` is `THIS_JOURNEY`, `FUTURE_JOURNEYS`, or `TRAVELER` |
| `source`, `sourceLabel` | `TRAVELER_STATED`, `COPILOT_DETECTED`, `PROVIDER_EVIDENCE`, `RECORDED_FIXTURE`, `LEARNED_SOFT`, `IMPORTED` |
| `evidence` | `state`, `provenance`, `summary`, `detail`, `liveChecks`, `conflictsWith`, `facts` |
| `active`, `confirmed`, `explicit`, `learned`, `travelerStated` | Authority / lifecycle flags |
| `constraints` | Typed constraint list (`max_walking_per_leg_m`, `nap_window`, etc.) |
| `confidence`, `strengthScore`, `evidenceCount` | Only meaningful for learned soft preferences; callers must not render these for HARD needs |
| `extra` | Unknown future fields are preserved instead of crashing |

### Other model objects

- `CapabilityEvidence`
- `CapabilityConflict`
- `CapabilityImpact` (status: `PRESERVED`, `IMPROVED`, `AT_RISK`, `VIOLATED`, `UNKNOWN`)
- `CapabilityConfirmation` (detected language proposal, ambiguity options)
- `CapabilityConfirmationDecision` (`CONFIRM`, `JOURNEY_ONLY`, `DISMISS`, `EDIT`)
- `PlanCapabilityExplanationModel`
- `RecoveryCapabilityDiffModel`
- `MobileCapabilityShieldModel`
- `CapabilityMapMarker`

## 4. Adapter surface

`adapter.ts` exports:

```ts
interface CapabilityDataSource {
  readonly sourceKind: "LIVE" | "RECORDED_FIXTURE" | "LOCAL_UI_ONLY";
  fetchCapabilities(travelerId: string): Promise<TravelerCapability[]>;
  fetchPlanExplanation(journeyId: string): Promise<PlanCapabilityExplanationModel>;
  fetchRecoveryDiff(journeyId: string): Promise<RecoveryCapabilityDiffModel>;
}
```

Factories:

- `createRecordedFixtureAdapter(scenario)` — always `RECORDED_FIXTURE`.
- `createLiveCapabilityAdapter({ baseUrl, fetcher })` — maps proposed live routes.

Live adapter failure mode:

```ts
if (response.status === 404) {
  throw new CapabilityAdapterNotConfiguredError(
    "Capability endpoint not implemented yet. Use RECORDED_FIXTURE explicitly."
  );
}
```

It never substitutes fixture data automatically.

## 5. Proposed backend contract

The UI is ready for these routes when the backend contract is complete:

| Method | Route | Response |
| --- | --- | --- |
| `GET` | `/api/v1/travelers/{traveler_id}/capabilities` | `{ items: TravelerCapabilityDto[] }` or `{ capabilities: [...] }` |
| `GET` | `/api/v1/journeys/{journey_id}/capability-plan` | `PlanCapabilityExplanationDto` |
| `GET` | `/api/v1/journeys/{journey_id}/recovery/capability-diff` | `RecoveryCapabilityDiffDto` |

The adapter also accepts a `traveler_twin` object when no hard capability rows
exist. In that case explicit and learned soft preferences are mapped to
`SOFT_PREFERENCE` / `TRAVELER` and evidence stays `UNVERIFIED`. The adapter does
not infer `HARD_ACCESSIBILITY_NEED` from `low_walking`, `indoor_stops`, or any
soft dimension.

## 6. Unknown-field behaviour

- `adaptCapability` reads unknown records defensively.
- Unknown `kind` → `UNKNOWN_CAPABILITY`.
- Unknown strength/class → `AMBIGUOUS` (requires confirmation), never `SOFT`.
- Unknown scope → `THIS_JOURNEY` (no silent future persistence).
- Unknown evidence state → `NEEDS_LIVE_EVIDENCE`.
- Unknown primitive fields are retained in `extra`.

## 7. Authority and persistence rules

1. Components are controlled and call caller-owned callbacks.
2. No component calls `localStorage`, IndexedDB, or a mutation API directly.
3. `JourneySetupNeeds` emits `TravelerCapability[]` to `onSave`; it does not
   persist them.
4. `CopilotNeedsConfirmation` emits `CapabilityConfirmationDecision`; it does
   not persist.
5. HARD future persistence requires the explicit acknowledgement checkbox or
   `This Journey only`.
6. `protectedCommitments` C4 are rendered separately from ordinary capability
   impacts.

## 8. Integration imports

```ts
import {
  createLiveCapabilityAdapter,
  createRecordedFixtureAdapter,
} from "../features/capability-experience/recordedFixture";
import { JourneySetupNeeds } from "../features/capability-experience/components/JourneySetupNeeds";
import { CopilotNeedsConfirmation } from "../features/capability-experience/components/CopilotNeedsConfirmation";
import { CapabilityPlanExplanation } from "../features/capability-experience/components/CapabilityPlanExplanation";
import { RecoveryDiffCapability } from "../features/capability-experience/components/RecoveryDiffCapability";
import { TwinCapabilitySummary } from "../features/capability-experience/components/TwinCapabilitySummary";
import { MobileCapabilityShield } from "../features/capability-experience/components/MobileCapabilityShield";
import { CapabilityMapOverlay } from "../features/capability-experience/components/CapabilityMapOverlay";
```

The shared CSS is imported by the components themselves:
`../styles/capability-experience.css`.
