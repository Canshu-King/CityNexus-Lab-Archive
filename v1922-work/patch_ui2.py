"""Pass recovery data into AuthoritativeExecution."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = P.read_text(encoding="utf-8")

old = """              policy={policy}
              loading={authoritativePlans.isLoading || authoritativeTwin.isLoading}
              onRefresh={() => void refreshAuthoritativeTruth(data.journey.id)}
            />"""
new = """              policy={policy}
              loading={authoritativePlans.isLoading || authoritativeTwin.isLoading}
              recovery={data.recovery}
              flags={data.experience_flags}
              onRefresh={() => void refreshAuthoritativeTruth(data.journey.id)}
            />"""
assert old in s, "AuthoritativeExecution call site not found"
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
