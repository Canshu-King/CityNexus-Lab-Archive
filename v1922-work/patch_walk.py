"""Recognise 'cannot walk far' style statements as a walking limit."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/capabilities.py")
s = P.read_text(encoding="utf-8")

old = '''    walking = any(
        token in value
        for token in ("少走", "少步行", "不能走太多", "步行少", "走路少", "不能超过", "不超过", "最多走", "最多步行", "走超过", "走不了远路", "走不远", "走不动", "不能走远", "low walking", "walk less", "avoid long walks", "avoid walking", "walking limit", "cannot walk more than", "walk no more than")
    )'''
new = '''    walking = any(
        token in value
        for token in (
            "少走",
            "少步行",
            "不能走太多",
            "步行少",
            "走路少",
            "不能超过",
            "不超过",
            "最多走",
            "最多步行",
            "走超过",
            "走不了远路",
            "走不远",
            "走不动",
            "不能走远",
            "不能走",
            "走不了",
            "low walking",
            "walk less",
            "avoid long walks",
            "avoid walking",
            "walking limit",
            "cannot walk more than",
            "walk no more than",
            "cannot walk",
            "can't walk",
            "can not walk",
            "unable to walk",
            "walk far",
        )
    )'''
assert old in s, "walking token list not found"
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
