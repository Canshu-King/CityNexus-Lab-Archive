# Live Capability Contract Map

Source of truth: isolated V19 backend snapshot
`snapshot/main-tree-20260915T1220`, exercised at `127.0.0.1:8052`.
Captured runtime OpenAPI: `evidence/api_contract.json`.

## 1. Contract authority

- The live backend owns capability persistence, confirmation, scope, and audit.
- The UI adapter maps live rows into presentation models only.
- No UI component writes `localStorage` as planning authority.
- No source mode silently substitutes fixture data for a live response.

## 2. Actual capability routes in the isolated V19 backend

| Method | Route | Contract role | UI consumption |
| --- | --- | --- | --- |
| `GET` | `/api/v1/travelers/{traveler_id}/capabilities` | traveler-scope capability rows + summary | `liveShadowAdapter.getTravelerCapabilities` |
| `PUT` | `/api/v1/travelers/{traveler_id}/capabilities` | stage user-stated rows; HARD unconfirmed rejected with 409 | not used by shadow UI for HARD |
| `POST` | `/api/v1/travelers/{traveler_id}/capabilities/confirm` | explicit durable confirmation | `confirmTravelerCapabilities` |
| `GET` | `/api/v1/journeys/{journey_id}/capabilities` | journey-scope capability rows + summary | `liveShadowAdapter.getJourneyCapabilities` |
| `PUT` | `/api/v1/journeys/{journey_id}/capabilities` | stage journey rows; HARD unconfirmed rejected with 409 | not used by shadow UI for HARD |
| `POST` | `/api/v1/journeys/{journey_id}/capabilities/confirm` | explicit journey confirmation | `confirmJourneyCapabilities` |
| `GET` | `/api/v1/travelers/{traveler_id}/traveler-twin` | explicit capabilities + learned soft preferences | `TwinCapabilitySummary` via live adapter |
| `GET` | `/api/v1/places/{place_id}/accessibility-evidence` | normalized provider evidence for a place | `ProviderEvidencePanel` |
| `GET` | `/api/v1/journeys/{journey_id}/accessibility-evidence` | place facts + explicit route-level gap | `ProviderEvidencePanel` |
| `GET` | `/api/v1/journeys/{journey_id}/capability-plan-impact` | actual deterministic gate failures translated into capability impacts | `CapabilityPlanExplanation` |
| `POST` | `/api/v1/travelers/{traveler_id}/capabilities/extract` | bounded text candidates only, no persistence | setup/Copilot helper |
| `GET` | `/api/v1/travelers/{traveler_id}/capabilities/audit` | capability change audit trail | transparency/debugging |
| `GET` | `/api/v1/capabilities/catalog` | canonical vocabulary for UI/Copilot | adapter labels/validation |

## 3. Field mapping

| Backend field | UI model | Rule |
| --- | --- | --- |
| `code` | `TravelerCapability.extra.backend_code`, label map | unknown code → `UNKNOWN_CAPABILITY`, never inferred |
| `class` | `CapabilityKind` | hard accessibility codes retain their class |
| `severity` | `CapabilityStrength` | `HARD`/`STRONG`/`SOFT` |
| `params` | `CapabilityConstraint[]` + `extra.backend_params` | parsed conservatively; no provider claim |
| `scope` | `THIS_JOURNEY` or `TRAVELER` | `JOURNEY` → `THIS_JOURNEY` |
| `source` / `provenance` | `CapabilitySource` / provenance label | `USER_CONFIRMED`/`USER_STATED` → traveler stated |
| `confirmed` | confirmation UI | unconfirmed rows show confirmation candidate |
| `active` | active capability shield | inactive rows excluded |
| `updated_at` / `confirmed_at` | evidence observed timestamp | provenance only |

## 4. Contract gaps still present

1. There is no direct `recovery/capability-diff` route.  The lab derives a
   recovery view from the actual plan-impact gate and labels it
   `BACKEND_PLANNING`; a dedicated before/after snapshot endpoint remains a
   recommended contract addition.
2. There is no route-level step-free evidence endpoint.  The journey endpoint
   explicitly returns `ROUTE_STEP_FREE = NEEDS_LIVE_EVIDENCE`.
3. `contracts/openapi.yaml` in the snapshot is stale relative to the runtime
   app: the checked-in file uses paths without `/api/v1`, and it does not
   include the capability or accessibility evidence routes.  The runtime
   `evidence/api_contract.json` is the mapped source for this lab.
4. TravelerTwin learned soft preferences are not accessibility evidence.  They
   remain soft ranking context only.

## 5. Minimal low-conflict proposal for Codex

No backend rewrite is required.  The minimum contract additions are:

1. keep the existing capability CRUD/confirm routes;
2. add `GET /api/v1/journeys/{journey_id}/recovery/capability-diff` returning
   `before`, `after`, `preserved`, `at_risk`, `evidence_gaps`, and C4;
3. add route-level provider evidence only when a real provider can prove it;
   otherwise return `NEEDS_LIVE_EVIDENCE` explicitly;
4. regenerate `contracts/openapi.yaml` from the running app so path prefixes
   and capability schemas stop drifting.

All UI calls already tolerate missing routes by returning
`CONTRACT_NOT_AVAILABLE` or `NEEDS_LIVE_EVIDENCE`.

## 6. Runtime vs checked-in spec delta

`evidence/contract_drift.json` records:

- runtime paths: 134;
- checked-in `contracts/openapi.yaml` paths: 124;
- all capability/accessibility routes are present in runtime and missing from
  the checked-in file;
- the checked-in file also omits the `/api/v1` prefix.

The runtime capture is `evidence/api_contract.json`.  Regenerating the
checked-in spec from the running app is a release-hygiene recommendation, not a
runtime dependency.
