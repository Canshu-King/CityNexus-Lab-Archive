import { useId } from "react";
import type { TravelerCapability } from "../types";
import { capabilityCopy } from "../copy";
import { EvidenceBadge } from "./EvidenceBadge";
import { capabilityDescription, capabilityKindLabel, capabilityLabel, scopeLabel } from "../evidence";
import "../styles/capability-experience.css";

function CapabilityRow({ capability, locale }: { capability: TravelerCapability; locale: "zh-CN" | "en" }) {
  const copy = capabilityCopy(locale);
  const isHard = capability.strength === "HARD" || capability.kind === "HARD_ACCESSIBILITY_NEED";
  const description = capabilityDescription(capability, locale);
  return (
    <li className="cne-twin-row" data-testid={`twin-capability-${capability.id}`} data-capability-kind={capability.kind}>
      <div className="cne-twin-row__head">
        <div>
          <b>{capabilityLabel(capability, locale)}</b>
          <small>{capabilityKindLabel(capability.kind, copy)}</small>
        </div>
        <EvidenceBadge state={capability.evidence.state} evidence={capability.evidence} locale={locale} />
      </div>
      {description ? <p>{description}</p> : null}
      <dl className="cne-facts">
        <div><dt>{copy.twin.active}</dt><dd>{capability.active ? "✓" : "—"}</dd></div>
        <div><dt>{copy.twin.scope}</dt><dd>{scopeLabel(capability.scope, copy)}</dd></div>
        <div><dt>{copy.twin.evidence}</dt><dd>{capability.evidence.state}</dd></div>
      </dl>
      {isHard ? <p className="cne-hard-fact">{copy.twin.travelerStated} · {copy.twin.explicit} · {copy.twin.active}</p> : null}
      {capability.learned ? (
        <div className="cne-learned-meter">
          <p><b>{copy.twin.learnedStrength}</b> {capability.strengthScore ?? "—"} · <b>{copy.twin.confidence}</b> {capability.confidence ?? "—"} · <b>{copy.twin.evidenceCount}</b> {capability.evidenceCount ?? "—"}</p>
          {typeof capability.confidence === "number" ? (
            <div
              role="meter"
              aria-label={`${capabilityLabel(capability, locale)} ${copy.twin.confidence}`}
              aria-valuemin={0}
              aria-valuemax={1}
              aria-valuenow={capability.confidence}
              className="cne-meter"
            >
              <span style={{ width: `${Math.max(0, Math.min(1, capability.confidence)) * 100}%` }} />
            </div>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}

export function TwinCapabilitySummary({ capabilities, locale = "zh-CN" }: { capabilities: TravelerCapability[]; locale?: "zh-CN" | "en" }) {
  const copy = capabilityCopy(locale);
  const titleId = useId();
  const hard = capabilities.filter((item) => item.strength === "HARD" || item.kind === "HARD_ACCESSIBILITY_NEED");
  const explicitCapabilities = capabilities.filter((item) => !item.learned && item.kind !== "SOFT_PREFERENCE" && !hard.includes(item));
  const explicitPreferences = capabilities.filter((item) => !item.learned && item.kind === "SOFT_PREFERENCE");
  const learned = capabilities.filter((item) => item.learned);
  return (
    <section className="cne-twin" aria-labelledby={titleId} data-testid="twin-capability-summary">
      <header className="cne-surface__head">
        <div><span className="cne-kicker">TRAVELER_TWIN</span><h2 id={titleId}>{copy.twin.title}</h2><p>{copy.twin.authorityNotice}</p></div>
      </header>

      {hard.length ? (
        <section className="cne-twin__group cne-twin__group--hard" aria-label={copy.twin.hardAccessibility}>
          <h3>{copy.twin.hardAccessibility}</h3>
          <ul>{hard.map((capability) => <CapabilityRow key={capability.id} capability={capability} locale={locale} />)}</ul>
        </section>
      ) : null}

      <section className="cne-twin__group" aria-label={copy.twin.explicitCapability}>
        <h3>{copy.twin.explicitCapability}</h3>
        {explicitCapabilities.length ? <ul>{explicitCapabilities.map((capability) => <CapabilityRow key={capability.id} capability={capability} locale={locale} />)}</ul> : <p className="cne-help">{copy.twin.noExplicit}</p>}
      </section>

      <section className="cne-twin__group" aria-label={copy.twin.explicitPreference}>
        <h3>{copy.twin.explicitPreference}</h3>
        {explicitPreferences.length ? <ul>{explicitPreferences.map((capability) => <CapabilityRow key={capability.id} capability={capability} locale={locale} />)}</ul> : <p className="cne-help">{copy.twin.noExplicit}</p>}
      </section>

      <section className="cne-twin__group cne-twin__group--learned" aria-label={copy.twin.learnedSoft}>
        <h3>{copy.twin.learnedSoft}</h3>
        {learned.length ? <ul>{learned.map((capability) => <CapabilityRow key={capability.id} capability={capability} locale={locale} />)}</ul> : <p className="cne-help">{copy.twin.noLearned}</p>}
      </section>

      <p className="cne-rule" data-testid="twin-unknown-rule">{copy.evidence.unknownIsNotAccessible}</p>
    </section>
  );
}