# FINAL_TRUTH_GATE_REPORT.md — CityNexus V19.2.5 C4 Interior-Truth Hotfix

## Verdict

**SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE**

One narrow shared-gate truth gap remains closed. The V19.2 contract stays
61/61, the V19.2.3 and V19.2.4 closure suites stay 13/13 and 12/12, a new
7-test V19.2.5 suite passes, and the broad regression has **zero new failures**.

## Scope discipline

* Snapshot G (V19.2.4) was frozen first, SHA-256 verified.
* V19.3 was **not** started. Nothing was redesigned.
* Exactly **one** production file changed semantically, plus one new test file.
* Per the task, frontend, OpenAPI, DeepSeek and mobile UI were **not** re-run —
  this one-file hotfix cannot affect them, and the task explicitly said not to
  spend time there.

## Snapshot G continuity

| Check | Result |
| --- | --- |
| Delivered V19.2.4 ZIP SHA-256 | `b6c521c1163791146bdf0989bca0d40f61c2c865862eabe6156274a7eeb0b017` |
| Independent review's expected value | identical |
| Live tree vs frozen Snapshot G source | 22/22 files identical |

The frozen artefact reviewed by the independent party is byte-for-byte the
artefact this hotfix is applied to.

## The defect

The shared deterministic feasibility gate is the defence-in-depth path for
plans that were **imported, persisted, edited or left stale** — plans the
generator never produced. It must reject an impossible C4 layout on its own.

Snapshot G did not. Reproduced before the fix against the exact Snapshot G code:

```
ARRIVAL 12:30 + MID_TRIP 10:00          -> passed = true, failures = []   WRONG
DEPARTURE 15:30 + MID_TRIP 17:00        -> passed = true, failures = []   WRONG
ARRIVAL 12:30 + role-less booking 10:00 -> passed = true, failures = []   WRONG
```

### Root cause

`evaluate_feasibility()` built `anchor_keys` for **every** `LOCKED_COMMITMENT`
and then skipped **every** anchor activity when enforcing the ARRIVAL/DEPARTURE
boundaries. Skipping is only correct for the structural edge anchors
(`ARRIVAL`, `DEPARTURE`), which define those boundaries and cannot constrain
themselves. Interior locks — `MID_TRIP` and role-less booking/order anchors —
were skipped too, so they could sit outside the usable city interval.

## The fix

One file, `backend/app/replanning/feasibility.py`, changing the skip rule from
key-membership to **role-aware** logic:

```python
anchor_roles = {
    commitment.activity_key: role for commitment, role in locked_specs
}
...
item_anchor_role = anchor_roles.get(item_key, "")
if item_anchor_role in {"ARRIVAL", "DEPARTURE"}:
    continue
```

Now:

* `ARRIVAL` and `DEPARTURE` remain structural edge markers and do not reject
  themselves;
* every other `LOCKED_COMMITMENT` activity — `MID_TRIP` **and** role-less
  booking/order anchors — must lie within
  `[ARRIVAL completion, DEPARTURE start]`;
* the rules are inclusive at the boundaries (an interior anchor starting
  exactly when ARRIVAL completes is valid).

No other behaviour was touched. No C4 protection was weakened.

## Verified behaviour

Independent probe `probes/v1925_c4_interior_probe.py` after the fix
(`evidence/v1925_c4_interior_probe.json`):

| Case | Result |
| --- | --- |
| MID_TRIP before ARRIVAL | rejected `C4_ACTIVITY_BEFORE_ARRIVAL` |
| MID_TRIP after DEPARTURE | rejected `C4_ACTIVITY_AFTER_DEPARTURE` |
| role-less lock before ARRIVAL | rejected `C4_ACTIVITY_BEFORE_ARRIVAL` |
| valid MID_TRIP inside | accepted |
| valid role-less lock inside | accepted |

`5/5 PASS`, exit code 0.

The prior V19.2.4 truth probe remains **4/4 PASS**
(`evidence/v1924_truth_probe_regression.json`, exit code 0).

## Retest summary

| Suite | Result |
| --- | --- |
| V19.2 contract | **61/61** |
| V19.2.3 closure | **13/13** |
| V19.2.4 truth | **12/12** |
| New V19.2.5 interior truth | **7/7** |
| Gate suites combined | **93/93** |
| Broad backend regression | **703 passed / 2 pre-existing / 15 skipped, 0 new** |
| Shared-gate probes | V19.2.5 5/5, V19.2.4 4/4 |

## Patch portability

`patches/V19_2_5_HOTFIX.patch` is a single-file LF patch against Snapshot G:

```
git apply --check  -> exit 0, no excluded paths
git apply          -> clean
post-apply file    -> byte-identical to the working tree
```

Verified against a reconstructed exact Snapshot G
(`baseline_norm` + `V19_2_4_CODE.patch`).
Evidence: `evidence/patch_verification.txt`.

## Next steps (not part of this code gate)

Per the Road-Prep, an independent WorkBuddy Snapshot-G/H delta gate should
follow, and the user may run the OPPO **plumbing** precheck (HTTPS/PWA/GPS/SSE)
in parallel. A full multi-anchor outdoor Shadow Journey must **not** be called
accepted before that delta gate agrees.

## Explicit non-claims

* No real payment was executed.
* **No physical-device testing** was performed in this round; the phone
  plumbing precheck is a separate activity run by the user.
* Frontend, OpenAPI, DeepSeek and mobile UI were deliberately not re-run: a
  single-file backend gate change cannot affect them.
* The two remaining broad-suite failures are pre-existing contradictory test
  expectations; production truth was not weakened to satisfy them.
