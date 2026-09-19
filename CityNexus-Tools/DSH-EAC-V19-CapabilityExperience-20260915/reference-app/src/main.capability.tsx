import { StrictMode, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./demo.css";
import { RECORDED_SCENARIOS, createRecordedFixtureAdapter, scenarioById } from "./features/capability-experience/recordedFixture";
import { createLiveCapabilityAdapter, CapabilityAdapterNotConfiguredError } from "./features/capability-experience/adapter";
import type { JourneySetupNeedsDraft } from "./features/capability-experience/types";
import { EMPTY_JOURNEY_SETUP_NEEDS, JourneySetupNeeds } from "./features/capability-experience/components/JourneySetupNeeds";
import { CopilotNeedsConfirmation } from "./features/capability-experience/components/CopilotNeedsConfirmation";
import { CapabilityPlanExplanation } from "./features/capability-experience/components/CapabilityPlanExplanation";
import { RecoveryDiffCapability } from "./features/capability-experience/components/RecoveryDiffCapability";
import { TwinCapabilitySummary } from "./features/capability-experience/components/TwinCapabilitySummary";
import { MobileCapabilityShield } from "./features/capability-experience/components/MobileCapabilityShield";
import { CapabilityMapOverlay } from "./features/capability-experience/components/CapabilityMapOverlay";

type Locale = "zh-CN" | "en";

function App() {
  const [locale, setLocale] = useState<Locale>("zh-CN");
  const [scenarioId, setScenarioId] = useState("A");
  const [sourceMode, setSourceMode] = useState<"RECORDED_FIXTURE" | "LIVE_ADAPTER">("RECORDED_FIXTURE");
  const [sourceStatus, setSourceStatus] = useState("");
  const [setupValue, setSetupValue] = useState<JourneySetupNeedsDraft>({
    ...EMPTY_JOURNEY_SETUP_NEEDS,
    quickNeedIds: ["less_walking", "midday_rest"],
    advanced: { maxWalkingPerLegM: 500, napWindow: { start: "12:00", end: "14:00" } },
    note: "我妈膝盖不好，不能走太多，中午最好休息。",
  });
  const scenario = useMemo(() => scenarioById(scenarioId), [scenarioId]);
  const recordedAdapter = useMemo(() => createRecordedFixtureAdapter(scenario), [scenario]);

  const testLiveAdapter = async () => {
    setSourceStatus("");
    try {
      const live = createLiveCapabilityAdapter({ baseUrl: "" });
      const capabilities = await live.fetchCapabilities("fixture-traveler");
      setSourceStatus(`${live.sourceKind}: ${capabilities.length} capabilities`);
    } catch (error) {
      if (error instanceof CapabilityAdapterNotConfiguredError) {
        setSourceStatus(`LIVE adapter unavailable: ${error.code}. RECORDED_FIXTURE remains selected; no live claim is made.`);
      } else {
        setSourceStatus(`LIVE adapter error: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
  };

  const chooseSource = (mode: "RECORDED_FIXTURE" | "LIVE_ADAPTER") => {
    setSourceMode(mode);
    setSourceStatus(mode === "RECORDED_FIXTURE" ? "Using labelled RECORDED_FIXTURE data. No live backend claim." : "LIVE adapter selected. It will report unavailable rather than fabricate data.");
  };

  return (
    <div className="demo-shell">
      <a className="demo-skip" href="#main-content">Skip to capability experience content</a>
      <header className="demo-header">
        <div>
          <span className="demo-badge demo-badge--recorded">V19 CAPABILITY EXPERIENCE LAB</span>
          <h1>Traveler Capability / Accessibility Experience Kit</h1>
          <p>Standards: HARD / STRONG / SOFT, Traveler/Journey scope, Verified / Unverified / Conflict / Needs live evidence. Unknown is never rendered as accessible.</p>
        </div>
        <div className="demo-toolbar" role="group" aria-label="Lab display controls">
          <button type="button" className="demo-button" onClick={() => setLocale((value) => value === "zh-CN" ? "en" : "zh-CN")} data-testid="demo-locale-toggle">
            {locale === "zh-CN" ? "English" : "中文"}
          </button>
          <span className="demo-badge demo-badge--recorded">SOURCE: {sourceMode}</span>
        </div>
      </header>

      <nav aria-label="Capability experience sections">
        <ul className="demo-section-nav">
          <li><a href="#setup">Setup</a></li>
          <li><a href="#copilot">Copilot detected needs</a></li>
          <li><a href="#plan">Plan explanation</a></li>
          <li><a href="#recovery">Recovery diff</a></li>
          <li><a href="#twin">Traveler Twin</a></li>
          <li><a href="#mobile">Mobile</a></li>
          <li><a href="#map">Map evidence</a></li>
        </ul>
      </nav>

      <section className={`demo-banner ${sourceMode === "RECORDED_FIXTURE" ? "demo-banner--recorded" : "demo-banner--live"}`} aria-labelledby="source-title" data-testid="source-banner">
        <div>
          <h2 id="source-title">Source honesty</h2>
          <p>
            {sourceMode === "RECORDED_FIXTURE"
              ? "RECORDED_FIXTURE: all scenarios below are labelled fixture data. They demonstrate UX states, not live provider truth."
              : "LIVE_ADAPTER: the adapter is wired to the proposed endpoints, but unavailable calls are reported as unavailable. It never falls back silently."}
          </p>
          {sourceStatus ? <p className="demo-status" role="status" aria-live="polite">{sourceStatus}</p> : null}
        </div>
        <div className="demo-toolbar">
          <button type="button" className="demo-button" aria-pressed={sourceMode === "RECORDED_FIXTURE"} onClick={() => chooseSource("RECORDED_FIXTURE")} data-testid="source-recorded">Use RECORDED_FIXTURE</button>
          <button type="button" className="demo-button" aria-pressed={sourceMode === "LIVE_ADAPTER"} onClick={() => chooseSource("LIVE_ADAPTER")} data-testid="source-live">Select LIVE adapter</button>
          <button type="button" className="demo-button" onClick={() => void testLiveAdapter()} data-testid="source-test-live">Test live adapter</button>
        </div>
      </section>

      <section aria-labelledby="scenario-title">
        <h2 id="scenario-title">Reference scenarios</h2>
        <div className="demo-scenarios" role="group" aria-label="Reference scenarios">
          {RECORDED_SCENARIOS.map((item) => (
            <button
              key={item.id}
              type="button"
              className="demo-scenario"
              aria-pressed={scenarioId === item.id}
              onClick={() => setScenarioId(item.id)}
              data-testid={`scenario-${item.id}`}
            >
              <strong>{locale === "zh-CN" ? item.titleZh : item.titleEn}</strong>
              <small>{locale === "zh-CN" ? item.summaryZh : item.summaryEn}</small>
            </button>
          ))}
        </div>
      </section>

      <main id="main-content" className="demo-grid">
        <section id="setup" aria-labelledby="setup-title">
          <h2 id="setup-title">1 · Journey Setup UX</h2>
          <p className="demo-caption">Optional quick chips and progressive advanced constraints. The draft is UI-only until the backend capability contract confirms it.</p>
          <JourneySetupNeeds value={setupValue} onChange={setSetupValue} locale={locale} onSave={(capabilities) => setSourceStatus(`UI draft emitted ${capabilities.length} capability candidates; no backend planning authority claimed.`)} />
        </section>

        <section id="copilot" aria-labelledby="copilot-title">
          <h2 id="copilot-title">2 · Copilot Detected Needs confirmation</h2>
          <p className="demo-caption">Detected language is a proposal, not authority. HARD future persistence requires explicit acknowledgement.</p>
          <div className="demo-grid demo-grid--2">
            <CopilotNeedsConfirmation
              confirmations={scenario.detected}
              statement={scenario.setup.note}
              locale={locale}
              onDecision={(decision) => setSourceStatus(`Confirmation decision: ${decision.action}; ${decision.capabilities.length} capabilities emitted.`)}
            />
            <div className="demo-mobile-frame" aria-label="Mobile Copilot bottom sheet reference">
              <CopilotNeedsConfirmation
                confirmations={scenario.detected}
                statement={scenario.setup.note}
                locale={locale}
                surface="sheet"
                onDecision={(decision) => setSourceStatus(`Mobile sheet decision: ${decision.action}; ${decision.capabilities.length} capabilities emitted.`)}
              />
            </div>
          </div>
        </section>

        <section id="plan" aria-labelledby="plan-title">
          <h2 id="plan-title">3 · Capability-aware Plan explanation</h2>
          <CapabilityPlanExplanation model={scenario.plan} locale={locale} />
        </section>

        <section id="recovery" aria-labelledby="recovery-title">
          <h2 id="recovery-title">4 · Recovery Diff</h2>
          <RecoveryDiffCapability model={scenario.recovery} locale={locale} />
        </section>

        <section id="twin" aria-labelledby="twin-title">
          <h2 id="twin-title">5 · Traveler Twin capability presentation</h2>
          <TwinCapabilitySummary capabilities={scenario.capabilities} locale={locale} />
        </section>

        <section id="mobile" data-testid="mobile-section" aria-labelledby="mobile-title">
          <h2 id="mobile-title">6 · Mobile Capability Shield</h2>
          <p className="demo-caption">390×844 / 430×932 reference frame. A HARD need produces a compact shield; evidence gaps stay visible without a panic wall.</p>
          <div className="demo-mobile-frame">
            <MobileCapabilityShield model={scenario.mobile.shield} locale={locale} onPrimaryAction={() => setSourceStatus("Mobile primary action is visible and reachable.")} />
            <div className="cne-plan" data-testid="mobile-plan-summary">
              <h3>{locale === "zh-CN" ? "移动端方案摘要" : "Mobile plan summary"}</h3>
              <ul className="cne-impact-list">
                {scenario.plan.why.slice(0, 2).map((impact) => (
                  <li key={impact.id} className="cne-impact">
                    <strong>{impact.capabilityLabel}</strong>
                    <span>{impact.explanation}</span>
                  </li>
                ))}
              </ul>
              <p className="cne-rule">{locale === "zh-CN" ? "未知 ≠ 无障碍可用。" : "Unknown is not accessible."}</p>
            </div>
          </div>
        </section>

        <section id="map" aria-labelledby="map-title">
          <h2 id="map-title">7 · Map evidence markers</h2>
          <CapabilityMapOverlay markers={scenario.mobile.mapMarkers} locale={locale} />
        </section>
      </main>

      <footer>
        <p>RECORDED_FIXTURE reference app. Product patches add files under <code>frontend/src/features/capability-experience/</code>; they do not replace router, main.tsx, or LocaleProvider.</p>
      </footer>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
