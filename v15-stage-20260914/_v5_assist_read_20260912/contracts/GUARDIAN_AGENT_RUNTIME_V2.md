# Guardian Agent Runtime V2

Current V4 behavior:
Guardian creates a deterministic AgentRun and executes a fixed three-tool sequence.

V5 behavior:

Guardian receives an incident and a standing JourneyMission.

It derives a RecoveryMission that preserves the standing mission's authority.

Then:

try configured Agent runtime:
    Hermes when configured
    Native DeepSeek otherwise
except external-unavailable:
    DeterministicGuardianController fallback

The AI runtime is not decorative.
It should decide what to inspect, whether to search alternatives, whether a replan is useful, and which allowed action to attempt.

The Gateway remains authoritative for policy and domain mutation.

All runtimes produce normalized:
AgentRun
AgentRunStep
tool args/results
policy decisions
outcome

This lets the UI and audit remain runtime-independent.
