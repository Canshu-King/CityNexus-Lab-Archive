import { useId } from "react";
import type { CapabilityImpact, RecoveryCapabilityDiffModel } from "../types";
import { capabilityCopy } from "../copy";
import { EvidenceBadge, EvidenceSummary } from "./EvidenceBadge";
import { capabilityKindLabel, impactStatusLabel } from "../evidence";
import "../styles/capability-experience.css";

function DiffRow({ impact, locale }: { impact: CapabilityImpact; locale: "zh-CN" | "en" }) {
  const copy = capabilityCopy(locale);
  return (
    <li className="cne-diff-row" data-testid={`diff-${impact.id}`} data-impact-status={impact.status}>
      <span className="status-dot" aria-hidden="true" />
      <div>
        <div className="cne-diff-row__head">
          <b>{impact.capabilityLabel}</b>
          <span>{impactStatusLabel(impact.status, copy)}</span>
        </div>
        <p>{impact.explanation}</p>
        <small>{capabilityKindLabel(impact.kind, copy)}</small>
        <EvidenceBadge state={impact.evidence.state} evidence={impact.evidence} locale={locale} />
      </div>
    </li>
  );
}

export function RecoveryDiffCapability({ model, locale = "zh-CN" }: { model: RecoveryCapabilityDiffModel; locale?: "zh-CN" | "en" }) {
  const copy = capabilityCopy(locale);
  const titleId = useId();
  return (
    <section className="cne-recovery" aria-labelledby={titleId} data-testid="recovery-capability-diff">
      <header className="cne-surface__head">
        <div>
          <span className="cne-kicker">{model.authority === "BACKEND_PLANNING" ? "BACKEND_PLANNING" : "RECORDED_FIXTURE_REFERENCE"}</span>
          <h2 id={titleId}>{copy.recovery.title}</h2>
          <p>{model.journeyId}</p>
        </div>
      </header>

      <div className="cne-recovery__columns">
        <section aria-labelledby={`${titleId}-before`}>
          <h3 id={`${titleId}-before`}>{copy.recovery.before}</h3>
          <ul className="cne-diff-list">{model.before.map((impact) => <DiffRow key={impact.id} impact={impact} locale={locale} />)}</ul>
        </section>
        <section aria-labelledby={`${titleId}-after`}>
          <h3 id={`${titleId}-after`}>{copy.recovery.after}</h3>
          <ul className="cne-diff-list">{model.after.map((impact) => <DiffRow key={impact.id} impact={impact} locale={locale} />)}</ul>
        </section>
      </div>

      <section className="cne-recovery__block cne-recovery__block--good" aria-labelledby={`${titleId}-preserved`}>
        <h3 id={`${titleId}-preserved`}>{copy.recovery.preserved}</h3>
        <ul className="cne-diff-list">{model.preserved.map((impact) => <DiffRow key={impact.id} impact={impact} locale={locale} />)}</ul>
      </section>

      <section className="cne-recovery__block cne-recovery__block--risk" aria-labelledby={`${titleId}-risk`}>
        <h3 id={`${titleId}-risk`}>{copy.recovery.atRisk}</h3>
        {model.atRisk.length ? <ul className="cne-diff-list">{model.atRisk.map((impact) => <DiffRow key={impact.id} impact={impact} locale={locale} />)}</ul> : <p className="cne-help">{copy.recovery.noAtRisk}</p>}
      </section>

      <section className="cne-recovery__block" aria-labelledby={`${titleId}-gaps`}>
        <h3 id={`${titleId}-gaps`}>{copy.recovery.evidenceGaps}</h3>
        {model.evidenceGaps.length ? <ul className="cne-unknown-list">{model.evidenceGaps.map((evidence, index) => <li key={`${evidence.provenance.sourceSystem}-${index}`}><EvidenceSummary evidence={evidence} locale={locale} /></li>)}</ul> : <p className="cne-help">{copy.recovery.noGaps}</p>}
      </section>

      {model.protectedCommitments.length ? (
        <section className="cne-c4" data-testid="recovery-protected-commitments">
          <h3>{copy.plan.protectedCommitments}</h3>
          <ul>
            {model.protectedCommitments.map((commitment) => (
              <li key={commitment.id}><span aria-hidden="true" className="cne-c4__glyph">C4</span><span><b>{commitment.label}</b><small>{commitment.level} · {commitment.preserved ? copy.plan.commitmentPreserved : copy.plan.commitmentAtRisk}</small></span></li>
            ))}
          </ul>
        </section>
      ) : null}
    </section>
  );
}