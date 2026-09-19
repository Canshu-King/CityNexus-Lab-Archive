import type { CapabilityEvidence, CapabilityEvidenceState } from "../types";
import { evidenceVisual, provenanceKindLabel } from "../evidence";
import { capabilityCopy } from "../copy";
import "../styles/capability-experience.css";

export interface EvidenceBadgeProps {
  state: CapabilityEvidenceState;
  evidence?: CapabilityEvidence;
  locale?: "zh-CN" | "en";
  showProvenance?: boolean;
  className?: string;
  testId?: string;
}

export function EvidenceBadge({
  state,
  evidence,
  locale = "zh-CN",
  showProvenance = false,
  className = "",
  testId,
}: EvidenceBadgeProps) {
  const copy = capabilityCopy(locale);
  const visual = evidenceVisual(state, copy);
  const label = evidence ? `${visual.label}: ${evidence.summary}` : visual.label;
  return (
    <span className={`cne-evidence cne-evidence--${visual.tone} ${className}`.trim()} data-evidence-state={state} data-testid={testId ?? `evidence-${state.toLowerCase()}`} aria-label={label}>
      <span className="cne-evidence__glyph" aria-hidden="true">{visual.glyph}</span>
      <span className="cne-evidence__label">{visual.label}</span>
      {showProvenance && evidence ? (
        <span className="cne-evidence__provenance" title={evidence.provenance.notes ?? evidence.summary}>
          {provenanceKindLabel(evidence.provenance.kind, copy)}
        </span>
      ) : null}
    </span>
  );
}

export function EvidenceSummary({ evidence, locale = "zh-CN" }: { evidence: CapabilityEvidence; locale?: "zh-CN" | "en" }) {
  const copy = capabilityCopy(locale);
  return (
    <div className="cne-evidence-summary">
      <EvidenceBadge state={evidence.state} evidence={evidence} locale={locale} showProvenance />
      <p>{evidence.summary}</p>
      {evidence.liveChecks?.length ? (
        <ul className="cne-evidence-summary__checks">
          {evidence.liveChecks.map((check) => <li key={check}>{check}</li>)}
        </ul>
      ) : null}
      {evidence.detail ? <p className="cne-evidence-summary__detail">{evidence.detail}</p> : null}
      {evidence.state !== "VERIFIED" ? <p className="cne-evidence-summary__rule">{copy.evidence.unknownIsNotAccessible}</p> : null}
    </div>
  );
}