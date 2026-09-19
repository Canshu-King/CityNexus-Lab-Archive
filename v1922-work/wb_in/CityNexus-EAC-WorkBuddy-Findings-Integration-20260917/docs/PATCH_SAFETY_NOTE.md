# WorkBuddy shadow-patch safety note

WB-O1 includes four shadow patches:

- P1 booking import robustness
- P1b i18n consumer keys
- P2 AI planning honesty gate
- P3 Copilot consumer language

They are useful as design/code references.

DO NOT blindly run:

`git apply <patch>`

against the current repository.

Reasons:

1. They were generated against an isolated ~01:15 baseline.
2. EAC may have changed the same files afterward.
3. The patch files are UTF-16 LE.
4. Their diff headers contain absolute WorkBuddy Windows paths rather than clean
   repository-relative paths.
5. P1/P1b/P2/P3 implement frontend safeguards, but some root causes still need
   authoritative backend fixes.

Correct procedure:
- inspect current source;
- compare the intent/hunks;
- manually port or regenerate a clean patch against current HEAD/worktree;
- run current build/E2E;
- verify the visible defect is actually gone.

Especially:
- AI planning success must be enforced by artifact truth, not only frontend copy;
- booking amount preservation must be verified through backend draft/confirm;
- Copilot raw enums must be removed across all traveler surfaces, not only one component.
