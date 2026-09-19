# 13 - Non-goals and Risk Controls

## Deliberate MVP non-goals

- real money movement;
- production-grade payment compliance;
- real hotel/rail/air booking;
- a city-scale routing engine;
- production identity federation;
- multiple real AI vendors at once;
- microservices/Kubernetes;
- background event streaming infrastructure;
- perfect recommendation ML;
- completion of all 138 requirements before the first demo.

These are not deleted from full product scope when the requirement baseline includes them; they are simply deferred or simulated for the vertical slice.

## Highest implementation risks

### R1 - Replanning becomes an uncontrolled optimisation project
Control: bounded candidate families, deterministic fixtures, explicit hard gates, fixed score weights, stop when canonical vertical slice works.

### R2 - Mock behavior is mistaken for real integration
Control: UI labels and implementation ledger use `SIMULATED`; provider ports preserve replacement path.

### R3 - AI leaks into authoritative decisions
Control: AI consumes feasible candidate facts after deterministic checks; tests run with AI disabled.

### R4 - Domain drift from frozen baseline
Control: WP00 read-only reconciliation; do not modify frozen YAML to fit code.

### R5 - 138 requirements cause scope explosion
Control: status ledger + progressive batches after MVP; evidence required for IMPLEMENTED.

### R6 - Demo becomes fragile because of network dependencies
Control: canonical scenario must be fully offline-capable with deterministic mock adapters.
