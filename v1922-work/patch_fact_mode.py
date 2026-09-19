"""Carry travel mode on frozen facts so walking evidence is mode-aware."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/replanning/provider_snapshots.py")
s = P.read_text(encoding="utf-8")

old = '''    distance_m: int | None = None
    walking_distance_m: int | None = None
    walking_min: int | None = None

    def __post_init__(self) -> None:
        if self.minutes < 0:
            raise ValueError("travel minutes must be non-negative")'''
new = '''    distance_m: int | None = None
    walking_distance_m: int | None = None
    walking_min: int | None = None
    # The travel mode is what makes ``distance_m`` interpretable.  Without it a
    # total route distance could be silently read as walking distance.
    mode: str | None = None

    def __post_init__(self) -> None:
        if self.minutes < 0:
            raise ValueError("travel minutes must be non-negative")'''
assert old in s, "TravelEstimateFact fields not found"
s = s.replace(old, new, 1)

old2 = '''                walking_min=(
                    int(item["walking_min"]) if item.get("walking_min") is not None else None
                ),
            )'''
new2 = '''                walking_min=(
                    int(item["walking_min"]) if item.get("walking_min") is not None else None
                ),
                mode=(
                    str(item["mode"]).upper()
                    if item.get("mode") is not None
                    else None
                ),
            )'''
assert old2 in s, "from_evidence block not found"
s = s.replace(old2, new2, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("mode field added")
