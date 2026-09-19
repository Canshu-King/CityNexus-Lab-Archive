

# --------------------------------------------------------------------------
# 6) structural edge anchors still do not constrain themselves
# --------------------------------------------------------------------------
def test_v1925_structural_edges_do_not_reject_themselves() -> None:
    """F05 of V19.2.4 must keep working: a booked 08:00 departure on a 09:00
    draft Journey is an authoritative edge, not an out-of-window violation."""

    from datetime import timedelta

    departure_at = _at(8)
    snapshot = MobilitySnapshot.from_minutes(
        source_provider_key="v1925-edge-test",
        minutes={(DEPARTURE, BOOKING): 0, (BOOKING, DEPARTURE): 0},
        captured_at="2026-09-15T00:00:00+00:00",
    )
    context = FeasibilityContext(
        journey_id="J",
        city_code="CITY-DELTA",
        journey_start=_at(9),
        journey_end=_at(19),
        budget_amount_minor=1_000_000,
        budget_currency="EUR",
        constraints=tuple([_lock(DEPARTURE, departure_at, "END", "DEPARTURE")]),
        places={pid: _place(pid) for pid in (DEPARTURE, BOOKING)},
        services={},
        mobility_provider=snapshot,
        plan_currency="EUR",
    )
    result = evaluate_feasibility(
        context,
        [_act(DEPARTURE, departure_at - timedelta(minutes=20), departure_at)],
    )
    assert not any(
        failure.startswith("C4_ANCHOR_OUTSIDE_JOURNEY") for failure in result.failures
    ), result.failures
    assert result.passed is True, result.failures


# --------------------------------------------------------------------------
# 7) an interior lock exactly on the boundary is inside, not outside
# --------------------------------------------------------------------------
def test_v1925_interior_lock_on_the_boundary_is_inside() -> None:
    """Boundary semantics are inclusive: an interior anchor starting exactly
    when ARRIVAL completes, and ending exactly when DEPARTURE begins, is valid."""

    from datetime import timedelta

    arrival_start = _at(10)
    arrival_end = arrival_start + timedelta(minutes=20)
    departure_start = _at(17)
    snapshot = MobilitySnapshot.from_minutes(
        source_provider_key="v1925-boundary-test",
        minutes={(a, b): 0 for a in (ARRIVAL, MID, DEPARTURE) for b in (ARRIVAL, MID, DEPARTURE) if a != b},
        captured_at="2026-09-15T00:00:00+00:00",
    )
    context = FeasibilityContext(
        journey_id="J",
        city_code="CITY-DELTA",
        journey_start=_at(9),
        journey_end=_at(19),
        budget_amount_minor=1_000_000,
        budget_currency="EUR",
        constraints=tuple(
            [
                _lock(ARRIVAL, arrival_start, "START", "ARRIVAL"),
                _lock(MID, arrival_end, "START", "MID_TRIP"),
                _lock(DEPARTURE, departure_start, "END", "DEPARTURE"),
            ]
        ),
        places={pid: _place(pid) for pid in (ARRIVAL, MID, DEPARTURE)},
        services={},
        mobility_provider=snapshot,
        plan_currency="EUR",
    )
    result = evaluate_feasibility(
        context,
        [
            _act(ARRIVAL, arrival_start, arrival_end),
            # starts exactly at the ARRIVAL boundary
            _act(MID, arrival_end, departure_start),
            _act(DEPARTURE, departure_start - timedelta(minutes=20), departure_start),
        ],
    )
    assert result.passed is True, result.failures
