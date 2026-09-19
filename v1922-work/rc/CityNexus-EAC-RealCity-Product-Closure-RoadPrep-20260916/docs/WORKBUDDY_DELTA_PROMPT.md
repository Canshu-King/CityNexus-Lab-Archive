# WORKBUDDY TARGETED DELTA — Snapshot H -> next closure

Read-only red-team.

Freeze:
CityNexus-EAC-Overnight-Mobile-Product-Rescue-V2-20260916.zip
as Snapshot H.

Do not modify the main tree.

Do not rerun the giant historical corpus.

Validate only the next product-closure claims.

## 1. Same-journey continuity

Demand SAME_JOURNEY_TRACE.json.

Verify one Xiamen journey_id remains unchanged through:
create -> AI -> candidate plans -> select -> itinerary -> hotel -> live -> replan.

Fail if acceptance evidence switches to:
- sealed Tianjin demo
- /demo/reset
- another journey id

## 2. Real-Xiamen content

The accepted plan must contain Xiamen-specific places/provider facts.

Reject Old Town Gate / Riverside Museum / Nexus City as proof of Xiamen success.

## 3. Hotel flow

Entry is not enough.

Verify:
compare -> choose -> state changes -> Trips reflects stay.

## 4. Live replan

Route opening is not enough.

Verify:
disruption -> proposal -> affected/unchanged -> accept -> durable state.

## 5. Order import

Verify consumer input:
paste text/manual/upload when supported
-> preview
-> explicit confirm
-> one booking/commitment

Raw JSON may exist only as advanced tooling.

## 6. UI/product

Inspect 390x844, 430x932 and Xiaomi-like captures.

Reject:
- giant concatenated Trips page
- browser-default giant forms
- raw engineering vocabulary on core screens
- English-heavy Chinese acceptance flow
- Copilot covering core content
- wrong-city map

## 7. Final verdict

Only:

BLOCKED

or

SNAPSHOT_ACCEPTED_FOR_XIAOMI_PHYSICAL_TRIAL

No PASS for "entry visible" or "route opens".
