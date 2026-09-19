

def _city_center(session: Session, journey: Journey) -> tuple[float, float]:
    first = session.scalar(
        select(Place).where(Place.city_code == journey.city_code).limit(1)
    )
    if first is not None:
        return float(first.latitude), float(first.longitude)
    return 0.0, 0.0


def _structural_place(session: Session, journey: Journey, role: str) -> Place:
    """Materialise (or reuse) the structural anchor Place, matching V12's identity."""

    external_id = structural_external_id(journey.id, role)
    row = session.scalar(
        select(Place).where(
            Place.provider_key == ANCHOR_PROVIDER_KEY,
            Place.external_id == external_id,
        )
    )
    if row is not None:
        return row
    place_id = structural_place_id(journey.id, role)
    row = session.get(Place, place_id)
    if row is not None:
        return row
    latitude, longitude = _city_center(session, journey)
    offset = -0.015 if role == ARRIVAL_ROLE else 0.06
    offset_lon = -0.02 if role == ARRIVAL_ROLE else 0.08
    row = Place(
        id=place_id,
        provider_key=ANCHOR_PROVIDER_KEY,
        external_id=external_id,
        city_code=journey.city_code,
        name="Arrival" if role == ARRIVAL_ROLE else "Departure",
        category=role.lower(),
        latitude=latitude + offset,
        longitude=longitude + offset_lon,
        opening_hours_json=_json({"status": "NORMALIZED", "always_available": True}),
        tags_json=_json(["v12-authoritative", role.lower()]),
        metadata_json=_json({"anchor": role, "available": True, "cost_minor": 0}),
        updated_at=datetime.now().astimezone().isoformat(),
    )
    session.add(row)
    session.flush()
    return row


def resolve_plan_anchors(
    session: Session, journey: Journey
) -> tuple[list[ResolvedAnchor], list[str]]:
    """Resolve active C4 anchors; returns (resolved, unresolved_descriptions)."""

    resolved: list[ResolvedAnchor] = []
    unresolved: list[str] = []
    for commitment in active_c4_commitments(session, journey):
        policy = _load(commitment.policy_json, {})
        role = normalise_role(policy.get("anchor_role"))
        raw_key = str(policy.get("semantic_key") or "").strip()
        scheduled = str(policy.get("scheduled_start_at") or "").strip()
        if not scheduled:
            unresolved.append(f"{role}:NO_SCHEDULED_START")
            continue
        try:
            scheduled_at = datetime.fromisoformat(scheduled)
        except ValueError:
            unresolved.append(f"{role}:INVALID_SCHEDULED_START")
            continue
        if role in (ARRIVAL_ROLE, DEPARTURE_ROLE):
            place = _structural_place(session, journey, role)
            resolved.append(
                ResolvedAnchor(
                    role=role,
                    semantic_key=structural_place_id(journey.id, role),
                    place_id=place.id,
                    place=place,
                    scheduled_at=scheduled_at,
                    time_boundary="END" if role == DEPARTURE_ROLE else "START",
                )
            )
            continue
        place = session.get(Place, raw_key)
        if place is None:
            service = session.get(CityService, raw_key)
            if service is not None and service.place_id:
                place = session.get(Place, service.place_id)
        if place is None or place.city_code != journey.city_code:
            unresolved.append(f"{role}:{raw_key}")
            continue
        resolved.append(
            ResolvedAnchor(
                role=MID_TRIP_ROLE,
                semantic_key=raw_key,
                place_id=place.id,
                place=place,
                scheduled_at=scheduled_at,
                time_boundary="START",
            )
        )
    return resolved, unresolved
