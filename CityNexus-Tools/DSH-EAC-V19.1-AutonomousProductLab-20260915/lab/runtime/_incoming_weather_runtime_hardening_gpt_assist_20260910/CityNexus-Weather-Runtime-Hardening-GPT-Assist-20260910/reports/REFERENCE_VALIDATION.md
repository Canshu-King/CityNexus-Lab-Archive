# Reference Validation

Source checkpoint baseline independently reproduced before hardening:

- Weather + trigger + provider targeted gate: 38 PASS
- full submitted backend: 188 passed, 1 skipped

Additional external adversarial test on the unmodified checkpoint:

- WRH-01..WRH-06: 6 FAILED

Reference hardening copy:

- WRH-01..WRH-06: 6 PASS
- WRH + WRT + weather trigger + Provider PRT/PRH + Golden/WP07 targeted: 44 PASS
- full backend printed: 194 passed, 1 skipped in 29.41s
- compileall: PASS
- combined reference patch `git apply --check`: PASS on fresh checkpoint extraction

Review-environment limitation:

- Ruff is not installed in this Linux container. The real Windows/Codex tree must run `ruff check` and `ruff format --check` before external freeze.
- The full pytest process can linger in this Linux environment after printing the complete PASS summary, a behavior seen in earlier reviews. Require a clean exit on the Windows environment.
