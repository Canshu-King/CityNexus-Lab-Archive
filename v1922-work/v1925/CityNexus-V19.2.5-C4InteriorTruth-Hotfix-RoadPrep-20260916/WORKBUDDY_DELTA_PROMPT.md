Read-only targeted delta only.

Freeze V19.2.4 as Snapshot G.
If V19.2.5 lands, freeze it as Snapshot H.

Do not modify the main tree.
Do not rerun the historical full corpus.

Run `probes/v1925_c4_interior_probe.py` against G first.
Expected on G: the first three cases reproduce the defect.

Run the same probe against H.
Expected on H: all five cases PASS.

Also confirm:
- previous V19.2.4 F01-F04 truth probe remains green;
- no changes outside the intended feasibility/test surface unless explicitly justified;
- broad-regression evidence reports zero new failures.

Final verdict:
BLOCKED
or
SNAPSHOT_H_ACCEPTED_FOR_PHYSICAL_TRIAL_PRECHECK
