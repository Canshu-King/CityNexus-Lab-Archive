"""Fix the anchor branch to use per-leg gap estimation correctly."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/planning/anchor_schedule.py")
s = P.read_text(encoding="utf-8")

old = '''        if item.anchor_role is not None:
            # Drop optional POIs that would arrive late for the anchor.
            while schedule and cursor is not None and (
                cursor + timedelta(minutes=_estimate_gap_minutes(travel_minutes, previous_place, item.place_id))
                > item.start_at
            ):
                schedule.pop()
                cursor = schedule[-1].end_at if schedule else None
                previous_place = schedule[-1].place_id if schedule else None
            if cursor is not None:
                gap = _estimate_gap_minutes(travel_minutes, previous_place, item.place_id)
                if cursor + timedelta(minutes=gap) > item.start_at:
                    return None
            schedule.append(item)
            cursor = item.end_at
            previous_place = item.place_id
            continue'''

new = '''        if item.anchor_role is not None:
            # Drop optional POIs that could not arrive before the anchor starts.
            while schedule and cursor is not None:
                needed = _estimate_gap_minutes(
                    travel_minutes, previous_place, item.place_id
                )
                if cursor + timedelta(minutes=needed) <= item.start_at:
                    break
                schedule.pop()
                cursor = schedule[-1].end_at if schedule else None
                previous_place = schedule[-1].place_id if schedule else None
            if cursor is not None:
                needed = _estimate_gap_minutes(travel_minutes, previous_place, item.place_id)
                if cursor + timedelta(minutes=needed) > item.start_at:
                    return None
            schedule.append(item)
            cursor = item.end_at
            previous_place = item.place_id
            continue'''
assert old in s, "anchor branch not found"
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
