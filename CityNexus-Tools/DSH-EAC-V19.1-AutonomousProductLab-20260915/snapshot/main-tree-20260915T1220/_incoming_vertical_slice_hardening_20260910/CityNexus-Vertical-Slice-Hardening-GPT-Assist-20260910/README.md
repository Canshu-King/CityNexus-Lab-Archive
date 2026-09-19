# CityNexus Vertical Slice Hardening GPT Assist - 2026-09-10

Start with:

1. `REVIEW_FINDINGS.md`
2. `CODEX_START_HERE.md`
3. `CODEX_ONE_SHOT_PROMPT.txt`

Patches are intentionally split so the real Windows worktree can be probed with tests before implementation is merged:

```text
patches/01_TEST_ONLY_VERTICAL_SLICE_HARDENING.patch
patches/02_BACKEND_SEMANTIC_HARDENING.patch
patches/03_FRONTEND_VERTICAL_SLICE_HARDENING.patch
```

`ALL_HARDENING_REFERENCE.patch` is for inspection/convenience, not an instruction to blindly apply everything.

Backend GPT review-copy validation:

```text
new targeted gate: 3 passed
full backend:       157 passed, 1 skipped
compileall:         PASS
```

Frontend changes are prepared but require Windows `npm run build` and `npm run test:e2e` before acceptance.

Future work is pre-designed under `contracts/` so Codex does not need to burn time rediscovering provider boundaries after this gate freezes.

Helper tools:

```text
tools/run_vertical_slice_hardening_gate.ps1
tools/verify_openapi_parity.py
tools/make_review_checkpoint.ps1
tools/fresh_extract_backend_smoke.ps1
```

These scripts are deliberately non-destructive. The packaging helpers exclude generated databases, dependency directories, caches, and ZIP debris, then require a fresh-extract backend smoke before a new checkpoint is reported as reproducible.
