

def open_recovery_event(
    session: Session,
    journey: Journey,
    *,
    capability_code: str,
    capability_params: dict[str, Any] | None = None,
    failures: list[str] | None = None,
) -> Event:
    """Create (or refresh) the durable recovery Event for this Journey.

    Refreshing keeps the event open but clears any prior acknowledgement: the
    underlying situation has changed, so a previous acknowledgement no longer
    describes what the traveller has seen.
    """

    existing = active_recovery_event(session, journey)
    payload = {
        "capability_code": capability_code,
        "capability_params": dict(capability_params or {}),
        "active_plan_version_id": journey.active_plan_version_id,
        "feasibility_failures": list(failures or []),
        "requires_user_decision": True,
        "silent_plan_mutation": False,
        # Reset any previous replan outcome: this is a fresh invalidation.
        "replan_attempted": False,
        "no_alternative": False,
        "acknowledged_at": None,
    }
    now = _now()
    if existing is not None:
        existing.payload_json = _json(payload)
        existing.detected_at = now
        existing.status = "DETECTED"
        existing.resolved_at = None
        return existing
    event = Event(
        id=str(uuid4()),
        journey_id=journey.id,
        provider_key=PROVIDER_KEY,
        provenance="USER_REPORTED",
        event_type=EVENT_TYPE,
        severity="MAJOR",
        status="DETECTED",
        affected_activity_id=None,
        occurred_at=now,
        detected_at=now,
        resolved_at=None,
        payload_json=_json(payload),
        created_at=now,
    )
    session.add(event)
    session.flush()
    return event


def acknowledge_recovery(session: Session, journey: Journey) -> Event | None:
    """Record that the traveller saw the warning.  Does NOT resolve it."""

    event = active_recovery_event(session, journey)
    if event is None:
        return None
    payload = _load(event.payload_json, {})
    payload["acknowledged_at"] = _now()
    event.payload_json = _json(payload)
    if event.status == "DETECTED":
        event.status = "ACKNOWLEDGED"
    return event


def record_replan_outcome(
    session: Session,
    journey: Journey,
    *,
    feasible_candidate_ids: list[str],
    failures: list[str] | None = None,
) -> Event | None:
    """Persist the outcome of an actual recovery/replan attempt.

    Zero feasibility-checked candidates is what makes the no-alternative state
    real.  A missing boolean never does.
    """

    event = active_recovery_event(session, journey)
    if event is None:
        return None
    payload = _load(event.payload_json, {})
    payload["replan_attempted"] = True
    payload["attempted_at"] = _now()
    payload["feasible_candidate_ids"] = list(feasible_candidate_ids)
    payload["no_alternative"] = not feasible_candidate_ids
    if failures:
        payload["replan_failures"] = list(failures)
    event.payload_json = _json(payload)
    return event


def resolve_recovery_events(session: Session, journey: Journey) -> int:
    """Mark every open recovery Event resolved (a feasible plan is active)."""

    rows = _open_events(session, journey)
    now = _now()
    for row in rows:
        row.status = "RESOLVED"
        row.resolved_at = now
        payload = _load(row.payload_json, {})
        payload["resolved_at"] = now
        row.payload_json = _json(payload)
    return len(rows)
