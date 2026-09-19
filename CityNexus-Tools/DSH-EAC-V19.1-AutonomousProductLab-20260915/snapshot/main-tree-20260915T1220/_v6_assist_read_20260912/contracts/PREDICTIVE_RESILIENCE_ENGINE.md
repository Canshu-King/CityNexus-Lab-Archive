# Predictive Journey Resilience Engine

V5 answers:
"What should I do after a disruption exists?"

V6 should also answer:
"How likely is my Journey to survive the next few hours?"

Introduce a server-owned JourneyResilienceSnapshot.

Suggested components:

1. Commitment buffer risk
   - minutes of slack before each C4/protected anchor

2. Weather exposure
   - forecast precipitation / severe weather overlap with outdoor legs and Activities

3. Mobility sensitivity
   - how much additional travel delay can each leg absorb before the Journey becomes infeasible

4. Single-point-of-failure risk
   - Activities or connections for which no good alternative exists

5. Cost headroom
   - how much authorized budget remains for autonomous recovery

6. Route / geography exposure
   - route overlap with known disruption scopes

7. Recovery optionality
   - count and quality of feasible alternatives within the future horizon

Produce:
- overall resilience score 0..100;
- per-Activity risk;
- per-Commitment buffer;
- dominant failure modes;
- recommended preventive action;
- snapshot provenance.

Do not make the score a decorative AI number.
Use deterministic component calculations where possible and use DeepSeek for semantic interpretation/explanation.

The Agent may preemptively replan if:
expected disruption risk
× consequence
is materially greater than
switching cost + change penalty

and the action is inside the user's Autonomy Envelope.
