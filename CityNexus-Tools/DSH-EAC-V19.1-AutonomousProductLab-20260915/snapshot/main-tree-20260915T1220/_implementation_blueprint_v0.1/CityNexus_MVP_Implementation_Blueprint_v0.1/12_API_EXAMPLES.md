# 12 - Canonical API Examples

These examples are illustrative payloads consistent with `api/openapi.yaml`.

## Create journey

```http
POST /api/v1/journeys
Content-Type: application/json
```

```json
{
  "traveler_id": "11111111-1111-4111-8111-111111111111",
  "title": "One Day in Nexus City",
  "city_code": "CNX-DEMO",
  "timezone": "Asia/Shanghai",
  "start_at": "2026-10-10T09:00:00+08:00",
  "end_at": "2026-10-10T19:00:00+08:00",
  "budget": {"amount_minor": 50000, "currency": "CNY"},
  "planning_mode": "balanced"
}
```

## Generate plans

```http
POST /api/v1/journeys/{journey_id}/plans/generate
```

```json
{"planning_mode": "balanced", "candidate_count": 3}
```

Expected: 201 with only hard-feasible PlanVersions.

## Inject canonical closure

```http
POST /api/v1/journeys/{journey_id}/events
```

```json
{
  "provider_key": "mock-context",
  "event_type": "CLOSURE",
  "severity": "MAJOR",
  "affected_activity_id": "<tech-art-activity-id>",
  "occurred_at": "2026-10-10T13:10:00+08:00",
  "payload": {
    "reason": "Unexpected facility closure",
    "unavailable_until": "2026-10-10T18:00:00+08:00"
  }
}
```

## Generate replan

```http
POST /api/v1/journeys/{journey_id}/replans
```

```json
{"trigger_event_id": "33333333-3333-4333-8333-333333333333", "candidate_count": 3}
```

The response must expose hard-gate flags and all eight score components.

## Accept replan

```http
POST /api/v1/replans/{proposal_id}/accept
Idempotency-Key: demo-replan-accept-001
```

The response contains Journey + accepted ReplanProposal + refreshed JourneyTwin.
