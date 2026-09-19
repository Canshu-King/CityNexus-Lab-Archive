import { useT } from "../i18n";
import { testIds } from "../testids";
import type { PulseState } from "../types";
import { RuntimeTruthBadge } from "./RuntimeTruthBadge";

export function JourneyPulse({
  pulse,
  nowTitle,
  nextTitle,
  riskLevelLabel,
  actionLabel,
  nowNote,
  nextNote,
  riskTitle,
  riskDetail,
  actionReason,
  onPrimaryAction,
}: {
  pulse: PulseState;
  nowTitle: string;
  nextTitle: string;
  riskLevelLabel: string;
  actionLabel: string;
  nowNote: string;
  nextNote: string;
  riskTitle: string;
  riskDetail: string;
  actionReason: string;
  onPrimaryAction: () => void;
}) {
  const t = useT();
  return (
    <section className="pulse" data-testid={testIds.journeyPulse}>
      <header className="pulse__head">
        <div>
          <span className="kicker">{t("pulse.kicker")}</span>
          <h2>{t("pulse.title")}</h2>
        </div>
        <RuntimeTruthBadge truth={{ semantic: "DeepSeek", execution: "DIRECT", truth: "CityNexus", source: "RECORDED_FIXTURE" }} compact />
      </header>
      <div className="pulse__grid">
        <article className="pulse-card now" data-testid={testIds.pulseNow}>
          <span className="pulse-card__label">{t("pulse.now")}</span>
          <strong>{nowTitle}</strong>
          <span className="pulse-card__time">{pulse.now.time}</span>
          <p>{nowNote}</p>
        </article>
        <article className="pulse-card next" data-testid={testIds.pulseNext}>
          <span className="pulse-card__label">{t("pulse.next")}</span>
          <strong>{nextTitle}</strong>
          <span className="pulse-card__time">{pulse.next.time}</span>
          <p>
            {t("pulse.buffer", { n: pulse.next.buffer_min })} · {nextNote}
          </p>
        </article>
        <article className={`pulse-card risk ${pulse.risk.level}`} data-testid={testIds.pulseRisk}>
          <span className="pulse-card__label">{t("pulse.risk")}</span>
          <strong>
            {riskLevelLabel} · {riskTitle}
          </strong>
          <span className="pulse-card__source">{pulse.risk.source}</span>
          <p>{riskDetail}</p>
        </article>
        <article className="pulse-card action" data-testid={testIds.pulseAction}>
          <span className="pulse-card__label">{t("pulse.action")}</span>
          <strong>{actionLabel}</strong>
          <p>{actionReason}</p>
          <button type="button" className="btn btn--primary" onClick={onPrimaryAction}>
            {t("pulse.openRecovery")}
          </button>
        </article>
      </div>
      <details className="technical" data-testid={testIds.technicalEvidence}>
        <summary>{t("pulse.technical")}</summary>
        <div className="technical__body">
          <p>{t("pulse.technicalHint")}</p>
          <dl>
            <div>
              <dt>{t("pulse.dataSource")}</dt>
              <dd>RECORDED_FIXTURE</dd>
            </div>
            <div>
              <dt>{t("pulse.planVersion")}</dt>
              <dd>V18.1-reference-r1</dd>
            </div>
            <div>
              <dt>{t("pulse.generatedAt")}</dt>
              <dd>2026-09-15T08:12:00+08:00</dd>
            </div>
            <div>
              <dt>{t("runtime.execution")}</dt>
              <dd>DIRECT</dd>
            </div>
          </dl>
        </div>
      </details>
    </section>
  );
}
