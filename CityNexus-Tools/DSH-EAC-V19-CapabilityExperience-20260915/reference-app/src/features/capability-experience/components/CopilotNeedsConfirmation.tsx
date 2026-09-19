import { useId, useState, type ChangeEvent } from "react";
import type { CapabilityConfirmation, CapabilityConfirmationDecision, CapabilityScope, CapabilityStrength, TravelerCapability } from "../types";
import { CAPABILITY_SCOPES, CAPABILITY_STRENGTHS } from "../types";
import { capabilityCopy } from "../copy";
import { EvidenceBadge, EvidenceSummary } from "./EvidenceBadge";
import { capabilityKindLabel, capabilityLabel, scopeLabel, strengthLabel } from "../evidence";
import "../styles/capability-experience.css";

export interface CopilotNeedsConfirmationProps {
  confirmations: CapabilityConfirmation[];
  statement?: string;
  locale?: "zh-CN" | "en";
  surface?: "card" | "sheet";
  onDecision?: (decision: CapabilityConfirmationDecision) => void;
  onDismiss?: () => void;
}

function applyOption(confirmation: CapabilityConfirmation): CapabilityConfirmation {
  if (!confirmation.selectedOptionId || !confirmation.ambiguityOptions) return confirmation;
  const option = confirmation.ambiguityOptions.find((item) => item.id === confirmation.selectedOptionId);
  if (!option) return confirmation;
  return {
    ...confirmation,
    ambiguous: false,
    capability: { ...confirmation.capability, ...option.capabilityPatch, confirmed: false },
  };
}

function editableCapability(confirmation: CapabilityConfirmation): TravelerCapability {
  return applyOption(confirmation).capability;
}

