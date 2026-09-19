from pathlib import Path
p = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = p.read_text(encoding="utf-8")

old = '''function Studio({
  data,
  selected,
  onNavigate,
  onRain,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  onNavigate: (route: string) => void;
  onRain: () => Promise<void>;
}) {'''
new = '''function Studio({
  data,
  selected,
  chosen,
  onNavigate,
  onRain,
}: {
  data: V8Data;
  /**
   * The option being previewed.  `selected` falls back to the first candidate
   * when the traveller has not chosen anything yet, so it is a *preview* and
   * must never be presented as the trip the traveller is on.
   */
  selected: V8Data["options"][number] | null;
  /** The option the traveller actually committed to, or null. */
  chosen: V8Data["options"][number] | null;
  onNavigate: (route: string) => void;
  onRain: () => Promise<void>;
}) {'''
assert s.count(old) == 1, "studio sig"
s = s.replace(old, new)

old2 = '''      <div className="v8-studio-layout">
        <div className="v8-days-column">
          {selected?.days.map((day) => ('''
new2 = '''      <div className="v8-studio-layout">
        <div className="v8-days-column">
          {!chosen && selected && (
            <p className="v8-muted" data-testid="studio-preview-caveat">
              {locale.startsWith("zh")
                ? "以下只是候选方案的预览，你还没有采用它。"
                : "This is a preview of a candidate option - you have not chosen a plan yet."}
            </p>
          )}
          {selected?.days.map((day) => ('''
assert s.count(old2) == 1, "studio day col"
s = s.replace(old2, new2)

old3 = '''          <div className="v8-aside-heading">
            <span>{selected ? t("studio.selectedStay") : t("studio.noStaySelected")}</span>
            <button onClick={() => onNavigate("stay")}>
              {selected ? t("studio.change") : t("studio.chooseStay")}
            </button>
          </div>
          {selected && (
            <div className="v8-selected-stay">
              <div className="v8-hotel-thumb">
                <Icon name="bed" />
              </div>
              <div>
                <b>{selected.stay.property_name}</b>
                <span>{selected.stay.room_type}</span>
                <strong>
                  {money(selected.stay.total_amount_minor, selected.stay.currency, locale)} <small>{t("studio.total")}</small>
                </strong>
              </div>
            </div>
          )}'''
new3 = '''          <div className="v8-aside-heading">
            <span>{chosen ? t("studio.selectedStay") : t("studio.noStaySelected")}</span>
            <button onClick={() => onNavigate("stay")}>
              {chosen ? t("studio.change") : t("studio.chooseStay")}
            </button>
          </div>
          {chosen && (
            <div className="v8-selected-stay">
              <div className="v8-hotel-thumb">
                <Icon name="bed" />
              </div>
              <div>
                <b>{chosen.stay.property_name}</b>
                <span>{chosen.stay.room_type}</span>
                <strong>
                  {stayTotalLabel(chosen, t, locale)}{" "}
                  <small>{t("studio.total")}</small>
                </strong>
              </div>
            </div>
          )}'''
assert s.count(old3) == 1, "studio aside"
s = s.replace(old3, new3)

old4 = '''          <div className="v8-cost-lines">
            <div>
              <span>{t("studio.stayTotal")}</span>
              {/* A total is only known once a stay is chosen, and OSM carries
                  no price: unknown must read as unknown, never as ¥0.00. */}
              <b>
                {!selected
                  ? t("studio.notChosen")
                  : (selected.stay.nightly_amount_minor ?? 0) > 0 ||
                      (selected.stay_total_minor ?? 0) > 0
                    ? money(selected.stay_total_minor, selected.stay.currency ?? data.trip.stay_budget.currency, locale)
                    : t("studio.priceUnknown")}
              </b>
            </div>
            <div>
              <span>{t("studio.dailyMovement")}</span>
              <b>{money(selected?.daily_travel_minor, selected?.stay.currency ?? data.journey.budget.currency, locale)}</b>
            </div>
            <div>
              <span>{t("studio.walkingExposure")}</span>
              <b>{selected?.walking_min} min</b>
            </div>
            <div className="total">
              <span>{t("studio.planHealth")}</span>
              <b className="green">
                {t("studio.protected", { n: selected?.protected_margin_min ?? 0 })}
              </b>
            </div>
          </div>'''
new4 = '''          <div className="v8-cost-lines">
            <div>
              <span>{t("studio.stayTotal")}</span>
              {/* A total is only known once a stay is chosen, and OSM carries
                  no price: unknown must read as unknown, never as ¥0.00. */}
              <b data-testid="studio-stay-total">
                {!chosen
                  ? t("studio.notChosen")
                  : (chosen.stay.nightly_amount_minor ?? 0) > 0 ||
                      (chosen.stay_total_minor ?? 0) > 0
                    ? money(chosen.stay_total_minor, chosen.stay.currency ?? data.trip.stay_budget.currency, locale)
                    : t("studio.priceUnknown")}
              </b>
            </div>
            <div>
              <span>{t("studio.dailyMovement")}</span>
              <b>
                {chosen
                  ? money(chosen.daily_travel_minor, chosen.stay.currency ?? data.journey.budget.currency, locale)
                  : t("studio.notChosen")}
              </b>
            </div>
            <div>
              <span>{t("studio.walkingExposure")}</span>
              <b>{chosen ? `${chosen.walking_min} min` : t("studio.notChosen")}</b>
            </div>
            <div className="total">
              <span>{t("studio.planHealth")}</span>
              <b className={data.active_plan ? "green" : ""}>
                {data.active_plan
                  ? t("studio.protected", { n: chosen?.protected_margin_min ?? 0 })
                  : t("studio.notChosen")}
              </b>
            </div>
          </div>'''
assert s.count(old4) == 1, "studio cost lines"
s = s.replace(old4, new4)

old5 = '''function Studio({'''
new5 = '''/** A chosen stay with no provider rate must not print as 0.00. */
function stayTotalLabel(
  option: NonNullable<V8Data["options"][number]>,
  t: (key: string, params?: Record<string, string | number>) => string,
  locale: string,
): string {
  const known =
    (option.stay.nightly_amount_minor ?? 0) > 0 || (option.stay_total_minor ?? 0) > 0;
  if (!known) return t("studio.priceUnknown");
  return money(option.stay.total_amount_minor, option.stay.currency, locale);
}

function Studio({'''
assert s.count(old5) == 1, "studio helper anchor"
s = s.replace(old5, new5, 1)

old6 = '''            <Studio
              data={data}
              selected={selected}
              onNavigate={navigate}
              onRain={triggerRain}
            />'''
new6 = '''            <Studio
              data={data}
              selected={selected}
              chosen={chosenOption}
              onNavigate={navigate}
              onRain={triggerRain}
            />'''
assert s.count(old6) == 1, "main studio call"
s = s.replace(old6, new6)

old7 = '''          <Studio
            data={data}
            selected={selected}
            onNavigate={onNavigate}
            onRain={onRain}
          />'''
new7 = '''          <Studio
            data={data}
            selected={selected}
            chosen={chosenOption}
            onNavigate={onNavigate}
            onRain={onRain}
          />'''
assert s.count(old7) == 1, "spend studio call"
s = s.replace(old7, new7)

p.write_text(s, encoding="utf-8")
print("Studio patched")
