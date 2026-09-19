# 11 - UI and Demo Flow Contract

This is the minimum coherent UI, not a visual-design specification.

## Navigation

```text
Dashboard
  -> Create Journey
  -> Journey Detail
      -> Candidate Plans
      -> Active Journey
          -> Booking / Payment
          -> Demo Event Injection
          -> Replan Proposal
          -> Journey History
          -> AI Copilot
```

## Screen responsibilities

### Dashboard
- list journeys and status;
- create a journey;
- open current active journey.

### Create Journey
Fields:
- city;
- date/time window;
- budget;
- planning mode;
- preference chips/weights;
- hard and soft constraints.

Primary action: `Generate Plans`.

### Candidate Plans
Show 2-3 cards with:
- activity timeline;
- total cost;
- estimated travel;
- utility score;
- major trade-offs;
- select action.

### Active Journey / JourneyTwin
Show:
- journey status;
- current activity;
- next activities;
- upcoming commitments;
- latest event/degraded indicator;
- start/complete activity controls for demo.

### Booking / Payment Simulation
Clearly label as `DEMO SIMULATION`.
Show booking state, payment state and resulting commitment level.

### Event Injection
Clearly label as `DEMO ONLY`.
Preset button: `Close Tech Art Center at 13:10`.
Do not make the evaluator type JSON during a presentation.

### Replan Proposal
Must make CityNexus's value visible:
- what changed;
- why;
- what was preserved;
- hard constraints status;
- score breakdown;
- before/after activity timeline;
- Accept / Reject.

### History
Show chronological events: create, plan select, booking, payment, journey start, disruption, proposal, acceptance.

### Copilot
Do not hide whether it is in AI or fallback mode.
AI text must be visually subordinate to verified plan/status facts.

## Demo script

1. Open seeded `One Day in Nexus City` journey.
2. Show selected plan and 15:30 River Cruise.
3. Simulate booking/payment and show LOCKED commitment.
4. Start journey.
5. Inject Tech Art Center closure.
6. Show detected event and `Replan available` state.
7. Open proposal and point to preserved River Cruise.
8. Compare score and changes.
9. Accept.
10. Show new active PlanVersion and history.
11. Toggle AI disabled; show deterministic fallback remains functional.
