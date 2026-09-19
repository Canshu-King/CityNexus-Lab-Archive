# PATCH_RESULTS.md — Patch portability and release truth (P01)

## Declared baseline

The declared baseline is the V19.2.1 package **with line endings deliberately
normalised to LF**. This is stated explicitly because the shipped V19.2.1
`contracts/openapi.yaml` has mixed CRLF/LF endings, which is exactly what broke
the V19.2.2 patch and what the Road-Prep required to be handled deliberately.

## Change detection is content-based

A file whose only difference from the baseline is line endings is **not**
counted as changed. This matters here: the live tree contains files such as
`backend/app/db/models.py` (mixed CRLF/LF) and
`backend/app/commerce/strengths_generated.py` (pure CRLF) whose *content* is
identical to the LF-normalised baseline. Counting raw bytes would have produced
three phantom "modified" files and a patch full of line-ending churn.

Both sides of every emitted diff are LF, so the patch is portable.

## Verification

```
$ cp -r baseline_norm /tmp/p24
$ git apply --check V19_2_4_CODE.patch          # no excluded paths
-> clean, exit 0

$ git apply V19_2_4_CODE.patch
$ diff each of the 22 files against the working tree (CR-insensitive)
-> 22/22 identical, 0 differences
```

## Changed files — 7 added, 15 modified, 0 removed

```
A  backend/app/operations/reservation_identity.py
A  backend/app/planning/anchor_schedule.py
A  backend/app/planning/anchors.py
A  backend/app/planning/hard_recovery.py
A  backend/tests/test_v1923_final_code_gate.py
A  backend/tests/test_v1924_final_truth_gate.py
A  frontend/src/features/recovery/RecoveryRequiredPanel.tsx
M  backend/app/capabilities.py
M  backend/app/db/session.py
M  backend/app/integrations/mobility/snapshot_capture.py
M  backend/app/main.py
M  backend/app/operations/v9.py
M  backend/app/replanning/feasibility.py
M  backend/app/replanning/protected_commitments.py
M  backend/app/replanning/provider_snapshots.py
M  backend/app/schemas.py
M  backend/app/services.py
M  backend/db/schema.sql
M  contracts/openapi.yaml
M  frontend/src/app/V8Experience.tsx
M  frontend/src/app/v8Types.ts
M  frontend/src/generated/api.ts
```

This is the cumulative V19.2.2 → V19.2.4 change set, which is what a release
patch against the declared baseline must contain.

## Release hygiene

| Check | Result |
| --- | --- |
| `__pycache__`, `.pytest_cache`, `.ruff_cache`, `*.pyc` | excluded |
| `*.db`, `*.log`, `*.err` | excluded |
| `node_modules`, `dist`, `test-results`, `playwright-report`, `storybook-static` | excluded |
| `CHANGED_FILES.txt` generated from the real diff | yes |
| Files claimed changed but not actually changed | **none** |
| Files changed but not claimed | **none** |

## Contents of this package

* `patches/V19_2_4_CODE.patch` — the portable release patch (LF, applies clean)
* `patches/reference_starter_patch.patch` — the Road-Prep verified starter patch,
  kept as reference for the semantics that were ported
* `source/` — the 22 changed source files, as review evidence
