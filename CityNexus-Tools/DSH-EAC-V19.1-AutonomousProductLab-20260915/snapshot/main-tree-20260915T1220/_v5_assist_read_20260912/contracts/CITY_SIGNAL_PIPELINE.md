# City Signal Pipeline V5

Purpose: make the Guardian observe the city instead of relying on a UI script to inject events.

Recommended flow:

Provider Watcher
→ ProviderObservation
→ Normalization
→ Incident Fingerprint
→ Event / Risk Evidence
→ Guardian Pulse

Weather:
- reuse Open-Meteo refresh and provider-verified weather ingestion;
- store capture timestamp and affected activity/place evidence.

Mobility:
- capture travel estimates for near-term active-plan legs;
- compare with baseline/frozen previous evidence;
- derive TRAFFIC_DELAY from meaningful deltas;
- store provider provenance;
- never perform live provider calls inside deterministic feasibility.

Simulation:
the demo signal source must implement the same provider observation interface.
A fixture may switch from NORMAL to DISRUPTED, but the UI must not directly create trusted Events.

Suggested semantic incident identity:
journey + provider + disruption_class + scope + time_bucket

The same incident may accumulate new evidence without spawning a new recovery every refresh.
