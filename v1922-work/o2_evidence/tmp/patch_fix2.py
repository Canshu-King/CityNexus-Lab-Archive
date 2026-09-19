from pathlib import Path
p = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = p.read_text(encoding="utf-8")

# Hub signature
old = '''function Hub({
  data,
  selected,
  onNavigate,
  onNewJourney,
  onPlanWithAi,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  onNavigate: (route: string) => void;
  onNewJourney: () => void;
  onPlanWithAi: () => void;
}) {'''
new = '''function Hub({
  data,
  selected,
  hasChosenPlan,
  onNavigate,
  onNewJourney,
  onPlanWithAi,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  /** True only when the traveller actually adopted a plan. */
  hasChosenPlan: boolean;
  onNavigate: (route: string) => void;
  onNewJourney: () => void;
  onPlanWithAi: () => void;
}) {'''
assert s.count(old) == 1, "hub sig"
s = s.replace(old, new)

# spend-tab Studio: pass the TripsWorkspace `chosen` prop
old2 = '''          <Studio
            data={data}
            selected={selected}
            chosen={chosenOption}
            onNavigate={onNavigate}
            onRain={onRain}
          />'''
new2 = '''          <Studio
            data={data}
            selected={selected}
            chosen={chosen}
            onNavigate={onNavigate}
            onRain={onRain}
          />'''
assert s.count(old2) == 1, "spend studio"
s = s.replace(old2, new2)

p.write_text(s, encoding="utf-8")
print("fixed")
