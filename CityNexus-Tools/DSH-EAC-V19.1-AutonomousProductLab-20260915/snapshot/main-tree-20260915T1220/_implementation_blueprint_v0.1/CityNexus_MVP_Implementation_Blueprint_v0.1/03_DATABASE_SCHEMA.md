# 03 - Database Schema

This schema is an executable MVP persistence design based on the source-backed domain concepts. It is not a claim that the frozen v0.4.2 YAML used these exact columns or lifecycle enum names.

## Aggregate ownership

- Traveler owns Preference records and creates Journeys.
- Journey is the principal aggregate root for planning/execution.
- PlanVersion belongs to Journey; Activities belong to a PlanVersion.
- JourneyTwin is a 1:1 read projection for the current state.
- Constraints, Events, Commitments, ReplanProposals and Recommendations belong to Journey.
- Booking/Order/Transaction provide commerce records and may create/update Commitments.
- Place/CityService are provider-catalog records shared across journeys.

## Domain tables

1. `travelers`
2. `preferences`
3. `journeys`
4. `journey_twins`
5. `constraints`
6. `plan_versions`
7. `activities`
8. `places`
9. `city_services`
10. `commitments`
11. `events`
12. `replan_proposals`
13. `bookings`
14. `orders`
15. `transactions`
16. `recommendations`

## Technical tables

- `provider_calls`: deterministic audit/replay of external/mock provider calls.
- `audit_logs`: user/system state-change audit trail.
- `idempotency_keys`: duplicate-write protection for high-risk operations.

## Important constraints

- `planning_mode` is restricted to `balanced`, `budget`, `explore`, `strict_schedule`.
- Money is stored as integer minor units.
- A Journey may have only one `active_plan_version_id` reference at a time.
- `plan_versions.version_no` is unique per journey.
- Activity `sequence_no` is unique per plan version.
- A ReplanProposal explicitly points from `base_plan_version_id` to `proposed_plan_version_id`.
- Proposal acceptance must verify that the journey is still on the proposal's base plan.
- Locked commitments are never silently deleted by replanning.
