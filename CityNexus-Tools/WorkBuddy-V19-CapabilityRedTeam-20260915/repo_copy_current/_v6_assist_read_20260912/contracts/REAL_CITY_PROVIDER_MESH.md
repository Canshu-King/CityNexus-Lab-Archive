# Real City Provider Mesh V6

Replace the single `guardian_signal_provider` switch with a composable Provider Mesh.

Recommended contracts:

WeatherSignalProvider
MobilitySignalProvider
GeocodingProvider
POIDiscoveryProvider
MapStyleProvider

Initial real providers:

Weather:
- existing Open-Meteo runtime

Routing / mobility:
- existing Valhalla provider
- support a configured real Valhalla endpoint
- public demo endpoint may be used only for development/fair-use smoke, with identifying client header and rate limiting
- freeze captured route/travel evidence before planning

Geocoding:
- Nominatim
- rate-limit and cache public-instance calls
- identifying User-Agent
- persist external OSM identity/provenance

POI discovery:
- Overpass API
- query categories within a bounded radius / polygon
- materialize only selected candidates into CityNexus Place rows
- never dump an unbounded city dataset into the DB

Map:
- OpenFreeMap vector style for development/demo
- retain provider abstraction for future self-hosting

Each provider must have:
READY / DEGRADED / OFFLINE
captured_at
provider_key
source provenance
TTL/cache policy
fallback behavior

Provider calls happen during explicit capture/refresh, never inside authoritative GET projections or deterministic feasibility.
