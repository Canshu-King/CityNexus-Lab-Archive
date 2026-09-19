# Accessibility Provider Evidence Report

## 1. Scope

This report covers the conservative provider-evidence adapter built in the
isolated V19.1 lab.  It uses existing CityNexus provider architecture
(Nominatim/Overpass-shaped records and frozen tags) and does not invent
accessibility facts.

Implementation:

- `lab/runtime/backend/app/integrations/accessibility/osm.py`
- `lab/runtime/backend/tests/test_v19_1_accessibility_evidence.py`
- `lab/runtime/data/accessibility/evidence_cases.json`
- `evidence/provider_evidence_cases.jsonl`

API:

- `GET /api/v1/places/{place_id}/accessibility-evidence`
- `GET /api/v1/journeys/{journey_id}/accessibility-evidence`

UI:

- `ProviderEvidencePanel`
- `providerEvidence.ts`

## 2. Normalization table

| Actual provider input | State | Subject | Notes |
| --- | --- | --- | --- |
| `wheelchair=yes/designated` | `ACCESSIBILITY_VERIFIED` | `PLACE` | explicit provider evidence |
| `entrance:wheelchair=yes` | `ACCESSIBILITY_VERIFIED` | `ENTRANCE` | explicit entrance evidence |
| `wheelchair=no` | `ACCESSIBILITY_CONFLICT` | `PLACE` | explicit conflict |
| `highway=steps`, `steps=yes`, `step_count>0` | `ACCESSIBILITY_CONFLICT` | `ROUTE` | explicit stair conflict |
| `wheelchair=limited` | `ACCESSIBILITY_UNVERIFIED` | `PLACE` | limited is not step-free |
| `ramp=yes` | `ACCESSIBILITY_UNVERIFIED` | `VERTICAL_ACCESS` | ramp exists, route not proven |
| `elevator=yes` | `ACCESSIBILITY_UNVERIFIED` | `VERTICAL_ACCESS` | elevator exists, route/status not proven |
| `kerb=lowered` | `ACCESSIBILITY_UNVERIFIED` | `KERB` | segment-level evidence |
| `tactile_paving=yes` | `ACCESSIBILITY_UNVERIFIED` | `ROUTE` | partial route evidence |
| `toilets:wheelchair=yes` | `ACCESSIBILITY_VERIFIED` | `TOILET` | scoped to the facility, not the route |
| missing relevant tags | `NEEDS_LIVE_EVIDENCE` | `PLACE` | absence is unknown, not accessible |
| positive place + explicit stairs | `ACCESSIBILITY_CONFLICT` | `PLACE` | `CONFLICTING_TAGS` |

Every fact includes:

- `provider`
- `source_key`
- `raw.key` / `raw.value`
- `place_id` / `city_code`
- `captured_at`
- `confidence_type`
- `provenance`

## 3. Prohibited inferences

The adapter and tests explicitly prohibit:

- inferring a wheelchair lift because a building is modern;
- inferring accessibility because a tag is absent;
- inferring step-free from short distance;
- inferring a nursing room from category;
- treating `ramp=yes` alone as a verified step-free route.

## 4. Journey-level truth

The journey endpoint aggregates actual place facts for planned activities and
then adds:

```json
{
  "state": "NEEDS_LIVE_EVIDENCE",
  "code": "ROUTE_STEP_FREE",
  "subject": "ROUTE",
  "summary": "Route-level step-free evidence is not available from the current provider contract."
}
```

This is deliberate.  The current provider contract cannot prove a route-level
step-free path, so the product must say so.

## 5. Frozen case results

The frozen cases cover:

- verified wheelchair + accessible toilet;
- `wheelchair=no`;
- unknown/no relevant tags;
- `wheelchair=limited`;
- stairs + step count;
- ramp + elevator only;
- positive `wheelchair=yes` conflicting with `step_count=5`.

`evidence/provider_evidence_cases.jsonl` contains the normalized output.

## 6. Honest limitations

- No live internet provider call was required for this lab.
- The adapter consumes existing/frozen provider-shaped tags; real Overpass
  metadata availability still depends on the external provider.
- `ramp`, `elevator`, `kerb`, and `tactile_paving` are intentionally partial
  evidence.  They should not be promoted to verified route accessibility
  without an explicit route-level provider check.
