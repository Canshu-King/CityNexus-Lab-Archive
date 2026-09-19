import { useState } from "react";
import { useLocale, useT } from "../i18n";
import { testIds } from "../testids";
import type { RecoveryProposal } from "../types";
import { PULSE_I18N, pick } from "../data/journey";
import { RuntimeTruthBadge } from "./RuntimeTruthBadge";

function activityLabel(id: string, fallback: string): { en: string; zh: string } {
  const known: Record<string, { en: string; zh: string }> = {
    "act-morning-walk": { en: "Five Great Avenues morning walk", zh: "五大道晨间步行" },
    "act-river-cruise": { en: "Haihe River cruise (C4 protected)", zh: "海河游船（C4 受保护）" },
    "act-market-window": { en: "Ancient Culture Street market window", zh: "古文化街市场时间窗" },
    "act-lunch": { en: "Lunch reservation · Nanshi Food Street", zh: "午餐预订 · 南市食品街" },
    "act-museum-early": { en: "Tianjin Museum indoor window", zh: "天津博物馆室内时间窗" },
  };
  return known[id] ?? { en: fallback, zh: fallback };
}

export function RecoveryDiff({ proposal }: { proposal: RecoveryProposal }) {
  const t = useT();
  const { locale } = useLocale();
  const [accepted, setAccepted] = useState(false);
  const [rejected, setRejected] = useState(false);

  const money = (minor: number) =>
    minor === 0 ? "¥0" : `${minor > 0 ? "+" : "−"}¥${(Math.abs(minor) / 100).toFixed(2)}`;

  return (
    <section className="recovery" data-testid={testIds.recoveryDiff}>
      <header className="recovery__head">
        <div>
          <span className="kicker">{t("recovery.kicker")}</span>
          <h2>{t("recovery.title")}</h2>
          <p className="muted">{pick(PULSE_I18N.recoveryTrigger, locale)}</p>
        </div>
        <RuntimeTruthBadge
          truth={{ semantic: "DeepSeek", execution: "DIRECT", truth: "CityNexus", source: "RECORDED_FIXTURE" }}
          compact
        />
      </header>
      <div className="recovery__grid">
        <article className="recovery-col before" data-testid={testIds.recoveryBefore}>
          <h3>{t("recovery.before")}</h3>
          <ol>
            {proposal.before.map((activity) => {
              const label = activityLabel(activity.id, activity.title);
              return (
                <li key={activity.id} className={activity.protected ? "protected" : undefined}>
                  <time>{activity.start_at.slice(11, 16)}</time>
                  <span>{pick(label, locale)}</span>
                  {activity.protected && <em>C4</em>}
                </li>
              );
            })}
          </ol>
        </article>
        <article className="recovery-col after" data-testid={testIds.recoveryAfter}>
          <h3>{t("recovery.after")}</h3>
          <ol>
            {proposal.after.map((activity) => {
              const label = activityLabel(activity.id, activity.title);
              const changed = activity.status === "candidate";
              return (
                <li key={activity.id} className={`${activity.protected ? "protected" : ""} ${changed ? "changed" : ""}`}>
                  <time>{activity.start_at.slice(11, 16)}</time>
                  <span>{pick(label, locale)}</span>
                  {activity.protected && <em>C4</em>}
                  {changed && <em className="changed-tag">CHANGED</em>}
                </li>
              );
            })}
          </ol>
        </article>
      </div>
      <div className="recovery__metrics">
        <div>
          <small>{t("recovery.costDelta")}</small>
          <b data-testid={testIds.recoveryCostDelta}>{money(proposal.cost_delta_minor)}</b>
        </div>
        <div>
          <small>{t("recovery.travelDelta")}</small>
          <b data-testid={testIds.recoveryTravelDelta}>+{proposal.travel_delta_min} min</b>
        </div>
        <div>
          <small>{t("recovery.protected")}</small>
          <b data-testid={testIds.recoveryProtected}>
            {proposal.protected_commitments_preserved ? t("recovery.protectedYes") : t("recovery.protectedNo")}
          </b>
        </div>
      </div>
      <div className="recovery__diff">
        <p>
          <b>{t("recovery.removed")}</b>: {pick(PULSE_I18N.recoveryRemoved, locale)}
        </p>
        <p>
          <b>{t("recovery.added")}</b>: {pick(PULSE_I18N.recoveryAdded, locale)}
        </p>
      </div>
      <details className="technical">
        <summary>{t("recovery.evidence")}</summary>
        <dl>
          <div>
            <dt>route_provenance</dt>
            <dd>{proposal.verified_evidence.route_provenance}</dd>
          </div>
          <div>
            <dt>source_provider</dt>
            <dd>{proposal.verified_evidence.source_provider}</dd>
          </div>
          <div>
            <dt>snapshot_id</dt>
            <dd>{proposal.verified_evidence.snapshot_id}</dd>
          </div>
          <div>
            <dt>{t("recovery.source")}</dt>
            <dd>RECORDED_FIXTURE · {t("recovery.simulation")}</dd>
          </div>
        </dl>
        <p>{pick(PULSE_I18N.recoveryExplanation, locale)}</p>
      </details>
      <div className="recovery__actions">
        <button
          type="button"
          className="btn btn--primary"
          onClick={() => {
            setAccepted(true);
            setRejected(false);
          }}
        >
          {t("recovery.accept")}
        </button>
        <button
          type="button"
          className="btn"
          onClick={() => {
            setRejected(true);
            setAccepted(false);
          }}
        >
          {t("recovery.reject")}
        </button>
      </div>
      {(accepted || rejected) && (
        <p className="fixture-banner" role="status">
          {accepted ? t("recovery.accepted") : t("recovery.rejected")} · RECORDED_FIXTURE reference only.
        </p>
      )}
    </section>
  );
}
