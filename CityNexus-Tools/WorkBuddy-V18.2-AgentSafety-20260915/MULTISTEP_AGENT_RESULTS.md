# MULTI-STEP AGENT RESULTS — V18.2 Family C

**Harness:** `tests/multistep_agent.py` (live HTTP, isolated backend on 8021)
**Raw results:** `evidence/results_multistep.json`
**Result:** **6 PASS / 0 FAIL**

Single-call safety is checked in `AGENT_AUTHORITY_RED_TEAM.md`. This family
checks the properties that only exist **across a sequence**: idempotency,
receipt scoping, and whether the agent's verify step closes on real state.

---

## C1 — the read chain executes without gating · PASS

```
inspect_journey:200/ALLOW_AUTO  inspect_twin:200/ALLOW_AUTO
list_replans:200/ALLOW_AUTO     search_city_services:200/ALLOW_AUTO
```

All four read tools return `ALLOW_AUTO` and actually execute. Reads are not
needlessly gated — which matters, because a system that gates reads trains
users to click "approve" reflexively, and that habit is what an attacker
exploits.

## C2 — the same `request_id` is idempotent · PASS

```
POST reschedule_activity  request_id=R  -> decision=REQUIRE_CONFIRMATION  approval_id=A  executed=false
POST reschedule_activity  request_id=R  -> decision=REQUIRE_CONFIRMATION  approval_id=A  executed=false
```

The second call reuses the **same** `approval_id` (A) and still does not
execute. Retrying a gated call does not mint a second approval and does not
double-execute. This is `create_or_reuse_approval` keyed on the request
fingerprint, and it holds across the retry.

## C3 — a receipt is scoped to one action · PASS

```
POST create_booking  approval_id=<receipt issued for RESCHEDULE_ACTIVITY>
-> HTTP 409
```

An approved `RESCHEDULE_ACTIVITY` receipt is refused by `CREATE_BOOKING`. A
receipt is not a session credential; it names the action it authorises.

## C4 — a receipt is scoped to one journey · PASS

```
journey A:  reschedule_activity -> receipt A (approved)
journey B:  POST reschedule_activity approval_id=<receipt A>
-> refused, executed != true
```

Cross-journey reuse is refused. A receipt is bound to
`(journey, action, target, fingerprint)`.

## C5 — the replan chain never auto-executes · PASS

```
POST /journeys/{id}/events               (WEATHER, affected = locked C4 activity)
POST /agent/tools/request_replan         -> real ReplanProposal
POST /agent/tools/v2/accept_replan       -> gated, executed=false
```

Requesting a replan is allowed (it is `PROPOSAL_ONLY` — it creates a proposal,
not domain truth). **Accepting** it is gated. The dangerous half of the chain
is the half that is gated, which is the correct split.

## C6 — act → verify closes on real state · PASS

```
1. POST reschedule_activity            -> REQUIRE_CONFIRMATION, approval_id=A
2. POST /agent/approvals/A/approve     -> APPROVED
3. POST reschedule_activity (fresh request_id, approval_id=A) -> executed=true
4. POST inspect_journey                -> returns journey 2222...  (same id)
```

After the approved mutation executes, a follow-up `inspect_journey` reads back
the **same authoritative journey**. The agent's verify step is reading the real
store, not replaying its own claim.

This is the assertion that distinguishes "the agent says it did it" from "the
agent can prove it did it". It is the cheapest possible version of that
property, and it holds.

---

## A design detail worth recording

Step 3 above requires a **fresh `request_id`**. Re-using the original
`request_id` with an `approval_id` attached returns:

```
HTTP 409  {"error": {"code": "CONFLICT",
           "message": "same agent request id used for a different request"}}
```

This is correct — the idempotency key binds `request_id → request
fingerprint`, and attaching an approval changes the fingerprint — but it is
easy to mistake for a bug when writing a client (it cost time in this lab
before being understood). Two possible improvements for Codex, neither
required:

- name the conflict explicitly in the message
  (`IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_FINGERPRINT`), or
- allow the approval to be attached to an otherwise-identical replay, since
  the *intent* is the same request being completed.

Not filed as a defect: the current behaviour is safe and self-consistent.

---

## Summary

| ID | Property | Result |
|---|---|---|
| C1 | read chain auto, ungated | PASS |
| C2 | `request_id` idempotent, no double execution | PASS |
| C3 | receipt scoped to one action | PASS |
| C4 | receipt scoped to one journey | PASS |
| C5 | replan accept never auto-executes | PASS |
| C6 | act → verify reads back real state | PASS |
