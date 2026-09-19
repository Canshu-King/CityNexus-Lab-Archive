# Replan identity gate

Do not validate disruption recovery by title alone.

For one fresh controlled flow, record:

## Before
- journey_id
- base_plan_id
- affected_activity_id
- affected_place_id
- affected semantic key
- title
- start/end
- locked/protected state

## Proposal
- proposal_id
- proposed_plan_id
- diff.removed exact semantic keys
- diff.added exact semantic keys
- moved exact semantic keys
- selected recovery target

## After accept
- active_plan_id
- all activity IDs
- all Place IDs
- all semantic keys

Assertions:

1. active plan changed.
2. removed key corresponds to the disrupted target or justified recovery target.
3. the exact disrupted activity identity does not survive unchanged.
4. added key has a valid grounded identity.
5. protected commitments survive.
6. no closed Place is silently reintroduced through a new Activity ID.
7. UI summary matches the exact diff.

If a different Place legitimately has the same title:
record both Place IDs and provider evidence.
