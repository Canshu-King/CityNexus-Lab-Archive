# SNAPSHOT_FREEZE.md — Snapshot E and Snapshot F

## Snapshot E — frozen V19.2.2

```
CityNexus-EAC-V19.2.2-RealPhone-CodeGate-Final-20260915.zip
```

Frozen at the start of this round, before any V19.2.3 edit. A SHA-256 manifest
of all 47 files is recorded in `evidence/SNAPSHOT_E_MANIFEST.json`, so the
reviewed artefact cannot be silently rewritten.

Snapshot E's own verdict was
`SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE`; the independent review
downgraded it to `BLOCKED_PENDING_FINAL_TEMPORAL_RECOVERY_MIGRATION_CLOSURE`
and raised seven blockers. This round closes those blockers and produces
**Snapshot F**.

## Snapshot F — this package

```
CityNexus-EAC-V19.2.3-FinalShadowTrial-CodeGate-20260915.zip
```

Contains:

* `source/` — the 21 changed source files
* `patches/V19_2_3_CODE.patch` — portable LF patch, `git apply --check` clean
  against the declared normalised V19.2.1 baseline with no excluded paths
* `evidence/` — raw machine-readable output for every claim
* the gate reports listed in `PACKAGE_INVENTORY.txt`

## Baseline declaration

The declared baseline for the patch is the V19.2.1 package **with line endings
normalised to LF**. This is stated explicitly rather than left implicit,
because the shipped V19.2.1 `contracts/openapi.yaml` has mixed CRLF/LF endings
and that is exactly what broke the V19.2.2 patch.

## Boundary

No V19.3 work was started. No broad product features were added. The only new
endpoint is the governed recovery acknowledgement the review required.
