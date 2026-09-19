# CityNexus Solver Runtime GPT Assist - 2026-09-10

Purpose: hand the next GPT Web Codex window a verified Weather Runtime freeze verdict plus concrete, dependency-light scaffolding for the first real OR-Tools candidate generator.

This package does **not** claim that OR-Tools runtime is already integrated. It deliberately separates:

1. externally accepted Weather Runtime facts;
2. a pure immutable Solver contract;
3. a dependency-free reference enumerator used as a semantic oracle;
4. an optional OR-Tools CP-SAT reference adapter;
5. the integration and acceptance gates Codex must satisfy in the real Windows repository.

The real product authority remains:

```text
Frozen external facts
-> candidate generator (OR-Tools or deterministic fallback)
-> materialize candidate PlanVersion
-> CityNexus deterministic feasibility gate
-> verified scoring / ReplanDiff
-> Traveler confirmation
-> acceptance-time revalidation
```

Do not allow OR-Tools to become Domain truth, feasibility authority, mobility provider, weather provider, or acceptance authority.
