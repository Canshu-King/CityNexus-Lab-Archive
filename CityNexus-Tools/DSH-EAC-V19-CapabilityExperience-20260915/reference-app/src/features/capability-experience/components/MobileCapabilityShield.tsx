import { useId } from "react";
import type { MobileCapabilityShieldModel } from "../types";
import { capabilityCopy, fillCount } from "../copy";
import { EvidenceBadge } from "./EvidenceBadge";
import { capabilityLabel } from "../evidence";
import "../styles/capability-experience.css";

export function MobileCapabilityShield({ model, locale = "zh-CN", onPrimaryAction }: { model: MobileCapabilityShieldModel; locale?: "zh-CN" | "en"; onPrimaryAction?: () => void }) {
  const copy = capabilityCopy(locale);
  const titleId = useId();
  const hasProtected = model.protectedCount > 0;
  return (
    <section className="cne-mobile-shield" aria-labelledby={titleId} data-testid="mobile-capability-shield">
      <header className="cne-mobile-shield__head">
        <div>
          <span className="cne-kicker">{copy.mobile.protectedTitle}</span>
          <h2 id={titleId}>
            {hasProtected ? fillCount(copy.mobile.protectedCount, model.protectedCount) : copy.mobile.noNeeds}
          </h2>
        </div>
        <span className="cne-mobile-shield__badge" aria-hidden="true">{hasProtected ? model.protectedCount : "—"}</span>
      </header>

      {hasProtected ? (
        <ul className="cne-mobile-shield__needs">
          {model.needs.slice(0, 3).map((capability) => (
            <li key={capability.id}>
              <span className="status-dot" aria-hidden="true" />
              <span>{capabilityLabel(capability, locale)}</span>
            </li>
          ))}
        </ul>
      ) : null}

      {model.evidenceGap ? (
        <div className="cne-mobile-shield__gap" data-testid="mobile-evidence-gap">
          <EvidenceBadge state={model.evidenceGap.evidence.state} evidence={model.evidenceGap.evidence} locale={locale} />
          <strong>{model.evidenceGap.label}</strong>
          <p>{copy.mobile.evidenceGapNotVerified}</p>
        </div>
      ) : null}

      <button type="button" className="cne-button cne-button--primary cne-mobile-shield__action" onClick={onPrimaryAction} data-testid="mobile-shield-action">
        {model.primaryActionLabel || copy.mobile.primaryAction}
      </button>
    </section>
  );
}