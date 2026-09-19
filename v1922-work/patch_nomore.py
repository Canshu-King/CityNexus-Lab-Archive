"""'no more than' is a bound, not a denial."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/capabilities.py")
s = P.read_text(encoding="utf-8")

old = '''        negated = any(marker in clause for marker in _NEGATED_MARKERS) or bool(
            re.search(r"\b(?:don't|do not|doesn't|does not|not|never|no)\b", clause)
        )'''
new = '''        # "no more than 100 m" / "walk no more than" is a bound, not a denial.
        bounded_phrase = bool(
            re.search(r"\bno (?:more|longer|further) than\b|\bnot more than\b", clause)
        )
        negated = any(marker in clause for marker in _NEGATED_MARKERS) or (
            bool(re.search(r"\b(?:don't|do not|doesn't|does not|not|never|no)\b", clause))
            and not bounded_phrase
        )'''
assert old in s, "negation test not found"
s = s.replace(old, new, 1)

# Add the English phrase to the walking trigger list.
old2 = '''            "cannot walk more than",
            "walk no more than",'''
new2 = '''            "cannot walk more than",
            "walk no more than",
            "no more than",'''
assert old2 in s, "walking trigger not found"
s = s.replace(old2, new2, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
