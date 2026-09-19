"""Apply the anchor-aware generation changes to app/services.py."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/services.py")
s = P.read_text(encoding="utf-8")


def sub(old, new, label):
    global s
    assert old in s, f"anchor not found: {label}"
    assert s.count(old) == 1, f"ambiguous anchor: {label}"
    s = s.replace(old, new, 1)
