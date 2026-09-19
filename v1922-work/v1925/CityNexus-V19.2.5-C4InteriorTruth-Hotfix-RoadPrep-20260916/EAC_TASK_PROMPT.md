You are performing a tiny CityNexus V19.2.5 truth hotfix.

Authoritative worktree:
D:\moodle\CityNexus

Freeze V19.2.4 as Snapshot G.

Read README_FIRST.md and INDEPENDENT_REVIEW.md.

Do not start V19.3. Do not redesign anything.

One residual shared-gate defect remains:

- MID_TRIP C4 before ARRIVAL is accepted by evaluate_feasibility()
- MID_TRIP C4 after DEPARTURE is accepted
- role-less interior booking/order C4 can escape ARRIVAL/DEPARTURE boundaries

The generator already rejects these layouts; the shared deterministic gate must independently reject them too.

Use `patches/V19_2_5_C4_INTERIOR_TRUTH.patch` as a verified semantic starter.
Run git apply --check first. If live code differs, port semantics.

Required invariant:
- ARRIVAL and DEPARTURE are structural edge anchors and do not reject themselves.
- every other LOCKED_COMMITMENT activity, including MID_TRIP and role-less interior anchors,
  must lie within ARRIVAL completion and DEPARTURE start.

Add regression coverage for:
1. MID_TRIP before ARRIVAL -> reject
2. MID_TRIP after DEPARTURE -> reject
3. role-less locked activity before ARRIVAL -> reject
4. valid MID_TRIP inside -> pass
5. valid role-less locked activity inside -> pass

Then re-run:
- V19.2 contract suite
- V19.2.3 closure suite
- V19.2.4 truth suite
- new V19.2.5 tests
- authoritative broad backend regression

No new regression is allowed.

Do not spend time on frontend, OpenAPI, DeepSeek or mobile UI unless this one-file hotfix unexpectedly changes them.

Target output:
CityNexus-EAC-V19.2.5-C4InteriorTruth-Hotfix-20260916.zip

Final verdict:
BLOCKED
or
SHADOW_TRIAL_CODE_READY_PENDING_PHYSICAL_DEVICE

Stop after packaging.
