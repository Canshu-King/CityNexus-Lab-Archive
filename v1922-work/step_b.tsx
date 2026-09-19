
const PACE_OPTIONS = [
  { key: "relaxed", zh: "轻松", en: "Relaxed" },
  { key: "balanced", zh: "适中", en: "Balanced" },
  { key: "packed", zh: "紧凑", en: "Packed" },
] as const;

const INTEREST_OPTIONS = [
  { key: "food", zh: "美食", en: "Food" },
  { key: "nature", zh: "自然", en: "Nature" },
  { key: "culture", zh: "人文", en: "Culture" },
  { key: "seaside", zh: "海边", en: "Seaside" },
  { key: "shopping", zh: "购物", en: "Shopping" },
  { key: "family", zh: "亲子", en: "Family" },
] as const;

export function JourneyTrialSetup({
  onCreate,
  onUseTianjinDemo,
  onCancel,
  busy,
}: {
  onCreate: (draft: JourneyTrialDraft) => Promise<void>;
  onUseTianjinDemo: () => Promise<void>;
  onCancel?: () => void;
  busy: boolean;
}) {
  const t = useT();
  const { locale, switchLocale } = useLocale();
  const zh = locale.startsWith("zh");
  const browserTimezone = useMemo(
    () => Intl.DateTimeFormat().resolvedOptions().timeZone || "Asia/Shanghai",
    [],
  );
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [advanced, setAdvanced] = useState(false);
  const [draft, setDraft] = useState<JourneyTrialDraft>({
    cityName: "",
    countryCode: "CN",
    timezone: browserTimezone,
    startAt: futureLocalAt(1, 10),
    endAt: futureLocalAt(3, 20),
    arrivalLocation: "",
    departureLocation: "",
    budgetMajor: 3000,
    stayBudgetMajor: 1000,
    currency: "CNY",
    partySize: 2,
    rooms: 1,
    pace: "relaxed",
    interests: [],
    specialRequirements: "",
  });
  const [roomsTouched, setRoomsTouched] = useState(false);

  const update = <K extends keyof JourneyTrialDraft>(key: K, value: JourneyTrialDraft[K]) =>
    setDraft((current) => ({ ...current, [key]: value }));

  // Corrections §5: infer country / timezone / currency from the city and keep
  // the technical fields behind "Advanced settings".
  const applyCity = (cityName: string) => {
    const facts = inferCityFacts(cityName);
    setDraft((current) => ({
      ...current,
      cityName,
      ...(facts
        ? { countryCode: facts.country, timezone: facts.timezone, currency: facts.currency }
        : {}),
    }));
  };

  const facts = inferCityFacts(draft.cityName);
  const step1Ready = draft.cityName.trim().length > 0;
  const step2Ready = draft.partySize >= 1 && draft.budgetMajor > 0;

  const stepTitle = zh
    ? ["目的地与时间", "人数与偏好", "确认创建"]
    : ["Destination & dates", "Travellers & preferences", "Review & create"];

  const submit = async () => {
    await onCreate(draft);
  };

  return (
    <section className="v8-page" data-testid="trial-setup">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">{t("trial.kicker")}</p>
          <h1>{zh ? "新建行程" : "Create a trip"}</h1>
          <p className="v8-lede">
            {zh
              ? "三步完成。选择目的地、告诉我们怎么玩，剩下的交给 CityNexus。"
              : "Three steps. Pick a destination, tell us how you like to travel, and let CityNexus handle the rest."}
          </p>
        </div>
        <button
          type="button"
          className="v8-outline-button"
          aria-label="Switch language"
          onClick={switchLocale}
        >
          {zh ? "EN" : "中文"}
        </button>
      </div>

      <ol className="trial-steps" data-testid="trial-steps">
        {stepTitle.map((label, index) => {
          const n = (index + 1) as 1 | 2 | 3;
          return (
            <li
              key={label}
              className={n === step ? "active" : n < step ? "done" : ""}
              data-testid={`trial-step-${n}`}
            >
              <span className="trial-step-dot">{n < step ? "✓" : n}</span>
              <span>{label}</span>
            </li>
          );
        })}
      </ol>

      {step === 1 && (
        <div className="v8-card trial-card" data-testid="trial-step1-body">
          <label className="trial-field">
            <span>{zh ? "目的地" : "Destination"}</span>
            <input
              data-testid="trial-city"
              value={draft.cityName}
              onChange={(event) => applyCity(event.target.value)}
              placeholder={zh ? "例如：厦门" : "e.g. Xiamen"}
              autoFocus
            />
          </label>

          {facts && (
            <p className="trial-inferred" data-testid="trial-inferred">
              {zh ? "已自动设置：" : "Auto-set: "}
              {facts.label} · {currencyLabel(draft.currency, locale)} ·{" "}
              {timezoneLabel(draft.timezone, locale)}
            </p>
          )}

          <label className="trial-field">
            <span>{zh ? "抵达厦门" : "Arrive at"}</span>
            <input
              data-testid="trial-arrival"
              value={draft.arrivalLocation}
              onChange={(event) => update("arrivalLocation", event.target.value)}
              placeholder={zh ? "例如：厦门高崎国际机场" : "e.g. Xiamen Gaoqi Intl Airport"}
            />
          </label>
          <label className="trial-field">
            <span>{zh ? "离开厦门" : "Depart from"}</span>
            <input
              data-testid="trial-departure"
              value={draft.departureLocation}
              onChange={(event) => update("departureLocation", event.target.value)}
              placeholder={zh ? "例如：厦门北站" : "e.g. Xiamen North Station"}
            />
          </label>
          <div className="trial-row">
            <label className="trial-field">
              <span>{zh ? "抵达时间" : "Arrival time"}</span>
              <input
                data-testid="trial-start"
                type="datetime-local"
                value={draft.startAt}
                onChange={(event) => update("startAt", event.target.value)}
              />
            </label>
            <label className="trial-field">
              <span>{zh ? "离开时间" : "Departure time"}</span>
              <input
                data-testid="trial-end"
                type="datetime-local"
                value={draft.endAt}
                onChange={(event) => update("endAt", event.target.value)}
              />
            </label>
          </div>

          <details
            className="trial-advanced"
            open={advanced}
            onToggle={(event) => setAdvanced((event.target as HTMLDetailsElement).open)}
          >
            <summary>{zh ? "高级设置" : "Advanced settings"}</summary>
            <div className="trial-row">
              <label className="trial-field">
                <span>{t("trial.country")}</span>
                <input
                  data-testid="trial-country"
                  value={draft.countryCode}
                  onChange={(event) => update("countryCode", event.target.value.toUpperCase().slice(0, 3))}
                />
              </label>
              <label className="trial-field">
                <span>{t("trial.timezone")}</span>
                <input
                  data-testid="trial-timezone"
                  value={draft.timezone}
                  onChange={(event) => update("timezone", event.target.value)}
                />
              </label>
              <label className="trial-field">
                <span>{t("trial.currency")}</span>
                <input
                  data-testid="trial-currency"
                  value={draft.currency}
                  onChange={(event) => update("currency", event.target.value.toUpperCase().slice(0, 3))}
                />
              </label>
            </div>
          </details>
        </div>
      )}
