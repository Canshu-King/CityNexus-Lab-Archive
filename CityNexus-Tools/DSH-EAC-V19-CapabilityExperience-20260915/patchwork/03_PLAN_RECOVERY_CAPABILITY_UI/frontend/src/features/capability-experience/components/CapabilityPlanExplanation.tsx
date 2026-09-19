import { useId } from "react";
import type { CapabilityImpact, PlanCapabilityExplanationModel } from "../types";
import { capabilityCopy } from "../copy";
import { EvidenceBadge, EvidenceSummary } from "./EvidenceBadge";
import { capabilityKindLabel, impactStatusLabel } from "../evidence";
import "../styles/capability-experience.css";

function ImpactRow({ impact, locale }: { impact: CapabilityImpact; locale: "zh-CN" | "en" }) {
  const copy = capabilityCopy(locale);
  return (
    <li className="cne-impact" data-testid={`impact-${impact.id}`} data-impact-status={impact.status}>
      <div className="cne-impact__head">
        <span className="cne-impact__status">{impactStatusLabel(impact.status, copy)}</span>
        <span className="cne-impact__kind">{capabilityKindLabel(impact.kind, copy)}</span>
        <EvidenceBadge state={impact.evidence.state} evidence={impact.evidence} locale={locale} />
      </div>
      <p>{impact.explanation}</p>
      {(impact.observedValue || impact.limitValue) ? (
        <dl className="cne-impact__values">
          {impact.observedValue ? <div><dt>Observed</dt><dd>{impact.observedValue}</dd></div> : null}
          {impact.limitValue ? <div><dt>{copy.plan.hardLimit}</dt><dd>{impact.limitValue}</dd></div> : null}
        </dl>
      ) : null}
      {impact.candidateLabel ? <small>{impact.candidateLabel}</small> : null}
    </li>
  );
}

export function CapabilityPlanExplanation({ model, locale = "zh-CN" }: { model: PlanCapabilityExplanationModel; locale?: "zh-CN" | "en" }) {
  const copy = capabilityCopy(locale);
  const titleId = useId();
  return (
    <section className="cne-plan" aria-labelledby={titleId} data-testid="capability-plan-explanation">
      <header className="cne-surface__head">
        <div>
          <span className="cne-kicker">{model.authority === "BACKEND_PLANNING" ? "BACKEND_PLANNING" : "RECORDED_FIXTURE_REFERENCE"}</span>
          <h2 id={titleId}>{copy.plan.title}</h2>
          <p><strong>{model.candidateLabel}</strong>{model.candidateSubtitle ? ` · ${model.candidateSubtitle}` : ""}</p>
        </div>
        <span className={`cne-plan__selected ${model.selected ? "is-selected" : ""}`}>{model.selected ? "SELECTED" : "CANDIDATE"}</span>
      </header>

      <section className="cne-plan__block" aria-labelledby={`${titleId}-why`}>
        <h3 id={`${titleId}-why`}>{copy.plan.whySelected}</h3>
        {model.why.length ? <ul className="cne-impact-list">{model.why.map((impact) => <ImpactRow key={impact.id} impact={impact} locale={locale} />)}</ul> : <p className="cne-help">—</p>}
      </section>

      <section className="cne-plan__block" aria-labelledby={`${titleId}-rejected`}>
        <h3 id={`${titleId}-rejected`}>{copy.plan.rejected}</h3>
        {model.rejected.length ? (
          <ul className="cne-impact-list">{model.rejected.map((impact) => <ImpactRow key={impact.id} impact={impact} locale={locale} />)}</ul>
        ) : <p className="cne-help">{copy.plan.noRejections}</p>}
      </section>

      <section className="cne-plan__block" aria-labelledby={`${titleId}-unknown`}>
        <h3 id={`${titleId}-unknown`}>{copy.plan.unknown}</h3>
        {model.unknown.length ? (
          <ul className="cne-unknown-list">
            {model.unknown.map((evidence, index) => (
              <li key={`${evidence.provenance.sourceSystem}-${index}`}><EvidenceSummary evidence={evidence} locale={locale} /></li>
            ))}
          </ul>
        ) : <p className="cne-help">{copy.plan.noUnknowns}</p>}
        <p className="cne-rule" data-testid="unknown-rule">{copy.evidence.unknownIsNotAccessible}</p>
      </section>

      {model.protectedCommitments.length ? (
        <section className="cne-c4" data-testid="protected-commitments">
          <h3>{copy.plan.protectedCommitments}</h3>
          <ul>
            {model.protectedCommitments.map((commitment) => (
              <li key={commitment.id}>
                <span aria-hidden="true" className="cne-c4__glyph">C4</span>
                <span>
                  <b>{commitment.label}</b>
                  <small>{commitment.level} · {commitment.preserved ? copy.plan.commitmentPreserved : copy.plan.commitmentAtRisk}</small>
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </section>
  );
}