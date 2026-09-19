# V19.1 Baseline Audit

## What V19.1 genuinely achieved

Codex V19.1 materially improved the product and should remain the base. The following are accepted as useful convergence results:

- the two previously mandated negation/history false-HARD cases are fixed;
- HARD accessibility downgrade protection is working;
- requirement-scoped accessibility evaluation is better than the EAC aggregate approach;
- route-level step-free remains unknown without route evidence;
- `PUT /capabilities` is full desired-set replacement;
- `POST /capabilities/confirm` is submitted-item upsert and preserves prior active items;
- REST/toilet interval semantics were moved toward continuous-span `interval_min` behavior;
- runtime OpenAPI and checked-in OpenAPI are now in parity in WorkBuddy's Snapshot C;
- frontend production build and 390x844 mobile smoke passed.

## Do not re-open solved questions

### OpenAPI `/api/v1`

WorkBuddy's final check found runtime/checked-in path parity. The earlier EAC suspicion about `/api/v1` was not a current V19.1 defect. Do not spend another round "fixing" a prefix that is already represented correctly through the API server/base-path contract.

### EAC aggregate accessibility state

Do not restore the EAC-style generic `overall_accessibility_state()` as the authority for every requirement. Requirement-specific evaluation remains the correct design.

### Local NLP authority

Do not promote the local extractor into the primary semantic interpreter. DeepSeek remains primary; local extraction is a conservative fallback/safety net.

## Release-truth problem

The V19.1 implementation reports under `reports/product-v19-1/` are current, but the packaged top-level files such as:

```text
CURRENT_STATUS.md
TEST_RESULTS.md
NEXT_RECOMMENDATION.md
PACKAGE-MANIFEST.json
CHANGED_FILES.txt
```

still describe V18.3 in the supplied V19.1 artifact.

That is a release-hygiene defect. V19.2 must regenerate top-level release truth from the actual final tree.

## Broad regression truth

Codex V19.1 itself reported:

```text
424 passed
10 failed
3 skipped
1 setup error
```

Therefore V19.1 must not be described as broadly green. V19.2 needs to classify every remaining failure and clear any genuine regression relevant to the product trial.
