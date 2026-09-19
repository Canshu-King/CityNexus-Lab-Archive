# Snapshots, moving-baseline protocol, and the authorised delta check

The main tree is being actively edited by Codex throughout this run. Every finding is therefore
bound to a timestamped read-only snapshot, and exactly **one** targeted delta check was performed,
as the task prompt allows.

All snapshots are taken with `PYTHONDONTWRITEBYTECODE=1` from a narrow include list; the main tree
is never written to (verified below).

---

## Snapshot ledger

| Snapshot | Taken | Files | `import app.main` | `capabilities.py` | Missing symbols |
|---|---|---|---|---|---|
| **A** | 2026-09-15 **17:29:11** | 341 | ✅ ok | 23,668 B / `9b68b17997f4cf4e` | `{}` |
| **B** | 2026-09-15 **17:50:44** | 341 | ✅ ok | 23,668 B / `9b68b17997f4cf4e` | `{}` |

For reference, the V19.1 round's baseline:

| Snapshot | Taken | `capabilities.py` | focused suite |
|---|---|---|---|
| FINAL_V19 (B₁) | 13:05:57 | 15,283 B / `7e3ff4cb3a85b7b6` | 37 P / 106 F / 45 S |
| Codex V19.1 (C) | 13:47:07 | 19,890 B / `b342df348c0d62a7` | 119 P / 54 F / 15 S |
| **Codex V19.2 (A)** | **17:29:11** | **23,668 B / `9b68b17997f4cf4e`** | **161 P / 14 F / 13 S** |

## Watched-file drift since the V19.1 baseline

| File | V19.1 (C) | V19.2 (A) | mtime |
|---|---|---|---|
| `backend/app/capabilities.py` | `b342df348c0d62a7` | `9b68b17997f4cf4e` | 17:28:33 |
| `backend/app/main.py` | `e357ac67260a7794` | `f352ff55fd1f3c6a` | 15:34:52 |
| `backend/app/services.py` | `39883320e3ae5901` | `bcd34f940a1d98d2` | 17:26:45 |
| `backend/app/replanning/feasibility.py` | `8a0de9106818725d` | `8a0de9106818725d` | **unchanged** (13:16:26) |
| `frontend/src/styles.css` | `f6bdac67feb82894` | `a1e5ff32f492efd4` | 13:54:24 |

`feasibility.py` is byte-identical to the V19.1 baseline. That is why the `_accessibility_metadata`
whitelist gap survives into V19.2 (see `PATCH_VALIDATION.md`).

## A → B drift

`capabilities.py`, `services.py`, `feasibility.py` and every other watched file are
**byte-identical** between A and B. Five files moved, taken straight from the two snapshot manifests
(`evidence/snapshot_a.json` / `_b.json`) rather than from a directory walk:

| File | A | B | mtime (B) | bytes |
|---|---|---|---|---|
| `backend/app/capabilities.py` | `9b68b17997f4cf4e` | `9b68b17997f4cf4e` | 17:28:33 | 23,668 |
| `backend/app/services.py` | `bcd34f940a1d98d2` | `bcd34f940a1d98d2` | 17:26:45 | 36,621 |
| `backend/app/replanning/feasibility.py` | `8a0de9106818725d` | `8a0de9106818725d` | 13:16:26 | 32,817 |
| `backend/app/main.py` | `f352ff55fd1f3c6a` | **`c17f74c4867a1a1d`** | 17:29:43 | 364,648 → 364,908 |
| `backend/app/operations/v9.py` | `e3427bffe7a886fa` | **`8a18af376260d98b`** | 17:40:21 | 47,157 → 48,580 |
| `backend/app/db/models.py` | `813a2e4b19e7c383` | **`787e7b06b2c06fd4`** | 17:30:35 | 57,237 → 57,308 |
| `backend/app/db/session.py` | `5b55c28024f1bc58` | **`6a371bef3df0136e`** | 17:30:35 | 23,862 → 24,402 |
| `backend/db/schema.sql` | `af58107ee942e1f9` | **`f20ded6bcddcf9c3`** | 17:30:35 | 38,192 → 38,334 |

