import { useMemo, useState } from "react";
import type { V8Data } from "../../app/v8Types";
import { useLocale, useT } from "../../i18n/LocaleContext";

/** Currencies whose smallest unit is the unit itself — never divide by 100. */
const ZERO_DECIMAL = new Set(["JPY", "KRW", "VND", "IDR", "CLP"]);

function formatMoney(minor: number, currency: string, locale: string) {
  const value = ZERO_DECIMAL.has(currency.toUpperCase()) ? minor : minor / 100;
  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency,
      maximumFractionDigits: ZERO_DECIMAL.has(currency.toUpperCase()) ? 0 : 2,
    }).format(value);
  } catch {
    return `${value} ${currency}`;
  }
}

function nightsBetween(startAt: string, endAt: string) {
  const start = new Date(startAt);
  const end = new Date(endAt);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 0;
  const day = 24 * 60 * 60 * 1000;
  const startDate = Date.UTC(start.getUTCFullYear(), start.getUTCMonth(), start.getUTCDate());
  const endDate = Date.UTC(end.getUTCFullYear(), end.getUTCMonth(), end.getUTCDate());
  return Math.max(0, Math.round((endDate - startDate) / day));
}

export function AgentComposer({
  data,
  onSubmit,
  busy,
}: {
  data: V8Data;
  onSubmit: (command: string) => Promise<void>;
  busy: boolean;
}) {
  const t = useT();
  const { locale } = useLocale();
  // V16: this used to be pre-filled with a canned demo mission ("Keep the hotel
  // under 700…"). A real traveller opening the desk saw a stranger's request
  // already typed, and pressing the button submitted it. An empty box with an
  // example placeholder is the honest default.
  const [command, setCommand] = useState("");

  // The summary panel used to hard-code "Hotel total ≤ CNY 700 · low walking"
  // on every journey, including GBP and JPY ones. Derive it from the journey.
  const summary = useMemo(() => {
    const stay = data.trip?.stay_budget;
    const amount = stay
      ? formatMoney(stay.amount_minor, stay.currency ?? "CNY", locale)
      : "—";
    return t("agent.staySummary", {
      amount,
      nights: nightsBetween(data.journey.start_at, data.journey.end_at),
      city: data.journey.city_code,
    });
  }, [data.journey.city_code, data.journey.end_at, data.journey.start_at, data.trip?.stay_budget, locale, t]);

  const canSubmit = !busy && command.trim().length > 0;

  return (
    <section className="v8-page" data-testid="v8-agent-composer">
      <div className="v8-page-intro compact">
        <div>
          <p className="v8-kicker">{t("agent.kicker")}</p>
          <h1>{t("agent.title")}</h1>
          <p className="v8-lede">{t("agent.lede")}</p>
        </div>
        <span className="v8-status-pill violet">
          {data.traveler_twin?.learned_soft_dimensions?.length
            ? t("agent.twinActive")
            : t("agent.twinReady")}
        </span>
      </div>
      <div className="v8-agent-composer-card">
        <div className="v8-agent-copy">
          <span className="v8-agent-mark">{t("agent.brand")}</span>
          <h2>{t("agent.whatChange")}</h2>
          <p>{t("agent.whatChangeSub")}</p>
          <div className="v8-agent-boundary">
            <b>{t("agent.authorityBoundary")}</b>
            <span>{t("agent.boundarySub")}</span>
          </div>
        </div>
        <div className="v8-agent-input">
          <label htmlFor="v8-agent-input">{t("agent.mission")}</label>
          <textarea
            id="v8-agent-input"
            value={command}
            onChange={(event) => setCommand(event.target.value)}
            placeholder={t("agent.placeholder")}
            data-testid="v8-agent-input"
          />
          <div className="v8-agent-toolbar">
            <span>
              {t("agent.journeyPrefix")} {data.journey.title}
            </span>
            <button
              className="v8-primary"
              data-testid="v8-agent-submit"
              disabled={!canSubmit}
              onClick={() => void onSubmit(command)}
            >
              {busy ? t("agent.working") : t("agent.handlePlan")}
            </button>
          </div>
        </div>
      </div>
      <div className="v8-agent-progress">
        <span className="v8-kicker">{t("agent.recentUnderstanding")}</span>
        <div>
          <b>{t("agent.stayMobility")}</b>
          <span>{summary}</span>
        </div>
        <div>
          <b>{t("agent.protected")}</b>
          <span>{t("agent.protectedSummary")}</span>
        </div>
      </div>
    </section>
  );
}
