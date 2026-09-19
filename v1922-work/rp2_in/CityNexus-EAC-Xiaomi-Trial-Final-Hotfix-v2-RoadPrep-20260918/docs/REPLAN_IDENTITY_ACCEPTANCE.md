# Replan identity acceptance

The new final trace must contain exact identities.

## Before

- journey_id
- base_plan_id
- affected_activity_id
- affected_place_id
- affected semantic key
- title
- protected/locked state

## Proposal

- proposal_id
- proposed_plan_id
- diff.removed[]
- diff.added[]
- diff.moved[]
- exact semantic/place/activity identities
- recovery family
- target resolution evidence

## After accept

- active_plan_id
- activity IDs
- Place IDs
- semantic keys

Assertions:

1. affected mutable entity is actually removed/replaced according to contract.
2. same closed Place cannot reappear through a new Activity ID.
3. booking-derived protected commitments survive.
4. imported booking with activity_id=None does not protect unrelated mutable POI.
5. UI summary matches exact diff.
6. if target resolution is uncertain, system asks/blocks instead of guessing.
