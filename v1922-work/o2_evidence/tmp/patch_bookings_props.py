from pathlib import Path
p = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = p.read_text(encoding="utf-8")

old = '''function Bookings({
  data,
  selected,
  wallet,
  onImport,
  busy,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  wallet: Wallet | null;'''
new = '''function Bookings({
  data,
  selected,
  chosen,
  wallet,
  onImport,
  busy,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  chosen: V8Data["options"][number] | null;
  wallet: Wallet | null;'''
assert s.count(old) == 1, "bookings sig"
s = s.replace(old, new)

# TripsWorkspace passes Bookings inside the Advanced drawer
old2 = '''            <Bookings
              data={data}
              selected={selected}
              wallet={wallet}
              onImport={onImport}
              busy={busy}
            />'''
new2 = '''            <Bookings
              data={data}
              selected={selected}
              chosen={chosen}
              wallet={wallet}
              onImport={onImport}
              busy={busy}
            />'''
assert s.count(old2) == 1, "bookings call in trips"
s = s.replace(old2, new2)

p.write_text(s, encoding="utf-8")
print("bookings props patched")
