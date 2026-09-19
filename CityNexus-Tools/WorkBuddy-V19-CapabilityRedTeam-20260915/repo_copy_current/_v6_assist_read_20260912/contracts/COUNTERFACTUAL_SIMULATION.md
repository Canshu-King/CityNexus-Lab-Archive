# Counterfactual Journey Simulation

Build a small scenario engine over the frozen JourneyTwin.

Examples:
- rain starts 30 minutes earlier;
- one route leg takes +10 / +20 / +30 minutes;
- one mutable Place closes;
- one candidate replacement becomes unavailable.

For each scenario:
- clone facts into an isolated simulation context;
- never mutate Domain Truth;
- run CP-SAT Solver V2;
- record feasible / infeasible;
- record protected Commitment preservation;
- compute recovery cost and schedule drift.

Aggregate into the Journey Resilience Snapshot.

Keep this bounded and deterministic:
- small scenario family;
- fixed seeds if sampling is used;
- strict runtime budget.

This is not a second planning engine.
It is a predictive use of the existing Twin + Solver.
