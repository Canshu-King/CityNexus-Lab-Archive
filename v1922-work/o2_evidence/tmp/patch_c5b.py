from pathlib import Path
p = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = p.read_text(encoding="utf-8")

# Studio takes the authoritative plan so it can read real cost evidence
old = '''function Studio({
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
new = '''function Studio({
  data,
  selected,
  chosen,
  plan,
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
  /** The authoritative plan, whose activities carry the cost evidence. */
  plan: PlanVersion | null;
  onNavigate: (route: string) => void;
  onRain: () => Promise<void>;
}) {'''
assert s.count(old) == 1, "studio signature"
s = s.replace(old, new)

old2 = '''  // How many stops carry real cost evidence?  Only then can the budget part of
  // the safety check be described as verified.
  const pricedStops = (data.active_plan?.activities ?? []).filter((item) => {
    const meta = (item.metadata ?? {}) as Record<string, unknown>;
    const status = String(meta.cost_status ?? "").toUpperCase();
    if (status === "KNOWN" || status === "KNOWN_FREE" || status === "KNOWN_PAID") return true;
    if (status === "UNKNOWN") return false;
    return meta.price_known === true;
  }).length;'''
new2 = '''  // How many stops carry real cost evidence?  Only then can the budget part of
  // the safety check be described as verified.  The evidence lives on the
  // authoritative plan's activities (`cost_status`), not on the /experience
  // projection, so it is read from `plan`.
  const planActivities = plan?.activities ?? [];
  const pricedStops = planActivities.filter((item) => {
    const status = String(
      (item as { cost_status?: string | null }).cost_status ?? "",
    ).toUpperCase();
    if (status === "KNOWN" || status === "KNOWN_FREE" || status === "KNOWN_PAID") return true;
    if (status === "UNKNOWN") return false;
    return (item.estimated_cost?.amount_minor ?? 0) > 0;
  }).length;
  const hasPricedEvidence = planActivities.length > 0 && pricedStops > 0;'''
assert s.count(old2) == 1, "pricedStops"
s = s.replace(old2, new2)

old3 = '''                  {pricedStops > 0
                    ? t("studio.feasibilitySub")
                    : t("studio.feasibilityNoPrice")}'''
new3 = '''                  {hasPricedEvidence
                    ? t("studio.feasibilitySub")
                    : t("studio.feasibilityNoPrice")}'''
assert s.count(old3) == 1, "feasibility copy"
s = s.replace(old3, new3)

# call sites pass the authoritative plan
old4 = '''            <Studio
              data={data}
              selected={selected}
              chosen={chosenOption}
              onNavigate={navigate}
              onRain={triggerRain}
            />'''
new4 = '''            <Studio
              data={data}
              selected={selected}
              chosen={chosenOption}
              plan={authoritativePlan}
              onNavigate={navigate}
              onRain={triggerRain}
            />'''
assert s.count(old4) == 1, "main studio call"
s = s.replace(old4, new4)

old5 = '''          <Studio
            data={data}
            selected={selected}
            chosen={chosen}
            onNavigate={onNavigate}
            onRain={onRain}
          />'''
new5 = '''          <Studio
            data={data}
            selected={selected}
            chosen={chosen}
            plan={plan}
            onNavigate={onNavigate}
            onRain={onRain}
          />'''
assert s.count(old5) == 1, "spend studio call"
s = s.replace(old5, new5)

# TripsWorkspace needs the plan too
old6 = '''function TripsWorkspace({
  data,
  selected,
  chosen,
  wallet,'''
new6 = '''function TripsWorkspace({
  data,
  selected,
  chosen,
  plan,
  wallet,'''
assert s.count(old6) == 1, "trips sig"
s = s.replace(old6, new6)

old7 = '''  data: V8Data;
  selected: V8Data["options"][number] | null;
  chosen: V8Data["options"][number] | null;
  wallet: Wallet | null;'''
new7 = '''  data: V8Data;
  selected: V8Data["options"][number] | null;
  chosen: V8Data["options"][number] | null;
  plan: PlanVersion | null;
  wallet: Wallet | null;'''
assert s.count(old7) == 1, "trips prop types"
s = s.replace(old7, new7)

old8 = '''            <TripsWorkspace
              data={data}
              selected={selected}
              chosen={chosenOption}
              wallet={wallet}'''
new8 = '''            <TripsWorkspace
              data={data}
              selected={selected}
              chosen={chosenOption}
              plan={authoritativePlan}
              wallet={wallet}'''
assert s.count(old8) == 1, "trips call"
s = s.replace(old8, new8)

p.write_text(s, encoding="utf-8")
print("Studio plan wiring patched")
