from pathlib import Path
p = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = p.read_text(encoding="utf-8")

old = '''          <article className="v8-booking-card selected">
            <div className="v8-booking-icon">
              <Icon name="bed" />
            </div>
            <div>
              <span className="v8-selected-label">{t("bookings.stayEvidence")}</span>
              <h2>{selected?.stay.property_name ?? t("bookings.noStay")}</h2>
              <p>
                {selected?.stay.room_type} ·{" "}
                {selected?.stay.refundable
                  ? t("bookings.freeCancel")
                  : t("bookings.nonRefundable")}
              </p>
              <strong data-testid="bookings-stay-total">
                {stayTotalLabel(
                  selected as NonNullable<V8Data["options"][number]>,
                  t,
                  locale,
                )}{" "}
                {t("bookings.total")}
              </strong>
            </div>
            <span className="v8-booking-state">{t("bookings.notBooked")}</span>
          </article>'''
new = '''          {selected ? (
            <article className="v8-booking-card selected">
              <div className="v8-booking-icon">
                <Icon name="bed" />
              </div>
              <div>
                <span className="v8-selected-label">
                  {chosen ? t("bookings.stayEvidence") : t("bookings.stayPreview")}
                </span>
                <h2>{selected.stay.property_name}</h2>
                <p>
                  {selected.stay.room_type} ·{" "}
                  {selected.stay.refundable
                    ? t("bookings.freeCancel")
                    : t("bookings.nonRefundable")}
                </p>
                <strong data-testid="bookings-stay-total">
                  {stayTotalLabel(selected, t, locale)} {t("bookings.total")}
                </strong>
              </div>
              <span className="v8-booking-state">
                {chosen ? t("bookings.notBooked") : t("bookings.notChosen")}
              </span>
            </article>
          ) : (
            <article className="v8-booking-card" data-testid="bookings-no-stay">
              <div className="v8-booking-icon">
                <Icon name="bed" />
              </div>
              <div>
                <span className="v8-selected-label">{t("bookings.stayEvidence")}</span>
                <h2>{t("bookings.noStay")}</h2>
                <p>{t("bookings.noStaySub")}</p>
              </div>
            </article>
          )}'''
assert s.count(old) == 1, "bookings card"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("bookings card patched")
