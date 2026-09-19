from pathlib import Path
p = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = p.read_text(encoding="utf-8")

old = '''  const selected =
    data?.options.find((item) => item.id === data.selected_option_id) ??
    data?.options[0] ??
    null;
  const navigate = (next: string) => {'''
new = '''  // `selected` is what to preview: the traveller's own choice, or the best
  // candidate so the screens are never empty.  `chosenOption` is what the
  // traveller actually committed to, and is the only thing that may be called
  // "your stay" or counted as spend.
  const selected =
    data?.options.find((item) => item.id === data.selected_option_id) ??
    data?.options[0] ??
    null;
  const chosenOption =
    data?.options.find((item) => item.id === data.selected_option_id) ??
    data?.options.find((item) => item.status === "SELECTED") ??
    null;
  const navigate = (next: string) => {'''
assert s.count(old) == 1, "selected anchor"
s = s.replace(old, new)

old2 = '''function TripsWorkspace({
  data,
  selected,
  wallet,
  onNavigate,
  onRain,
  onImport,
  busy,
  onOpenCopilot,
  onOpenActivity,
  onRefresh,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  wallet: Wallet | null;'''
new2 = '''function TripsWorkspace({
  data,
  selected,
  chosen,
  wallet,
  onNavigate,
  onRain,
  onImport,
  busy,
  onOpenCopilot,
  onOpenActivity,
  onRefresh,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  chosen: V8Data["options"][number] | null;
  wallet: Wallet | null;'''
assert s.count(old2) == 1, "trips sig"
s = s.replace(old2, new2)

old4 = '''  // Only a *chosen* stay is a committed cost.  Summing every candidate option
  // would invent a spend the traveller never agreed to.
  const chosenStayOption =
    data.options.find((option) => option.id === data.selected_option_id) ??
    data.options.find((option) => option.status === "SELECTED") ??
    null;'''
new4 = '''  // Only a *chosen* stay is a committed cost.  Summing every candidate option
  // would invent a spend the traveller never agreed to.
  const chosenStayOption = chosen;'''
assert s.count(old4) == 1, "chosenStayOption"
s = s.replace(old4, new4)

old6 = '''            <TripsWorkspace
              data={data}
              selected={selected}
              wallet={wallet}'''
new6 = '''            <TripsWorkspace
              data={data}
              selected={selected}
              chosen={chosenOption}
              wallet={wallet}'''
assert s.count(old6) == 1, "trips call"
s = s.replace(old6, new6)

p.write_text(s, encoding="utf-8")
print("chosen wiring patched")
