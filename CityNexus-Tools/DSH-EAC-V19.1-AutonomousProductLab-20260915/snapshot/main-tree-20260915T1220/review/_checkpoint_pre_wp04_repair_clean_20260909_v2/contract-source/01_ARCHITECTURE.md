# 01 - Technical Architecture

## 1. Architecture style

Use a **modular monolith**. The goal is to preserve clear domain boundaries without paying the operational cost of microservices in a coursework prototype.

```text
React/Vite web client
        |
        | HTTPS/JSON in production; HTTP localhost in demo
        v
FastAPI /api/v1
        |
        +-- Journey Management
        +-- City Discovery
        +-- Booking & Commerce
        +-- Journey Intelligence
        |
        +-- Provider Port Interfaces
        |      +-- Mock City Data
        |      +-- Mock Mobility
        |      +-- Mock Booking
        |      +-- Mock Payment/Auth
        |      +-- Mock Context Events
        |      +-- Optional AI Provider
        |
        v
SQLAlchemy Unit of Work / Repositories
        |
        v
SQLite (MVP)
```

## 2. Frontend

- React 19 compatible code style, TypeScript, Vite.
- React Router for pages.
- TanStack Query for server state.
- Plain component state for local forms; add Zustand only if a concrete need appears.
- Mobile-first responsive layout so the UI can later inform the Mobile Applications coursework prototype.
- No business-feasibility rules in the browser. The frontend may validate form syntax, but the backend is authoritative.

### Primary screens

1. Dashboard / journey list
2. Create Journey wizard
3. Candidate Plans comparison
4. Active Journey / JourneyTwin
5. Booking and payment simulation
6. Disruption event panel (demo-only injection control)
7. Replan Proposal comparison and explanation
8. Journey History
9. AI Copilot side panel

## 3. Backend modules

### Journey Management

Owns Journey, PlanVersion, Activity, Constraint, Preference links and JourneyTwin orchestration.

### City Discovery

Owns Place/CityService catalog access through provider ports. Mock catalog is deterministic for tests.

### Booking & Commerce

Owns Booking, Order, Transaction and Commitment creation/update. For MVP, providers are simulations with deterministic success/failure modes.

### Journey Intelligence

Owns Event interpretation, candidate generation, deterministic feasibility, scoring, ReplanProposal and AI explanation adapter.

## 4. Dependency rule

- API routers call application services.
- Application services use repositories and provider interfaces.
- Domain/replanning logic must not import FastAPI, SQLAlchemy session globals or frontend concerns.
- Provider adapters may depend on HTTP clients later; the core domain must not.

## 5. Provider ports

Define interfaces first:

```text
CityDataProvider.search_places(...)
CityDataProvider.get_place(...)
MobilityProvider.estimate(origin, destination, departure_time)
BookingProvider.create_booking(...)
BookingProvider.cancel_booking(...)
PaymentProvider.authorize(...)
PaymentProvider.capture(...)
ContextEventProvider.list_events(...)
AIProvider.rank_or_explain(...)
```

Mock adapters implement the same interfaces. Real adapters can replace them later without changing domain services.

## 6. Deterministic/AI boundary

AI may:

- interpret free-text preferences;
- rank already feasible candidates;
- generate user-friendly explanations;
- answer natural-language questions using verified journey context.

AI may not:

- override hard constraints;
- invent provider availability as fact;
- activate a plan;
- move or cancel a locked commitment without deterministic policy approval;
- make core planning unavailable when AI fails.

## 7. Transaction boundaries

Use one database transaction for each user-visible state change, especially:

- plan selection;
- booking/payment state change;
- journey start/advance;
- event acknowledgement;
- ReplanProposal acceptance and active-plan swap.

Replan acceptance must atomically:

1. verify proposal still applies to the current active plan;
2. mark previous plan superseded;
3. mark proposed plan active;
4. update `journey.active_plan_version_id`;
5. update proposal status;
6. refresh JourneyTwin;
7. write an audit record.

## 8. Idempotency

Require an `Idempotency-Key` header for simulated transaction creation and replan acceptance. Store keys in transaction/audit records to prevent duplicate payment or double plan activation.

## 9. Time, money and coordinates

- Persist timestamps in UTC; keep journey display timezone separately.
- Money uses integer minor units plus ISO-like currency code; never floating-point money.
- Latitude/longitude may use decimal REAL values for MVP.

## 10. Error envelope

All API errors use:

```json
{
  "error": {
    "code": "HARD_CONSTRAINT_VIOLATION",
    "message": "Candidate violates a non-negotiable constraint.",
    "details": {},
    "trace_id": "..."
  }
}
```

## 11. Observability for coursework

Every important action writes `audit_log` rows. This provides material for testing, debugging, screenshots and Part 2 evidence without introducing a full logging platform.
