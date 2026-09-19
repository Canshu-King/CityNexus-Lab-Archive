# V6 Gate Matrix

V6-01 Worker lifecycle is global but Autopilot enrollment is persisted per Journey.
V6-02 Starting Autopilot for Journey A does not silently enroll Journey B.
V6-03 Stopping Journey A does not disable another enrolled Journey.
V6-04 Live signal refresh composes weather and mobility providers rather than selecting exactly one.
V6-05 Provider observations carry independent state/provenance/TTL.
V6-06 Real Nominatim geocoding smoke passes when network is available.
V6-07 Real Overpass POI discovery smoke returns bounded provider-backed candidates when network is available.
V6-08 Selected real POIs materialize into CityNexus with stable provider/external IDs.
V6-09 Real Valhalla route smoke passes when endpoint is reachable; fallback remains honest.
V6-10 MapLibre uses a real basemap style and still renders backend route evidence.
V6-11 Literal Hermes model-backed tool loop passes when Hermes is available.
V6-12 Native DeepSeek fallback remains model-backed and functional.
V6-13 Journey Resilience Snapshot is deterministic for the same frozen facts.
V6-14 Resilience includes Commitment slack, weather exposure, mobility sensitivity and recovery optionality.
V6-15 Counterfactual simulation never mutates Domain Truth.
V6-16 Preemptive recovery can occur before a hard failure when risk threshold is crossed.
V6-17 Preemptive action still obeys Autonomy Envelope and protected Commitments.
V6-18 Real-city replacement discovery feeds CP-SAT V2.
V6-19 Control Tower shows real POIs, real basemap, real route provenance and resilience.
V6-20 Phoenix trace captures Agent/solver/policy spans if enabled.
V6-21 Promptfoo adversarial suite covers hallucinated POIs, tool misuse, budget abuse and prompt injection if enabled.
V6-22 Live-mode failure gracefully falls back to captured/replay mode.
V6-23 Full offline deterministic Golden remains green.
V6-24 final ZIP contains no credentials, runtime DB, caches, node_modules, dist or nested archives.
