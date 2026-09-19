from pathlib import Path
P = Path("D:/moodle/CityNexus/backend/app/operations/v9.py")
s = P.read_text(encoding="utf-8")
old = '''        raise ValueError(
            "MID_TRIP reservation requires a resolvable semantic target "
            "(a structural or synthetic placeholder is not accepted)"
        )'''
new = '''        raise ValueError(
            "MID_TRIP reservation requires a non-structural semantic target"
        )'''
assert old in s
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
