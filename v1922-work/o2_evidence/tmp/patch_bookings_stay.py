from pathlib import Path
p = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = p.read_text(encoding="utf-8")

old = '''              <strong>{money(selected?.stay.total_amount_minor, selected?.stay.currency ?? data.journey.budget.currency, locale)} {t("bookings.total")}</strong>'''
new = '''              <strong data-testid="bookings-stay-total">
                {stayTotalLabel(
                  selected as NonNullable<V8Data["options"][number]>,
                  t,
                  locale,
                )}{" "}
                {t("bookings.total")}
              </strong>'''
assert s.count(old) == 1, "bookings stay total"
s = s.replace(old, new)

# bookings card is only meaningful when an option is previewed/chosen; guard it
old2 = '''          <article className="v8-booking-card selected">
            <div className="v8-booking-icon">
              <Icon name="bed" />
            </div>'''
assert s.count(old2) == 1

p.write_text(s, encoding="utf-8")
print("bookings stay total patched")
