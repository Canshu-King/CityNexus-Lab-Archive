

# --------------------------------------------------------------------------
# R01/R02 — an open Event never projects RESOLVED, and flags agree
# --------------------------------------------------------------------------
def _active_with_hard_recovery(ref: str = "V1924-R") -> str:
    journey_id = H.DEMO_JOURNEY_ID
    H.reset_demo()
    assert H.generate_plans()[0] == 201
    plans = H.list_plans()
    assert H.select_plan(journey_id, plans[0]["id"]).status_code == 200
    assert H.start_journey(journey_id).status_code == 200
    confirmed = H.confirm_journey_capabilities(
        [H.capability("STEP_FREE_REQUIRED", "HARD")]
    )
    assert confirmed.status_code == 200, confirmed.text
    return journey_id


def test_v1924_open_event_never_projects_resolved() -> None:
    from app.db.models import Event, Journey
    from app.planning.hard_recovery import recovery_flags, recovery_state
    from sqlalchemy import select

    journey_id = _active_with_hard_recovery("V1924-R01")
    with H._session() as session:
        journey = session.get(Journey, journey_id)
        # A caller may pass is_feasible=True; it must not resolve durable truth.
        projected = recovery_state(session, journey, is_feasible=True)
        flags = recovery_flags(session, journey)
        event = session.scalar(
            select(Event).where(
                Event.journey_id == journey_id,
                Event.status.in_(("DETECTED", "ACKNOWLEDGED")),
            )
        )
        assert event is not None and event.status == "DETECTED"
        assert projected["state"] != "RESOLVED", projected
        assert flags["recovery_required"] is True
        # projection and durable truth agree
        assert projected["state"] == flags["recovery_state"]


# --------------------------------------------------------------------------
# R03 — GET /experience is a projection, not a durable transition
# --------------------------------------------------------------------------
def test_v1924_experience_get_does_not_resolve_recovery() -> None:
    from app.db.models import Event
    from sqlalchemy import select

    journey_id = _active_with_hard_recovery("V1924-R03")
    for _ in range(3):
        response = H.client().get(f"/api/v1/journeys/{journey_id}/experience")
        assert response.status_code == 200
        body = response.json()
        assert body["recovery"] is not None
        assert body["recovery"]["state"] != "RESOLVED"
        assert body["experience_flags"]["recovery_required"] is True
    with H._session() as session:
        event = session.scalar(
            select(Event).where(
                Event.journey_id == journey_id,
                Event.status.in_(("DETECTED", "ACKNOWLEDGED")),
            )
        )
        assert event is not None, "a read must not durably resolve the Event"
        assert event.status == "DETECTED"


# --------------------------------------------------------------------------
# R04 — only replan-validated candidates are advertised
# --------------------------------------------------------------------------
def test_v1924_unvalidated_candidates_are_not_advertised() -> None:
    journey_id = _active_with_hard_recovery("V1924-R04")
    plans = H.list_plans(journey_id)
    unvalidated = [plan for plan in plans if plan["status"] == "CANDIDATE"]
    assert unvalidated, "the fixture should contain arbitrary candidate rows"

    recovery = H.experience(journey_id)["recovery"]
    assert recovery["replan_attempted"] is False
    assert recovery["candidate_plan_count"] == 0, (
        "an arbitrary CANDIDATE row is not proof of feasibility"
    )
    assert recovery["candidate_plan_ids"] == []


def test_v1924_replan_validated_candidates_are_advertised() -> None:
    journey_id = _active_with_hard_recovery("V1924-R04B")
    # A real replan attempt is what makes candidates advertisable.
    assert H.generate_plans()[0] == 422, "no feasible alternative for this HARD need"
    recovery = H.experience(journey_id)["recovery"]
    assert recovery["replan_attempted"] is True
    assert recovery["no_alternative"] is True
    assert recovery["state"] == "RECOVERY_REQUIRED_NO_ALTERNATIVE"
    assert recovery["candidate_plan_count"] == 0


# --------------------------------------------------------------------------
# R02b — a genuinely feasible replacement still resolves transactionally
# --------------------------------------------------------------------------
def test_v1924_feasible_replacement_still_resolves_recovery() -> None:
    journey_id = _active_with_hard_recovery("V1924-R02B")
    H.put_journey_capabilities([])
    assert H.confirm_journey_capabilities([]).status_code == 200
    assert H.generate_plans()[0] == 201
    original = H.journey(journey_id)["active_plan_version_id"]
    replacement = next(
        plan for plan in H.list_plans(journey_id) if plan["id"] != original
    )
    assert H.select_plan(journey_id, replacement["id"]).status_code == 200
    experience = H.experience(journey_id)
    assert experience["recovery"] is None
    assert experience["experience_flags"]["recovery_required"] is False
    assert experience["experience_flags"]["needs_review"] is False
    # reload must not resurrect it
    assert H.experience(journey_id)["recovery"] is None
