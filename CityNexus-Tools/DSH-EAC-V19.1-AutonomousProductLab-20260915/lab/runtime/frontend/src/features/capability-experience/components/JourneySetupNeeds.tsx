import { useId, useState, type ChangeEvent } from "react";
import type { JourneySetupNeedsDraft, QuickNeedId, TravelerCapability } from "../types";
import { QUICK_NEEDS } from "../types";
import { capabilityCopy } from "../copy";
import { draftToCapabilities } from "../adapter";
import { EvidenceBadge } from "./EvidenceBadge";
import { makeUiOnlyEvidence } from "../evidence";
import "../styles/capability-experience.css";

export const EMPTY_JOURNEY_SETUP_NEEDS: JourneySetupNeedsDraft = {
  quickNeedIds: [],
  advanced: {},
  note: "",
};

export interface JourneySetupNeedsProps {
  value: JourneySetupNeedsDraft;
  onChange: (next: JourneySetupNeedsDraft) => void;
  locale?: "zh-CN" | "en";
  onSave?: (capabilities: TravelerCapability[]) => void;
  disabled?: boolean;
  showSourceNotice?: boolean;
}

export function JourneySetupNeeds({
  value,
  onChange,
  locale = "zh-CN",
  onSave,
  disabled = false,
  showSourceNotice = true,
}: JourneySetupNeedsProps) {
  const copy = capabilityCopy(locale);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const advancedId = useId();
  const quickNeedIds = new Set(value.quickNeedIds);
  const capabilities = draftToCapabilities(value, locale);

  const update = <K extends keyof JourneySetupNeedsDraft>(key: K, next: JourneySetupNeedsDraft[K]) => {
    onChange({ ...value, [key]: next });
  };
  const updateAdvanced = <K extends keyof JourneySetupNeedsDraft["advanced"]>(key: K, next: JourneySetupNeedsDraft["advanced"][K]) => {
    onChange({ ...value, advanced: { ...value.advanced, [key]: next } });
  };
  const toggleQuick = (id: QuickNeedId) => {
    const nextIds = quickNeedIds.has(id) ? value.quickNeedIds.filter((item) => item !== id) : [...value.quickNeedIds, id];
    update("quickNeedIds", nextIds);
  };

  return (
    <section className="cne-setup" aria-labelledby="cne-setup-title" data-testid="journey-setup-needs">
      <header className="cne-surface__head">
        <div>
          <span className="cne-kicker">{copy.journeySetup.optional}</span>
          <h2 id="cne-setup-title">{copy.journeySetup.title}</h2>
          <p>{copy.journeySetup.lede}</p>
        </div>
        <EvidenceBadge
          state="NEEDS_LIVE_EVIDENCE"
          evidence={makeUiOnlyEvidence(copy.journeySetup.sourceNotice)}
          locale={locale}
          showProvenance
          testId="journey-setup-source"
        />
      </header>

      <fieldset className="cne-setup__group" disabled={disabled}>
        <legend>{copy.journeySetup.quickTitle}</legend>
        <p className="cne-help" id="cne-quick-help">{copy.journeySetup.quickHelp}</p>
        <div className="cne-chiplist" role="group" aria-describedby="cne-quick-help">
          {QUICK_NEEDS.map((need) => {
            const selected = quickNeedIds.has(need.id);
            return (
              <button
                key={need.id}
                type="button"
                className={`cne-chip ${selected ? "is-selected" : ""}`}
                role="checkbox"
                aria-checked={selected}
                data-testid={`setup-quick-${need.id}`}
                onClick={() => toggleQuick(need.id)}
              >
                <span className="cne-chip__mark" aria-hidden="true">{selected ? "✓" : "+"}</span>
                <span>{locale === "zh-CN" ? need.labelZh : need.labelEn}</span>
              </button>
            );
          })}
        </div>
      </fieldset>

      <div className="cne-setup__advanced">
        <button
          type="button"
          className="cne-disclosure"
          aria-expanded={advancedOpen}
          aria-controls={advancedId}
          onClick={() => setAdvancedOpen((open) => !open)}
        >
          <span aria-hidden="true" className={`cne-disclosure__arrow ${advancedOpen ? "is-open" : ""}`}>▸</span>
          {copy.journeySetup.advancedToggle}
        </button>
        {advancedOpen ? (
          <div id={advancedId} className="cne-setup__advanced-grid">
            <p className="cne-help cne-grid-full">{copy.journeySetup.advancedHelp}</p>
            <label>
              {copy.journeySetup.maxWalkingPerLeg}
              <input
                type="number"
                min={0}
                inputMode="numeric"
                value={value.advanced.maxWalkingPerLegM ?? ""}
                onChange={(event: ChangeEvent<HTMLElement>) => updateAdvanced("maxWalkingPerLegM", event.target.value === "" ? undefined : Number(event.target.value))}
                data-testid="setup-max-walking-leg"
              />
            </label>
            <label>
              {copy.journeySetup.maxContinuousWalking}
              <input
                type="number"
                min={0}
                inputMode="numeric"
                value={value.advanced.maxContinuousWalkingM ?? ""}
                onChange={(event: ChangeEvent<HTMLElement>) => updateAdvanced("maxContinuousWalkingM", event.target.value === "" ? undefined : Number(event.target.value))}
                data-testid="setup-max-walking-continuous"
              />
            </label>
            <label>
              {copy.journeySetup.restFrequency}
              <input
                type="number"
                min={0}
                inputMode="numeric"
                value={value.advanced.restFrequencyMin ?? ""}
                onChange={(event: ChangeEvent<HTMLElement>) => updateAdvanced("restFrequencyMin", event.target.value === "" ? undefined : Number(event.target.value))}
                data-testid="setup-rest-frequency"
              />
            </label>
            <label>
              {copy.journeySetup.toiletFrequency}
              <input
                type="number"
                min={0}
                inputMode="numeric"
                value={value.advanced.toiletFrequencyMin ?? ""}
                onChange={(event: ChangeEvent<HTMLElement>) => updateAdvanced("toiletFrequencyMin", event.target.value === "" ? undefined : Number(event.target.value))}
                data-testid="setup-toilet-frequency"
              />
            </label>
            <fieldset className="cne-nap-window">
              <legend>{copy.journeySetup.napWindow}</legend>
              <label>
                <span className="cne-sr-only">Start</span>
                <input
                  type="time"
                  value={value.advanced.napWindow?.start ?? ""}
                  onChange={(event: ChangeEvent<HTMLElement>) => updateAdvanced("napWindow", { start: event.target.value, end: value.advanced.napWindow?.end ?? "14:00" })}
                  data-testid="setup-nap-start"
                />
              </label>
              <span aria-hidden="true">–</span>
              <label>
                <span className="cne-sr-only">End</span>
                <input
                  type="time"
                  value={value.advanced.napWindow?.end ?? ""}
                  onChange={(event: ChangeEvent<HTMLElement>) => updateAdvanced("napWindow", { start: value.advanced.napWindow?.start ?? "12:00", end: event.target.value })}
                  data-testid="setup-nap-end"
                />
              </label>
            </fieldset>
            <label>
              {copy.journeySetup.pace}
              <select
                value={value.advanced.pace ?? ""}
                onChange={(event: ChangeEvent<HTMLElement>) => updateAdvanced("pace", event.target.value === "" ? undefined : (event.target.value as JourneySetupNeedsDraft["advanced"]["pace"]))}
                data-testid="setup-pace"
              >
                <option value="">—</option>
                <option value="RELAXED">{copy.journeySetup.paceRelaxed}</option>
                <option value="BALANCED">{copy.journeySetup.paceBalanced}</option>
                <option value="BRISK">{copy.journeySetup.paceBrisk}</option>
              </select>
            </label>
            <label className="cne-check cne-grid-full">
              <input
                type="checkbox"
                checked={Boolean(value.advanced.quietSensory)}
                onChange={(event: ChangeEvent<HTMLElement>) => updateAdvanced("quietSensory", event.target.checked)}
                data-testid="setup-quiet-sensory"
              />
              <span>{copy.journeySetup.quietSensory}</span>
            </label>
          </div>
        ) : null}
      </div>

      <label className="cne-setup__note">
        {copy.journeySetup.note}
        <textarea
          rows={2}
          value={value.note ?? ""}
          placeholder={copy.journeySetup.notePlaceholder}
          onChange={(event: ChangeEvent<HTMLElement>) => update("note", event.target.value)}
          data-testid="setup-note"
        />
      </label>

      <div className="cne-active-summary" aria-live="polite">
        <strong>{copy.journeySetup.activeSummary}</strong>
        {capabilities.length === 0 ? <span>{copy.mobile.noNeeds}</span> : (
          <ul>
            {capabilities.slice(0, 6).map((capability) => <li key={capability.id}>{capability.label}</li>)}
          </ul>
        )}
      </div>

      {showSourceNotice ? <p className="cne-source-notice" data-testid="setup-source-notice">{copy.journeySetup.sourceNotice}</p> : null}

      <footer className="cne-surface__actions">
        <button type="button" className="cne-button cne-button--ghost" onClick={() => onChange(EMPTY_JOURNEY_SETUP_NEEDS)} disabled={disabled} data-testid="setup-clear">
          {copy.journeySetup.clear}
        </button>
        <button
          type="button"
          className="cne-button cne-button--primary"
          disabled={disabled}
          onClick={() => onSave?.(capabilities)}
          data-testid="setup-save"
        >
          {copy.journeySetup.save}
        </button>
      </footer>
    </section>
  );
}