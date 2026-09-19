# Real City Discovery

Goal:
A Journey Agent should be able to discover real replacement places rather than choosing only from the seeded demo catalog.

Flow:

user / standing mission
→ semantic preference
→ geographic search envelope
→ Nominatim or Journey center grounding
→ Overpass category search
→ normalized RealPlaceCandidate
→ DeepSeek semantic ranking
→ server-side provider/geometry/opening validation
→ selected candidates materialized as Place / CityService
→ CP-SAT Solver V2
→ deterministic feasibility

Candidate fields should include:
- provider_key
- external_id
- name
- category
- coordinates
- tags
- opening_hours raw/normalized when available
- source URL/reference metadata if appropriate
- captured_at
- distance from Journey corridor
- confidence/evidence summary

AI can rank and interpret real POIs.
The server owns external identity, geometry and captured provider facts.

Cache aggressively enough to respect public provider fair-use policies.
