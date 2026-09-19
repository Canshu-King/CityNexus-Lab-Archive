# V18.2 test harnesses

Six suites. 93 assertions. **88 PASS / 5 FAIL / 0 NOT_TESTED.**
The five failures are the three real defects (F1, F2, F3) — see
`../WORKBUDDY_V18_2_AGENT_SAFETY_REPORT.md`.

| File | Family | Kind | Assertions | Needs |
|---|---|---|---|---|
| `test_authority_matrix.py` | A/B deterministic | pure, offline | 27 | repo on `sys.path` |
| `blackbox_agent_safety.py` | B + E | live HTTP | 22 | backend + sqlite path |
| `runtime_truth.py` | A | live HTTP | 6 | backend |
| `semantic_boundary.py` | D | live HTTP + offline | 17 | backend + repo path |
| `multistep_agent.py` | C | live HTTP | 6 | backend |
| `frontend_runtime_truth.mjs` | F | Playwright | 15 | frontend URL + `@playwright/test` |

## Run order

```bash
# 1. deterministic, no server needed
python tests/test_authority_matrix.py --repo repo_copy/backend

# 2-5. live suites (backend must be up on 8021)
python tests/blackbox_agent_safety.py --base-url http://127.0.0.1:8021 --db citynexus_v182.db
python tests/runtime_truth.py         --base-url http://127.0.0.1:8021
python tests/semantic_boundary.py     --base-url http://127.0.0.1:8021 \
                                      --repo repo_copy/backend --db citynexus_v182.db
python tests/multistep_agent.py       --base-url http://127.0.0.1:8021

# 6. frontend (frontend must be up on 4173)
node tests/frontend_runtime_truth.mjs --base http://127.0.0.1:4173
```

Each suite writes its own `evidence/results_*.json`. Merge them with the
snippet in `../WORKBUDDY_V18_2_AGENT_SAFETY_REPORT.md` §6.

## Conventions

- `record(id, name, expected, actual, status, evidence=None)` — every suite
  uses the same shape, so the JSON merges without transformation.
- Statuses are `PASS` / `FAIL` / `NOT_TESTED`. `NOT_TESTED` means a
  precondition was missing (e.g. no fixture), **not** a soft pass.
- Suites are **self-seeding**: each calls `POST /api/v1/demo/reset` at
  bootstrap. Run them one at a time; they are not parallel-safe against the
  same database.
- Live suites assert against **real entities** (a real Booking + Commitment, a
  real ReplanProposal, a locked C4 activity) — never stubs.

## What the suites deliberately do NOT do

- No full pytest run (out of scope per the task book).
- No re-audit of V13–V17.
- No native-Hermes end-to-end trigger: the gateway profile pins MCP to the
  authoritative backend on 8000, so a real run would write the main DB. See
  `../CODEX_HANDOFF_AFTER_V18_2.md` §6.

## Applying to the repo

`../patches/V18_2_TESTS_ONLY.patch` adds these files under
`tests/v18_2_agent_safety/`. Tests only — `git apply --check` verified clean.
