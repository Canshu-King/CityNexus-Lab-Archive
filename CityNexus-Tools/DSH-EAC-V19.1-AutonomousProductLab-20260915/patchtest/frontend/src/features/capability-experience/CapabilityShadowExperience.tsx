import { useCallback, useEffect, useMemo, useState, type ChangeEvent } from "react";
import type {
  CapabilityConfirmation,
  JourneySetupNeedsDraft,
  MobileCapabilityShieldModel,
  RecoveryCapabilityDiffModel,
  TravelerCapability,
} from "./types";
import { EMPTY_JOURNEY_SETUP_NEEDS, JourneySetupNeeds } from "./components/JourneySetupNeeds";
import { CopilotNeedsConfirmation } from "./components/CopilotNeedsConfirmation";
import { CapabilityPlanExplanation } from "./components/CapabilityPlanExplanation";
import { RecoveryDiffCapability } from "./components/RecoveryDiffCapability";
import { TwinCapabilitySummary } from "./components/TwinCapabilitySummary";
import { MobileCapabilityShield } from "./components/MobileCapabilityShield";
import { ProviderEvidencePanel } from "./components/ProviderEvidencePanel";
import { capabilityLabel, capabilityKindLabel } from "./evidence";
import {
  createHttpShadowClient,
  loadCapabilitySource,
  mapJourneySetupDraftToBackend,
  type CapabilitySourceMode,
  type CapabilitySourceResult,
} from "./liveShadowAdapter";
import { mapPlanImpactResponse, mapRecoveryDiffFromPlan, type BackendPlanImpactResponse } from "./livePlanAdapter";
import {
  loadProviderEvidence,
  type ProviderEvidenceResult,
} from "./providerEvidence";

export interface CapabilityShadowExperienceProps {
  client?: ReturnType<typeof createHttpShadowClient>;
  baseUrl?: string;
  initialTravelerId?: string;
  initialJourneyId?: string;
  initialPlaceId?: string;
  suggestedPlanVersionId?: string;
  locale?: "zh-CN" | "en";
  fixtureCapabilities?: TravelerCapability[];
}

function buildShieldModel(capabilities: TravelerCapability[], locale: "zh-CN" | "en"): MobileCapabilityShieldModel {
  const protectedNeeds = capabilities.filter(
    (item) => item.active && (item.strength === "HARD" || item.strength === "STRONG" || item.kind === "HARD_ACCESSIBILITY_NEED"),
  );
  const gap = capabilities.find(
    (item) => item.active && item.kind === "HARD_ACCESSIBILITY_NEED" && item.evidence.state !== "VERIFIED",
  );
  return {
    protectedCount: protectedNeeds.length,
    needs: protectedNeeds,
    evidenceGap: gap
      ? { label: `${capabilityLabel(gap, locale)}: ${gap.evidence.summary}`, capabilityId: gap.id, evidence: gap.evidence }
      : null,
    primaryActionLabel: locale === "zh-CN" ? "查看或修改需求" : "Review or edit needs",
  };
}

function buildConfirmations(capabilities: TravelerCapability[]): CapabilityConfirmation[] {
  return capabilities
    .filter((item) => item.active && !item.confirmed)
    .map((item) => ({
      id: item.id,
      statement: "Live capability contract returned an unconfirmed row.",
      detectedLabel: item.label,
      capability: item,
      ambiguous: false,
    }));
}

