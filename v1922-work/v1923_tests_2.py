

# --------------------------------------------------------------------------
# T05 — impossible anchor combination yields a precise conflict
# --------------------------------------------------------------------------
def test_v1923_arrival_after_departure_is_a_precise_conflict() -> None:
    H.reset_demo()
    _confirmed("ARRIVAL", arrival=f"{DAY}T18:00:00{TZ}", departure=None, node=None, ref="T05-A")
    _confirmed("DEPARTURE", arrival=None, departure=f"{DAY}T10:00:00{TZ}", node=None, ref="T05-D")
    status, body = H.generate_plans()
    assert status == 422, f"an impossible anchor set must not fabricate a plan: {status}"
    message = str(body)
    assert "C4_ANCHOR_ARRIVAL_AFTER_DEPARTURE" in message, message
    assert not H.list_plans(), "no plan may be persisted for an impossible anchor set"


# --------------------------------------------------------------------------
# R01 — acknowledgement cannot hide unsafe truth
# --------------------------------------------------------------------------
def _active_journey_with_hard_recovery(ref: str = "R01") -> tuple[str, dict]:
    H.reset_demo()
    journey_id = H.DEMO_JOURNEY_ID
    status, _ = H.generate_plans()
    assert status == 201
    plans = H.list_plans()
    assert H.select_plan(journey_id, plans[0]["id"]).status_code == 200
    assert H.start_journey(journey_id).status_code == 200
    confirmed = H.confirm_journey_capabilities(
        [H.capability("STEP_FREE_REQUIRED", "HARD")]
    )
    assert confirmed.status_code == 200, confirmed.text
    return journey_id, confirmed.json()


def test_v1923_acknowledge_never_resolves_or_hides_recovery() -> None:
    journey_id, confirmed = _active_journey_with_hard_recovery("R01")
    assert (confirmed.get("recovery") or {}).get("state") == "RECOVERY_REQUIRED"

    ack = H.client().post(f"/api/v1/journeys/{journey_id}/recovery/acknowledge")
    assert ack.status_code == 200, ack.text
    body = ack.json()
    assert body["acknowledged"] is True
    assert body["resolved"] is False
    assert (body.get("recovery") or {}).get("state") == "RECOVERY_REQUIRED"
    assert (body.get("recovery") or {}).get("event_status") == "ACKNOWLEDGED"

    exp = H.experience(journey_id)
    flags = exp["experience_flags"]
    assert flags["needs_review"] is True, "an acknowledged HARD need is still unsafe"
    assert flags["recovery_required"] is True
    assert flags["acknowledged"] is True
    assert exp["recovery"]["state"] == "RECOVERY_REQUIRED"
    # the journey is still ACTIVE on the unchanged plan
    assert H.journey(journey_id)["status"] == "ACTIVE"


def test_v1923_acknowledge_does_not_make_infeasible_plan_selectable() -> None:
    journey_id, _ = _active_journey_with_hard_recovery("R01B")
    before = H.plan_signatures(journey_id)
    H.client().post(f"/api/v1/journeys/{journey_id}/recovery/acknowledge")
    after = H.plan_signatures(journey_id)
    assert before == after, "acknowledgement must not rewrite the plan"
    # the active plan still fails the same truth policy used by select/start
    exp = H.experience(journey_id)
    assert exp["experience_flags"]["needs_review"] is True
    assert exp["experience_flags"]["recovery_required"] is True
    # a replacement still cannot be produced while the HARD need is unmet
    status, _ = H.generate_plans()
    assert status == 422, "an unmet HARD need must not yield a selectable replacement"
