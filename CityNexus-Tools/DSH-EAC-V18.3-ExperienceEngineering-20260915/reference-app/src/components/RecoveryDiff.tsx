import { useLocale, useT } from "../i18n";
import { testIds } from "../testids";
import type { ApprovalState, JourneyActivity, RecoveryProposal } from "../types";
import { pick } from "../experience/locale";
import { RuntimeTruthBadge } from "./RuntimeTruthBadge";

function ActivityRow({ activity, changed = false }: { activity: JourneyActivity; changed?: boolean; key?: string }) {
  const t = useT();
  return (
    <li className={`${activity.protected ? "protected" : ""}${changed ? " changed" : ""}`}>
      <time>{activity.start_at.slice(11, 16)}</time>
      <div>
        <b>{activity.title}</b>
        <small>
          {t(`environment.${activity.environment}`)} · {activity.walking_min} {t("recovery.walking")} · {activity.place}
        </small>
      </div>
      {activity.protected && <em>C4</em>}
      {changed && <em className="changed-tag">CHANGED</em>}
    </li>
  );
}

export function RecoveryDiff({
  proposal,
  approvalState,
  submitting = false,
  offline = false,
  lastUpdated,
  onDecision,
}: {
  proposal: RecoveryProposal;
  approvalState: ApprovalState;
  submitting?: boolean;
  offline?: boolean;
  lastUpdated?: string | null;
  onDecision?: (decision: "approve" | "reject" | "review_requested") => void;
}) {
  const t = useT();
  const { locale } = useLocale();
  const money = (minor: number) => (minor === 0 ? "¥0" : `${minor > 0 ? "+" : "−"}¥${(Math.abs(minor) / 100).toFixed(2)}`);
  const signed = (value: number, suffix = " min") => `${value > 0 ? "+" : ""}${value}${suffix}`;

  return (
    <section
      className="recovery"
      data-testid={testIds.recoveryDiff}
      data-evidence-state={proposal.evidence_state}
      data-approval-state={approvalState}
    >
      <header className="recovery__head">
        <div>
          <span className="kicker">{t("recovery.kicker")}</span>
          <h2>{t("recovery.title")}</h2>
          <p className="muted">{pick(proposal.trigger, locale)}</p>
          {lastUpdated && <p className="muted small">last updated {lastUpdated}</p>}
        </div>
        <RuntimeTruthBadge
          truth={{
            semantic: "DeepSeek",
            execution: offline ? "UNAVAILABLE" : "DIRECT",
            truth: "CityNexus",
            source: proposal.source,
            status: offline ? "offline_stale" : "ready",
          }}
          compact
        />
      </header>
      <div className="recovery__grid">
        <article className="recovery-col before" data-testid={testIds.recoveryBefore}>
          <h3>{t("recovery.before")}</h3>
          <ol>{proposal.before.map((activity) => <ActivityRow key={activity.id} activity={activity} />)}</ol>
        </article>
        <article className="recovery-col after" data-testid={testIds.recoveryAfter}>
          <h3>{t("recovery.after")}</h3>
          <ol>
            {proposal.after.map((activity) => (
              <ActivityRow key={activity.id} activity={activity} changed={activity.status === "candidate"} />
            ))}
          </ol>
        </article>
      </div>
      <div className="recovery__block">
        <h3>{t("recovery.why")}</h3>
        <ul className="recovery__why" data-testid="recovery-why">
          {proposal.why.map((reason) => <li key={reason.en}>{pick(reason, locale)}</li>)}
        </ul>
      </div>
      <div className="recovery__block protected-block">
        <h3>{t("recovery.protectedList")}</h3>
        <ul className="recovery__protected" data-testid="recovery-protected-list">
          {proposal.protected_commitments.map((commitment) => <li key={commitment.en}>✓ {pick(commitment, locale)}</li>)}
        </ul>
      </div>
      <div className="recovery__metrics">
        <div>
          <small>{t("recovery.timeDelta")}</small>
          <b data-testid="recovery-time-delta">{signed(proposal.time_delta_min)}</b>
        </div>
        <div>
          <small>{t("recovery.costDelta")}</small>
          <b data-testid={testIds.recoveryCostDelta}>{money(proposal.cost_delta_minor)}</b>
        </div>
        <div>
          <small>{t("recovery.walkingDelta")}</small>
          <b data-testid="recovery-walking-delta">{signed(proposal.walking_delta_min)}</b>
        </div>
        <div>
          <small>{t("recovery.travelDelta")}</small>
          <b data-testid="recovery-travel-delta">{signed(proposal.travel_delta_min)}</b>
        </div>
      </div>
      <div className="recovery__evidence" data-evidence-state={proposal.evidence_state}>
        <b>{t(`recovery.evidence.${proposal.evidence_state}`)}</b>
      </div>
      <div
        className="approval-panel recovery-approval"
        data-testid="recovery-approval"
        data-approval-state={approvalState}
        role="group"
        aria-label={t("approval.title")}
      >
        <div>
          <b>{t("approval.title")}</b>
          <p>{t("approval.impact")}</p>
          {offline && <p className="muted small">OFFLINE: destructive approval is disabled until authoritative truth returns.</p>}
        </div>
        <div className="approval-actions">
          <button
            type="button"
            className="btn btn--approve"
            data-testid="recovery-approve"
            disabled={submitting || offline || proposal.evidence_state !== "verified"}
            onClick={() => onDecision?.("approve")}
          >
            {submitting ? "Submitting…" : t("recovery.accept")}
          </button>
          <button
            type="button"
            className="btn btn--reject"
            data-testid="recovery-reject"
            disabled={submitting || offline}
            onClick={() => onDecision?.("reject")}
          >
            {t("recovery.reject")}
          </button>
          <button
            type="button"
            className="btn"
            data-testid="recovery-review"
            disabled={submitting || offline}
            onClick={() => onDecision?.("review_requested")}
          >
            {t("approval.review")}
          </button>
        </div>
        <p className="muted small" data-testid="recovery-approval-state">
          {t(`approval.state.${approvalState === "submitting" ? "proposal_only" : approvalState}`)} · {t("approval.authority")}
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
            <dd>{proposal.source} · {t("recovery.simulation")}</dd>
          </div>
        </dl>
        <p>{pick(proposal.explanation, locale)}</p>
      </details>
    </section>
  );
}
