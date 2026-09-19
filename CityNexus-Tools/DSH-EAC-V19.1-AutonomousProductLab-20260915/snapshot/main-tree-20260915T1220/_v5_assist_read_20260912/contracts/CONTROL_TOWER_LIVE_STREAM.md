# Control Tower Live Operations Stream

Recommended transport: Server-Sent Events.

SSE is a projection/notification channel, not truth.

Persist first, publish second.

Event examples:
- city_signal_received
- incident_updated
- guardian_wake
- mission_compiled
- agent_run_started
- agent_tool_called
- impact_resolved
- solver_candidates_ready
- policy_decision
- domain_mutation
- twin_refreshed

On reconnect:
client fetches REST state and resumes from persisted sequence/event ID.

The UI should visibly distinguish:
Observation / AI Inference / Optimization / Policy / Mutation.

No fake delays or timer-based agent narration.
