"""Require an explicit walking-limit signal for 'cannot walk' phrasing."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/capabilities.py")
s = P.read_text(encoding="utf-8")

old = '''            "不能走远",
            "不能走",
            "走不了",
            "low walking",'''
new = '''            "不能走远",
            "low walking",'''
assert old in s
s = s.replace(old, new, 1)

old2 = '''            "cannot walk",
            "can't walk",
            "can not walk",
            "unable to walk",
            "walk far",
        )
    )'''
new2 = '''            "cannot walk",
            "can't walk",
            "can not walk",
            "unable to walk",
            "walk far",
        )
    )
    # "cannot walk" only implies a bounded walking limit when the clause is about
    # the traveller walking, not an accessibility/step-free statement that
    # merely mentions walking in passing.
    if walking and "走" not in value and "walk" in value:
        walking = any(
            token in value
            for token in (
                "walk far",
                "cannot walk",
                "can't walk",
                "can not walk",
                "unable to walk",
                "walk less",
                "less walking",
                "walking limit",
                "avoid walking",
                "avoid long walks",
            )
        )'''
assert old2 in s
s = s.replace(old2, new2, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
