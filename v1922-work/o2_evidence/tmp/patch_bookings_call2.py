from pathlib import Path
p = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = p.read_text(encoding="utf-8")
old = '''              <Bookings
                data={data}
                selected={selected}
                wallet={wallet}
                onImport={importReservation}
                busy={busy}
              />'''
new = '''              <Bookings
                data={data}
                selected={selected}
                chosen={chosenOption}
                wallet={wallet}
                onImport={importReservation}
                busy={busy}
              />'''
assert s.count(old) == 1, "route bookings call"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("ok")
