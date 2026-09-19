from pathlib import Path
P = Path("D:/moodle/CityNexus/backend/app/planning/anchor_schedule.py")
s = P.read_text(encoding="utf-8")
old = '''    start = datetime.fromisoformat(str(journey.start_at))
    end = datetime.fromisoformat(str(journey.end_at))
    for anchor in anchors:
        duration = timedelta(
            minutes=(
                ANCHOR_DURATION_MIN
                if anchor.role != MID_TRIP_ROLE
                else max(ANCHOR_DURATION_MIN, _place_duration(anchor.place))
            )
        )
        if anchor.time_boundary == "END":
            candidate_start = anchor.scheduled_at - duration
            candidate_end = anchor.scheduled_at
        else:
            candidate_start = anchor.scheduled_at
            candidate_end = anchor.scheduled_at + duration
        if candidate_start < start:
            start = candidate_start
        if candidate_end > end:
            end = candidate_end
    return start.isoformat(), end.isoformat()'''
new = '''    start = datetime.fromisoformat(str(journey.start_at))
    end = datetime.fromisoformat(str(journey.end_at))
    for anchor in anchors:
        duration = (
            ANCHOR_DURATION_MIN
            if anchor.role != MID_TRIP_ROLE
            else max(ANCHOR_DURATION_MIN, _place_duration(anchor.place))
        )
        candidate_start, candidate_end = anchor_window(
            anchor.role, anchor.scheduled_at, duration
        )
        if candidate_start < start:
            start = candidate_start
        if candidate_end > end:
            end = candidate_end
    return start.isoformat(), end.isoformat()'''
assert old in s
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
