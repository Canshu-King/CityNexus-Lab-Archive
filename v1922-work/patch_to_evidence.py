from pathlib import Path
P = Path("D:/moodle/CityNexus/backend/app/replanning/provider_snapshots.py")
s = P.read_text(encoding="utf-8")
old = '''                    "walking_distance_m": fact.walking_distance_m,
                    "walking_min": fact.walking_min,
                }'''
new = '''                    "walking_distance_m": fact.walking_distance_m,
                    "walking_min": fact.walking_min,
                    "mode": fact.mode,
                }'''
assert old in s
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
