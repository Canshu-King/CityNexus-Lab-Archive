# CityNexus V19.2 Real-Phone Trial Road-Prep

Date: 2026-09-15

## Purpose

This package supersedes the previous V19.1 convergence prompt for the next main-tree implementation round.

The goal is **not** to add another broad feature wave. The goal is to make the current product safe and coherent enough for the first real-phone **SHADOW** trial.

Authoritative worktree:

```text
D:\moodle\CityNexus
```

Authoritative baseline for this round:

```text
CityNexus-V19.1-Capability-Evidence-LiveUX-20260915.zip
```

Independent read-only red-team evidence:

```text
CityNexus-WorkBuddy-V19.1-ConvergenceRedTeam-20260915.zip
```

## Read order

1. `BASELINE_AUDIT.md`
2. `DEFECT_MATRIX.md`
3. `PATCH_PORT_MATRIX.md`
4. `TRIAL_READINESS_GATE.md`
5. `ACCEPTANCE_MATRIX.md`
6. `CODEX_TASK_PROMPT.md` or `WORKBUDDY_TASK_PROMPT.md`
7. `VERIFICATION.md`
8. `RUNBOOK.md`

## Critical rule

Do **not** blindly apply any patch in this package.

The patches are reviewed starting points. Port semantically against the live main tree, inspect surrounding code first, and preserve current contracts/state-machine behavior unless this package explicitly calls for a change.

## Current release decision

- Phone UI/PWA alpha: already usable for local-device testing.
- Real-city shadow trial: **BLOCKED only by the V19.2 gate in this package.**
- Real payment / production reliance: out of scope for V19.2.

## Target output

```text
CityNexus-V19.2-RealPhone-Trial-Gate-20260915.zip
```

The final V19.2 package must contain fresh release-truth files and a phone-trial runbook. Do not leave top-level V18.3 status files in a V19.2 package.
