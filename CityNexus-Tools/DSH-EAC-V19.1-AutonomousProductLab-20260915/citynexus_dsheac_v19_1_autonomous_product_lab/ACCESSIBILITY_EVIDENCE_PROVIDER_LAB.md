# Accessibility Evidence Provider Lab

Goal: help V19 move from “we know the traveler needs step-free access” to
“we have bounded evidence about this place/route”.

Use existing CityNexus provider architecture first.

Research and prototype a conservative accessibility evidence adapter using
available provider/frozen data. If internet is available, use authoritative
provider documentation / OpenStreetMap tagging documentation as research input.

Candidate evidence concepts may include, when actually present:

- `wheelchair=yes/no/limited`
- `toilets:wheelchair`
- `ramp`
- `elevator`
- `highway=steps`
- `step_count`
- `kerb`
- entrance/door/access tags
- route/path metadata actually returned by existing providers

Do NOT infer:

- elevator exists because a building is modern;
- wheelchair accessible because `wheelchair` tag is absent;
- step-free route because route distance is short;
- toilet/nursing room exists because the place category suggests it.

Normalize to CityNexus evidence:

- ACCESSIBILITY_VERIFIED
- ACCESSIBILITY_UNVERIFIED
- ACCESSIBILITY_CONFLICT
- NEEDS_LIVE_EVIDENCE

Every normalized fact must carry provenance:
provider
source key/tag
captured timestamp
city/place identity
confidence type if applicable

Build:
- provider adapter/reference code in isolated tree;
- frozen fixtures for verified/unknown/conflict;
- unit tests;
- UI mapping;
- a low-conflict patch or reference implementation.

If route-level step-free evidence cannot be proved from the current provider,
say so explicitly and keep the route `NEEDS_LIVE_EVIDENCE`.
