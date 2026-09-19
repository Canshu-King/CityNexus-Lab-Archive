

# --------------------------------------------------------------------------
# R02 — a feasible replacement resolves the durable recovery
# --------------------------------------------------------------------------
def test_v1923_feasible_replacement_resolves_recovery() -> None:
    journey_id, _ = _active_journey_with_hard_recovery("R02")
    assert H.experience(journey_id)["recovery"]["state"] == "RECOVERY_REQUIRED"

    # Remove the HARD need, then generate and select a replacement.
    H.put_journey_capabilities([])
    assert H.confirm_journey_capabilities([]).status_code == 200
    status, _ = H.generate_plans()
    assert status == 201, status
    original = H.journey(journey_id)["active_plan_version_id"]
    replacement = next(p for p in H.list_plans(journey_id) if p["id"] != original)
    assert H.select_plan(journey_id, replacement["id"]).status_code == 200

    exp = H.experience(journey_id)
    assert exp["recovery"] is None, "a selected feasible plan must resolve recovery"
    flags = exp["experience_flags"]
    assert flags["recovery_required"] is False
    assert flags["needs_review"] is False
    assert flags["staleness"] is False
    # reload must not resurrect it
    again = H.experience(journey_id)
    assert again["recovery"] is None
    assert again["experience_flags"]["needs_review"] is False


def test_v1923_infeasible_plan_cannot_be_reselected_to_fake_resolution() -> None:
    journey_id, _ = _active_journey_with_hard_recovery("R02B")
    active = H.journey(journey_id)["active_plan_version_id"]
    rejected = H.select_plan(journey_id, active)
    assert rejected.status_code == 422, (
        "an infeasible plan must not become selectable merely by re-selecting it"
    )
    assert H.experience(journey_id)["recovery"]["state"] == "RECOVERY_REQUIRED"


# --------------------------------------------------------------------------
# R03 — real no-alternative state
# --------------------------------------------------------------------------
def test_v1923_zero_alternatives_persists_explicit_no_alternative() -> None:
    journey_id, _ = _active_journey_with_hard_recovery("R03")
    status, _ = H.generate_plans()
    assert status == 422, "no feasible alternative exists for this HARD need"
    exp = H.experience(journey_id)
    recovery = exp["recovery"]
    assert recovery is not None
    assert recovery["state"] == "RECOVERY_REQUIRED_NO_ALTERNATIVE", recovery
    assert recovery["replan_attempted"] is True, "must reflect an actual replan attempt"
    assert recovery["no_alternative"] is True
    assert exp["experience_flags"]["needs_review"] is True
    # survives a reload
    again = H.experience(journey_id)
    assert again["recovery"]["state"] == "RECOVERY_REQUIRED_NO_ALTERNATIVE"


# --------------------------------------------------------------------------
# R04 — C4 stays protected through recovery
# --------------------------------------------------------------------------
def test_v1923_c4_is_preserved_through_recovery() -> None:
    H.reset_demo()
    journey_id = H.DEMO_JOURNEY_ID
    _confirmed("ARRIVAL", arrival=f"{DAY}T12:30:00{TZ}", departure=None, node=None, ref="R04")
    assert H.generate_plans()[0] == 201
    plans = H.list_plans(journey_id)
    assert H.select_plan(journey_id, plans[0]["id"]).status_code == 200
    assert H.start_journey(journey_id).status_code == 200

    committed = [
        item for item in H.commitment_rows(journey_id) if item["level"] == "C4_Anchored"
    ]
    assert committed, "expected the reservation to create a C4 commitment"

    confirmed = H.confirm_journey_capabilities(
        [H.capability("STEP_FREE_REQUIRED", "HARD")]
    )
    assert confirmed.status_code == 200

    after = [
        item for item in H.commitment_rows(journey_id) if item["level"] == "C4_Anchored"
    ]
    assert len(after) == len(committed)
    assert all(item["status"] == "ACTIVE" for item in after), (
        "recovery must not drop or weaken an active C4 commitment"
    )