Codex changed `main.py` 32 seconds after Snapshot A was frozen, the three DB-layer files 50 seconds
after that, and `v9.py` ten minutes later. That is exactly the condition the moving-baseline
protocol exists for.

> **Correction.** An earlier revision of this file listed only `main.py` and `v9.py`. That came from
> a `find -newermt` sweep over `backend/app` instead of from the snapshot manifests, and it missed
> `db/models.py`, `db/session.py` and `db/schema.sql` because they had already been updated **before**
> the sweep ran. Reading the manifests is the authoritative method; the sweep is a cross-check, not
> a source. Recorded here rather than silently edited, because the same mistake would under-report
> drift in any round that edits the DB layer.

### Does the DB-layer change affect any verdict?

Snapshot B was taken at 17:50:44, i.e. **after** all three DB files moved, so B runs on the new
models, the new session factory and the new schema. Every probe was re-run against B and produced
identical results (table below). `models.py` grew by 71 bytes and `schema.sql` by 142 bytes, which
is consistent with an added column rather than a structural rewrite — but the schema delta was not
individually audited this round, so treat it as a residual unknown, not as "no impact".

## Result of the delta check

The two changed files (`main.py`, `v9.py`) are precisely the ones the C4, feasibility and
lifecycle probes exercise. All three were re-run against B:

| Probe | A | B |
|---|---|---|
| `feasibility_truth` — `generator_produced_plans_the_validator_rejects` | `[]` | `[]` |
| `c4_lifecycle` — `anchors_blocking_existing_plans` | 4 of 4 | **4 of 4** |
| `c4_lifecycle` — `any_start_5xx` | `false` | `false` |
| `c4_lifecycle` — `one_confirmation_one_commitment` | `true` | `true` |
| `stale_candidates` — `journey_still_running_on_expired_evidence` | `true` | `true` |
| `stale_candidates` — `experience_flags_staleness` | `false` | `false` |
| focused suite | 14 F / 161 P / 13 S | **14 F / 161 P / 13 S** |

**No finding changed between A and B.** The two `main.py` / `v9.py` edits did not touch any of
the behaviours reported here. Every verdict in this round is therefore stable across a 21-minute
window of active concurrent editing.

## Main-tree integrity

No lab artefact exists anywhere under `D:\moodle\CityNexus`. The lab writes only to:

- `D:\moodle\CityNexus-Tools\WorkBuddy-V19.2-RealPhoneShadowTrial-20260915\snapshot_{a,b}\`
- `...\evidence\` (including `evidence\_db\*.db`, the throwaway SQLite files)
- `...\_scratch\` (patch apply-checks)

The web lab's `node_modules` is a directory junction to the main tree's `node_modules` (read-only
reuse, `mklink /J`, no copy). Vite's dependency cache is redirected to `%TEMP%\v192-vite-cache`.

Snapshot copies are taken with `PYTHONDONTWRITEBYTECODE=1` and the harness sets it again in-process,
so importing `app.main` from a snapshot never writes a `.pyc` back into the main tree.

## Method notes worth carrying forward

1. **`importlib.import_module` caches on the dotted name.** A first version of
   `v192_cross_snapshot_numeric.py` loaded three snapshots in one process and silently received
   the *same* module three times, producing a plausible-looking table in which all three columns
   were identical. The fix is to purge `sys.modules` entries matching `app` / `app.*` before each
   load and to assert the loaded `__file__` lives under the intended snapshot. **Any
   cross-snapshot comparison in one process needs this guard.**
2. **The V19.1 probes had a hardcoded lab path.** They were made self-locating
   (`Path(__file__).resolve().parent.parent`) with a `V192_LAB` / `V192_EVID` override, so the same
   file runs against any round's lab.
3. **`validate_plan_feasibility` moved from `app.replanning.feasibility` to `app.services`.**
   Probes written against the old import fail with `ImportError` and must be updated.
4. **The host runs a system proxy.** `curl` to `127.0.0.1` returns 502 through it; local checks
   need `--noproxy '*'`. Playwright must be forced direct.
5. **A launcher process that exits takes its children with it.** `tools/start_web_lab.py` starts
   the servers and returns; the servers die with it. The lab servers are therefore launched as two
   independent long-running background tasks instead.
