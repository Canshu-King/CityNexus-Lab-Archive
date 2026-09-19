# PATCH_RESULTS.md — Hotfix patch portability and release truth

## Scope

This is a **one-file** semantic hotfix plus one new regression test file.

```
A  backend/tests/test_v1925_c4_interior_truth.py
M  backend/app/replanning/feasibility.py
```

No other file was touched. `CHANGED_FILES.txt` is generated from the real
content diff against Snapshot G.

## Baseline: Snapshot G, verified

The hotfix patch is declared against Snapshot G:

```
CityNexus-EAC-V19.2.4-FinalTruth-CodeGate-20260915.zip
SHA-256 b6c521c1163791146bdf0989bca0d40f61c2c865862eabe6156274a7eeb0b017
```

That hash matches the value in the independent review exactly, so the artefact
the review examined is the artefact patched here.

## Verification

The full Snapshot G tree was reconstructed
(`baseline_norm` + `V19_2_4_CODE.patch`), then:

```
$ git apply --check V19_2_5_HOTFIX.patch
-> exit 0, no excluded paths

$ git apply V19_2_5_HOTFIX.patch
-> clean

$ diff post-apply feasibility.py vs the working tree (CR-insensitive)
-> identical
```

## Patch content

The diff contains exactly two changes, both in
`backend/app/replanning/feasibility.py`:

```
-    anchor_keys = {commitment.activity_key for commitment, _role in locked_specs}
+    anchor_roles = {
+        commitment.activity_key: role for commitment, role in locked_specs
+    }
...
-        if item_key in anchor_keys:
+        # ARRIVAL and DEPARTURE are structural edge markers and therefore do
+        # not constrain themselves. Every interior C4 activity, including
+        # MID_TRIP and role-less booking/order locks, must still live inside
+        # those structural boundaries.
+        item_anchor_role = anchor_roles.get(item_key, "")
+        if item_anchor_role in {"ARRIVAL", "DEPARTURE"}:
```

No unrelated hunk, no formatting churn, no line-ending churn.

## Release hygiene

| Check | Result |
| --- | --- |
| `__pycache__`, `.pytest_cache`, `.ruff_cache`, `*.pyc` | excluded |
| `*.db`, `*.log`, `*.err` | excluded |
| `node_modules`, `dist`, `test-results`, `playwright-report` | excluded |
| `CHANGED_FILES.txt` truthful | yes — 1 added, 1 modified, 0 removed |
| Files claimed changed but not actually changed | **none** |
| Files changed but not claimed | **none** |

## Contents

* `patches/V19_2_5_HOTFIX.patch` — the portable single-file hotfix
* `patches/reference_starter_patch.patch` — the Road-Prep verified starter patch
  (identical semantics; kept as reference)
* `source/` — the 2 changed source files