export function CapabilityShadowExperience({
  client: providedClient,
  baseUrl = "",
  initialTravelerId = "",
  initialJourneyId = "",
  initialPlaceId = "",
  suggestedPlanVersionId,
  locale = "zh-CN",
  fixtureCapabilities,
}: CapabilityShadowExperienceProps) {
  const client = useMemo(() => providedClient ?? createHttpShadowClient(baseUrl), [providedClient, baseUrl]);
  const [mode, setMode] = useState<CapabilitySourceMode>("LIVE_SHADOW");
  const [travelerId, setTravelerId] = useState(initialTravelerId);
  const [journeyId, setJourneyId] = useState(initialJourneyId);
  const [placeId, setPlaceId] = useState(initialPlaceId);
  const [capabilityResult, setCapabilityResult] = useState<CapabilitySourceResult | null>(null);
  const [providerResult, setProviderResult] = useState<ProviderEvidenceResult | null>(null);
  const [planModel, setPlanModel] = useState<ReturnType<typeof mapPlanImpactResponse>>(null);
  const [recoveryModel, setRecoveryModel] = useState<RecoveryCapabilityDiffModel | null>(null);
  const [setupValue, setSetupValue] = useState<JourneySetupNeedsDraft>({ ...EMPTY_JOURNEY_SETUP_NEEDS, quickNeedIds: [], advanced: {} });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    setMessage("");
    try {
      const capabilities = await loadCapabilitySource(client, {
        mode,
        travelerId: travelerId || undefined,
        journeyId: journeyId || undefined,
        locale,
        fixtureCapabilities,
      });
      setCapabilityResult(capabilities);
      const providerFetcher = placeId
        ? () => client.getPlaceAccessibilityEvidence(placeId)
        : journeyId
          ? () => client.getJourneyAccessibilityEvidence(journeyId)
          : null;
      if (providerFetcher) {
        const provider = await loadProviderEvidence({ mode, placeId: placeId || undefined, journeyId: journeyId || undefined, fetcher: providerFetcher });
        setProviderResult(provider);
      } else {
        setProviderResult(null);
      }
      if (journeyId) {
        const planResponse = (await client.getCapabilityPlanImpact(journeyId, suggestedPlanVersionId)) as unknown as BackendPlanImpactResponse;
        const mapped = mapPlanImpactResponse(planResponse);
        setPlanModel(mapped);
        setRecoveryModel(mapped ? mapRecoveryDiffFromPlan(planResponse, journeyId) : null);
      } else {
        setPlanModel(null);
        setRecoveryModel(null);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  }, [client, fixtureCapabilities, journeyId, locale, mode, placeId, suggestedPlanVersionId, travelerId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const detectedNeeds = useMemo(() => buildConfirmations(capabilityResult?.capabilities ?? []), [capabilityResult]);
  const shield = useMemo(() => buildShieldModel(capabilityResult?.capabilities ?? [], locale), [capabilityResult, locale]);

  const handleSetupSave = async () => {
    setMessage("");
    try {
      const payload = mapJourneySetupDraftToBackend(setupValue);
      if (journeyId) {
        await client.confirmJourneyCapabilities(journeyId, payload);
      } else if (travelerId) {
        await client.confirmTravelerCapabilities(travelerId, payload);
      } else {
        setMessage("No traveler/journey selected; draft was not confirmed.");
        return;
      }
      setMessage("Capability draft confirmed against the live/shadow contract. UI does not persist planning authority.");
      await reload();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    }
  };

  const handleDetectedDecision = async (decision: { action: string; capabilities: TravelerCapability[] }) => {
    if (decision.action === "DISMISS") {
      setMessage("Detected needs dismissed; no persistence request sent.");
      return;
    }
    const payload = decision.capabilities.map((item) => ({
      code: String(item.extra?.backend_code ?? ""),
      class: String(item.extra?.backend_class ?? item.kind),
      severity: item.strength === "AMBIGUOUS" ? "STRONG" : item.strength,
      params: (item.extra?.backend_params as Record<string, unknown>) ?? {},
      scope: item.scope === "TRAVELER" ? "TRAVELER" : "JOURNEY",
      source: "USER_CONFIRMED",
      provenance: "USER_CONFIRMED",
      explicit: true,
      active: true,
      confirmed: true,
    })).filter((item) => item.code);
    try {
      if (journeyId) await client.confirmJourneyCapabilities(journeyId, payload);
      else if (travelerId) await client.confirmTravelerCapabilities(travelerId, payload);
      else {
        setMessage("No traveler/journey selected; confirmation not sent.");
        return;
      }
      setMessage(`Confirmation decision ${decision.action} sent for ${payload.length} capability row(s).`);
      await reload();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    }
  };

  const modeButton = (candidate: CapabilitySourceMode, label: string) => (
    <button
      type="button"
      className={`cne-chip ${mode === candidate ? "is-selected" : ""}`}
      role="checkbox"
      aria-checked={mode === candidate}
      onClick={() => setMode(candidate)}
      data-testid={`shadow-mode-${candidate}`}
    >
      {label}
    </button>
  );

  return (
    <section className="cne-shadow-experience" data-testid="capability-shadow-experience">
      <header className="cne-surface__head">
        <div>
          <span className="cne-kicker">V19.1 SHADOW INTEGRATION</span>
          <h1>Capability-aware live/shadow experience</h1>
          <p>
            {locale === "zh-CN"
              ? "LIVE_SHADOW 只展示隔离后端返回的数据；RECORDED_FIXTURE 明确标记；断线时保留 last-known 数据并标为 OFFLINE_STALE。"
              : "LIVE_SHADOW only displays isolated-backend data. RECORDED_FIXTURE is labelled. Disconnects keep last-known data as OFFLINE_STALE."}
          </p>
        </div>
        <span className={`cne-source-pill ${mode === "LIVE_SHADOW" ? "is-live" : ""}`}>{mode}</span>
      </header>

      <div className="cne-shadow-controls" role="group" aria-label="Shadow source controls">
        {modeButton("LIVE_SHADOW", "LIVE_SHADOW")}
        {modeButton("RECORDED_FIXTURE", "RECORDED_FIXTURE")}
        {modeButton("OFFLINE_STALE", "OFFLINE_STALE")}
        <label>
          traveler_id
          <input value={travelerId} onChange={(event: ChangeEvent<HTMLElement>) => setTravelerId(event.target.value)} data-testid="shadow-traveler-id" />
        </label>
        <label>
          journey_id
          <input value={journeyId} onChange={(event: ChangeEvent<HTMLElement>) => setJourneyId(event.target.value)} data-testid="shadow-journey-id" />
        </label>
        <label>
          place_id
          <input value={placeId} onChange={(event: ChangeEvent<HTMLElement>) => setPlaceId(event.target.value)} data-testid="shadow-place-id" />
        </label>
        <button type="button" className="cne-button cne-button--primary" onClick={() => void reload()} disabled={loading} data-testid="shadow-reload">
          {loading ? (locale === "zh-CN" ? "加载中" : "Loading") : (locale === "zh-CN" ? "重新加载" : "Reload")}
        </button>
      </div>

      {capabilityResult ? (
        <section className={`cne-shadow-source cne-shadow-source--${capabilityResult.mode.toLowerCase()}`} data-testid="shadow-source-result">
          <b>{capabilityResult.label}</b>
          <span>{capabilityResult.mode}</span>
          <span>{capabilityResult.fetchedAt}</span>
          {capabilityResult.staleAt ? <span>{locale === "zh-CN" ? "stale at" : "stale at"}: {capabilityResult.staleAt}</span> : null}
          {capabilityResult.error ? <p role="status">{capabilityResult.error}</p> : null}
          {capabilityResult.contractGap?.length ? <ul>{capabilityResult.contractGap.map((gap) => <li key={gap}>{gap}</li>)}</ul> : null}
        </section>
      ) : null}
      {message ? <p className="cne-status" role="status" aria-live="polite" data-testid="shadow-message">{message}</p> : null}

      <div className="cne-shadow-grid">
        <section aria-labelledby="shadow-setup-title">
          <h2 id="shadow-setup-title">{locale === "zh-CN" ? "1 · Journey Setup 实时确认" : "1 · Live Journey Setup confirmation"}</h2>
          <JourneySetupNeeds value={setupValue} onChange={setSetupValue} locale={locale} onSave={() => void handleSetupSave()} />
        </section>

        <section aria-labelledby="shadow-confirm-title">
          <h2 id="shadow-confirm-title">{locale === "zh-CN" ? "2 · Copilot 检测需求确认" : "2 · Copilot detected-needs confirmation"}</h2>
          {detectedNeeds.length ? (
            <CopilotNeedsConfirmation confirmations={detectedNeeds} locale={locale} onDecision={(decision) => void handleDetectedDecision(decision)} />
          ) : (
            <p className="cne-rule">{locale === "zh-CN" ? "live contract 没有未确认的 capability 行。" : "The live contract has no unconfirmed capability rows."}</p>
          )}
        </section>

        <section aria-labelledby="shadow-twin-title">
          <h2 id="shadow-twin-title">{locale === "zh-CN" ? "3 · TravelerTwin capability" : "3 · TravelerTwin capability"}</h2>
          <TwinCapabilitySummary capabilities={capabilityResult?.capabilities ?? []} locale={locale} />
        </section>

        <section aria-labelledby="shadow-mobile-title">
          <h2 id="shadow-mobile-title">{locale === "zh-CN" ? "4 · Mobile capability shield" : "4 · Mobile capability shield"}</h2>
          <div className="cne-mobile-frame">
            <MobileCapabilityShield model={shield} locale={locale} />
          </div>
        </section>

        <section aria-labelledby="shadow-provider-title">
          <h2 id="shadow-provider-title">{locale === "zh-CN" ? "5 · Accessibility provider evidence" : "5 · Accessibility provider evidence"}</h2>
          {providerResult ? <ProviderEvidencePanel result={providerResult} locale={locale} /> : <p className="cne-rule">{locale === "zh-CN" ? "未选择 place/journey，或 provider evidence 未加载。" : "No place/journey selected, or provider evidence not loaded."}</p>}
        </section>

        <section aria-labelledby="shadow-plan-title">
          <h2 id="shadow-plan-title">{locale === "zh-CN" ? "6 · Capability-aware plan impact" : "6 · Capability-aware plan impact"}</h2>
          {planModel ? <CapabilityPlanExplanation model={planModel} locale={locale} /> : <p className="cne-rule" data-testid="plan-impact-contract-gap">{locale === "zh-CN" ? "CONTRACT_NOT_AVAILABLE：当前 journey 尚无可用 plan impact；不会软化成“已保护”。" : "CONTRACT_NOT_AVAILABLE: no plan impact for this journey; no softened preserved claim."}</p>}
        </section>

        <section aria-labelledby="shadow-recovery-title">
          <h2 id="shadow-recovery-title">{locale === "zh-CN" ? "7 · Recovery capability diff" : "7 · Recovery capability diff"}</h2>
          {recoveryModel ? <RecoveryDiffCapability model={recoveryModel} locale={locale} /> : <p className="cne-rule">{locale === "zh-CN" ? "CONTRACT_NOT_AVAILABLE：尚无 recovery capability diff 数据。" : "CONTRACT_NOT_AVAILABLE: no recovery capability diff yet."}</p>}
        </section>
      </div>

      <p className="cne-rule">{locale === "zh-CN" ? "UNKNOWN != ACCESSIBLE。未知证据不显示绿色勾号；本地 UI 不冒充 planning authority。" : "UNKNOWN != ACCESSIBLE. Missing evidence never gets a green check; local UI never impersonates planning authority."}</p>
    </section>
  );
}
