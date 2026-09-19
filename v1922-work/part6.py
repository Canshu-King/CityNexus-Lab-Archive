

def anchor_window(
    role: str,
    scheduled_at: datetime,
    duration_min: int = 20,
) -> tuple[datetime, datetime]:
    """The real-world time span a C4 anchor occupies.

    A DEPARTURE anchor constrains the END of its activity, so the span starts
    ``duration_min`` before the booked departure.  Everything else is anchored
    on its START.
    """

    delta = timedelta(minutes=max(1, int(duration_min)))
    if normalise_role(role) == DEPARTURE_ROLE:
        return scheduled_at - delta, scheduled_at
    return scheduled_at, scheduled_at + delta