export function CopilotNeedsConfirmation({
  confirmations,
  statement,
  locale = "zh-CN",
  surface = "card",
  onDecision,
  onDismiss,
}: CopilotNeedsConfirmationProps) {
  const copy = capabilityCopy(locale);
  const [drafts, setDrafts] = useState<CapabilityConfirmation[]>(confirmations);
  const [editing, setEditing] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);
  const [status, setStatus] = useState("");
  const titleId = useId();
  const warningId = useId();

  const effective = drafts.map(applyOption);
  const unresolvedAmbiguity = effective.some((item) => item.ambiguous);
  const hardFuturePersistence = effective.some((item) => item.capability.strength === "HARD" && item.capability.scope !== "THIS_JOURNEY");
  const confirmBlocked = unresolvedAmbiguity || (hardFuturePersistence && !acknowledged) || effective.length === 0;

  const updateCapability = (id: string, patch: Partial<TravelerCapability>) => {
    setDrafts((current) => current.map((item) => item.id === id ? { ...item, capability: { ...item.capability, ...patch } } : item));
  };
  const selectOption = (id: string, optionId: string) => {
    setDrafts((current) => current.map((item) => item.id === id ? { ...item, selectedOptionId: optionId, ambiguous: false } : item));
  };
  const decide = (action: CapabilityConfirmationDecision["action"], override?: CapabilityConfirmation[]) => {
    const source = override ?? effective;
    const capabilities = source.map((item) =>
      action === "JOURNEY_ONLY" ? { ...item.capability, scope: "THIS_JOURNEY" as const } : item.capability,
    );
    if (action === "CONFIRM" && confirmBlocked) return;
    onDecision?.({ id: capabilities.map((item) => item.id).join(","), action, capabilities, acknowledgedFuturePersistence: acknowledged });
    if (action === "CONFIRM") setStatus(copy.confirmation.confirmed);
    if (action === "JOURNEY_ONLY") setStatus(copy.confirmation.journeyOnlyConfirmed);
    if (action === "DISMISS") setStatus(copy.confirmation.dismissed);
  };
  const dismiss = () => {
    setStatus(copy.confirmation.dismissed);
    onDismiss?.();
    onDecision?.({ id: "dismiss", action: "DISMISS", capabilities: [] });
  };

  return (
    <section
      className={`cne-confirmation cne-confirmation--${surface}`}
      role={surface === "sheet" ? "dialog" : "region"}
      aria-modal={surface === "sheet" ? true : undefined}
      aria-labelledby={titleId}
      data-testid={surface === "sheet" ? "copilot-needs-sheet" : "copilot-needs-confirmation"}
    >
      <header className="cne-surface__head">
        <div>
          <span className="cne-kicker">{copy.confirmation.detected}</span>
          <h2 id={titleId}>{surface === "sheet" ? copy.confirmation.sheetTitle : copy.confirmation.title}</h2>
          {statement ? <blockquote className="cne-quote">{statement}</blockquote> : null}
        </div>
        <span className="cne-source-pill">{copy.confirmation.sourceValue}</span>
      </header>

      <ul className="cne-confirmation__list">
        {effective.map((item, index) => {
          const capability = item.capability;
          return (
            <li key={item.id} className="cne-confirmation__item" data-testid={`detected-need-${index}`}>
              <div className="cne-confirmation__item-main">
                <div>
                  <strong>{capabilityLabel(capability, locale)}</strong>
                  <p className="cne-help">{copy.confirmation.classLabel}: {strengthLabel(capability.strength, copy)} · {copy.confirmation.scopeLabel}: {scopeLabel(capability.scope, copy)} · {capabilityKindLabel(capability.kind, copy)}</p>
                </div>
                <EvidenceBadge state={capability.evidence.state} evidence={capability.evidence} locale={locale} />
              </div>

              {item.ambiguous ? (
                <fieldset className="cne-ambiguity" data-testid={`detected-ambiguity-${index}`}>
                  <legend>{copy.confirmation.ambiguity}</legend>
                  {item.ambiguityPrompt ? <p>{item.ambiguityPrompt}</p> : null}
                  {item.ambiguityOptions?.map((option) => (
                    <label key={option.id} className="cne-choice">
                      <input
                        type="radio"
                        name={`ambiguity-${item.id}`}
                        value={option.id}
                        checked={item.selectedOptionId === option.id}
                        onChange={() => selectOption(item.id, option.id)}
                      />
                      <span><b>{option.label}</b>{option.description ? <small>{option.description}</small> : null}</span>
                    </label>
                  ))}
                </fieldset>
              ) : null}

              {editing ? (
                <div className="cne-confirmation__edit">
                  <label>
                    {copy.confirmation.classLabel}
                    <select
                      value={capability.strength}
                      onChange={(event: ChangeEvent<HTMLElement>) => updateCapability(item.id, { strength: event.target.value as CapabilityStrength })}
                      data-testid={`detected-strength-${index}`}
                    >
                      {CAPABILITY_STRENGTHS.filter((value) => value !== "AMBIGUOUS").map((value) => (
                        <option key={value} value={value}>{strengthLabel(value, copy)}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    {copy.confirmation.scopeLabel}
                    <select
                      value={capability.scope}
                      onChange={(event: ChangeEvent<HTMLElement>) => updateCapability(item.id, { scope: event.target.value as CapabilityScope })}
                      data-testid={`detected-scope-${index}`}
                    >
                      {CAPABILITY_SCOPES.map((value) => (
                        <option key={value} value={value}>{scopeLabel(value, copy)}</option>
                      ))}
                    </select>
                  </label>
                </div>
              ) : null}
              <EvidenceSummary evidence={capability.evidence} locale={locale} />
            </li>
          );
        })}
      </ul>

      {hardFuturePersistence ? (
        <div className="cne-hard-warning" id={warningId}>
          <strong>{copy.confirmation.hardPersistenceWarning}</strong>
          <label className="cne-check">
            <input
              type="checkbox"
              checked={acknowledged}
              onChange={(event: ChangeEvent<HTMLElement>) => setAcknowledged(event.target.checked)}
              data-testid="hard-persistence-ack"
            />
            <span>{copy.confirmation.hardPersistenceAcknowledge}</span>
          </label>
        </div>
      ) : null}

      {unresolvedAmbiguity ? <p className="cne-blocked-note" role="status">{copy.confirmation.ambiguity}</p> : null}
      {status ? <p className="cne-status" role="status" aria-live="polite" data-testid="copilot-status">{status}</p> : null}

      <footer className="cne-surface__actions cne-surface__actions--wrap">
        <button type="button" className="cne-button cne-button--primary" disabled={confirmBlocked} onClick={() => decide("CONFIRM")} data-testid="copilot-confirm">
          {copy.confirmation.actions.confirm}
        </button>
        <button type="button" className="cne-button cne-button--secondary" onClick={() => setEditing((value) => !value)} data-testid="copilot-edit">
          {editing ? copy.confirmation.actions.saveEdit : copy.confirmation.actions.edit}
        </button>
        <button
          type="button"
          className="cne-button cne-button--secondary"
          onClick={() => {
            const journeyOnly = effective.map((item) => ({ ...item, capability: { ...item.capability, scope: "THIS_JOURNEY" as const } }));
            setDrafts(journeyOnly);
            decide("JOURNEY_ONLY", journeyOnly);
          }}
          data-testid="copilot-journey-only"
        >
          {copy.confirmation.actions.journeyOnly}
        </button>
        <button type="button" className="cne-button cne-button--ghost" onClick={dismiss} data-testid="copilot-dismiss">
          {copy.confirmation.actions.dismiss}
        </button>
      </footer>
    </section>
  );
}