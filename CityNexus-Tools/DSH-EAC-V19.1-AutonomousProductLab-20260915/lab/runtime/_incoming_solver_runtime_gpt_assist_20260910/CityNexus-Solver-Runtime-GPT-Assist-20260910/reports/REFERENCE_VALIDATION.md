# Reference Solver Prep Validation

The Assist package includes a dependency-free semantic oracle and an optional CP-SAT adapter reference.

Validated locally against the Weather Hardening checkpoint codebase:

```text
python -m pytest -q tests/test_solver_reference_contract.py tests/test_ortools_optional_boundary.py tests/test_solver_runtime_policy.py
15 passed, 2 skipped
```

The two skips are real OR-Tools solve checks (reference parity and stable semantic tie-breaking) because OR-Tools is intentionally not installed in the GPT review environment. The missing-dependency branch was executed and passed as a controlled `ORToolsUnavailable` boundary.

Also validated:

```text
python -m compileall -q \
  app/planning/solver_contract.py \
  app/planning/reference_replan_solver.py \
  app/planning/ortools_replan_solver.py
PASS
```

What this proves:

- immutable/JSON-friendly solver input contract works;
- missing frozen travel facts fail closed rather than becoming zero minutes;
- budget/opening/C4-buffer semantics in the reference oracle work;
- Top-K reference assignments are deterministic and unique;
- OR-Tools absence/disabled/UNKNOWN states are controlled fallback conditions;
- unexpected programming errors are not silently converted into successful fallback;
- solver-attempt provenance is stable and tied to the exact mobility snapshot;
- the supplied CP-SAT reference module is syntactically valid.

What this does **not** prove:

- real OR-Tools CP-SAT solve in the user's Windows repository;
- runtime wiring into `generate_replan()`;
- all ORT-01..20 integration gates.

Codex must install the optional solver dependency in its environment, run the real CP-SAT parity test, then perform the runtime integration and full regressions.
