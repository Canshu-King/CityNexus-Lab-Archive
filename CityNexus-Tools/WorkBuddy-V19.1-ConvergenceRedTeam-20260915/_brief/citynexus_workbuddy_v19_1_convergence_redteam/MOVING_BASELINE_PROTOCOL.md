# Moving Baseline Protocol

Codex may still be changing the main worktree.

Do not test a moving directory directly for the entire run.

Take:

- Snapshot A at task start.
- Snapshot B once, roughly halfway through the task or after a major Codex state change.

Each snapshot must record:
- timestamp
- source file mtimes/hash summary
- backend import status
- relevant capability file list

Run the same focused contract tests against A and B.

Do not:
- repeatedly recopy the main tree;
- modify the main tree;
- conclude a defect remains if Snapshot B proves it was fixed.

Final handoff must classify every finding:

- FIXED_IN_CURRENT
- STILL_REPRODUCIBLE
- REGRESSED
- NEW
- INCONCLUSIVE
