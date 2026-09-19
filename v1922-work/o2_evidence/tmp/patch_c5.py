from pathlib import Path

# ---------- i18n: honest budget wording ----------
p = Path("D:/moodle/CityNexus/frontend/src/i18n/LocaleContext.tsx")
s = p.read_text(encoding="utf-8")

en = '  "studio.feasibilitySub": "Arrival, departure, budget, and protected commitments verified.",\n'
zh = '  "studio.feasibilitySub": "到达、出发、预算和受保护承诺已验证。",\n'
assert s.count(en) == 1 and s.count(zh) == 1, "feasibility keys"
s = s.replace(en, en + '  "studio.feasibilityNoPrice": "Arrival, departure, and protected commitments verified. Budget not verified: no stop has a provider price yet.",\n')
s = s.replace(zh, zh + '  "studio.feasibilityNoPrice": "到达、出发和受保护承诺已验证。预算未验证：目前没有任何一站拿到供应商价格。",\n')
p.write_text(s, encoding="utf-8")
print("i18n patched")

# ---------- Studio: only claim what was actually checked ----------
p = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = p.read_text(encoding="utf-8")

old = '''          {/* The plan gate has nothing to validate before a plan exists. */}
          {data.active_plan ? (
            <div className="v8-feasibility">
              <span className="status-dot" />
              <div>
                <b>{t("studio.feasibilityPassed")}</b>
                <small>
                  {t("studio.feasibilitySub")}
                </small>
              </div>
            </div>'''
new = '''          {/* The plan gate has nothing to validate before a plan exists, and
              it cannot verify a budget it has no prices for: a stop with no
              provider price is not a free stop.  Claiming "budget verified"
              over an all-unknown itinerary is a fabricated fact. */}
          {data.active_plan ? (
            <div className="v8-feasibility" data-testid="studio-feasibility">
              <span className="status-dot" />
              <div>
                <b>{t("studio.feasibilityPassed")}</b>
                <small>
                  {pricedStops > 0
                    ? t("studio.feasibilitySub")
                    : t("studio.feasibilityNoPrice")}
                </small>
              </div>
            </div>'''
assert s.count(old) == 1, "studio feasibility block"
s = s.replace(old, new)

old2 = '''  const [draftImpact, setDraftImpact] = useState<{ day: number; count: number } | null>(null);
  return (
    <section className="v8-page" data-testid="v8-trip-studio">'''
new2 = '''  const [draftImpact, setDraftImpact] = useState<{ day: number; count: number } | null>(null);
  // How many stops carry real cost evidence?  Only then can the budget part of
  // the safety check be described as verified.
  const pricedStops = (data.active_plan?.activities ?? []).filter((item) => {
    const meta = (item.metadata ?? {}) as Record<string, unknown>;
    const status = String(meta.cost_status ?? "").toUpperCase();
    if (status === "KNOWN" || status === "KNOWN_FREE" || status === "KNOWN_PAID") return true;
    if (status === "UNKNOWN") return false;
    return meta.price_known === true;
  }).length;
  return (
    <section className="v8-page" data-testid="v8-trip-studio">'''
assert s.count(old2) == 1, "studio pricedStops"
s = s.replace(old2, new2)

p.write_text(s, encoding="utf-8")
print("Studio patched")
