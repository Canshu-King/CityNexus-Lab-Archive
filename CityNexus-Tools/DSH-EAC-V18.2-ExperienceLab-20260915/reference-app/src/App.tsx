import { useEffect, useMemo, useState } from "react";
import { useLocale, useT } from "./i18n";
import { syncReducedMotionAttribute, withViewTransition } from "./motion";
import { testIds } from "./testids";
import type { AgentRunFixture, RuntimeStatus } from "./types";
import { ACTIVITIES, JOURNEY, PULSE, PULSE_I18N, RECOVERY, WALLET_ITEMS, pick } from "./data/journey";
import { JourneyPulse } from "./components/JourneyPulse";
import { TodayTimeline } from "./components/TodayTimeline";
import { DesktopNav, LocaleToggle, MobileNav } from "./components/TravelerNav";
import { CopilotDock } from "./components/CopilotDock";
import { RecoveryDiff } from "./components/RecoveryDiff";
import { MapCanvas } from "./components/MapCanvas";
import { MapBottomSheet } from "./components/MapBottomSheet";
import { RuntimeStatusBanner } from "./components/RuntimeTruthBadge";

const ROUTES = [
  "journey",
  "live",
  "map",
  "studio",
  "stay",
  "discover",
  "wallet",
  "copilot",
  "recovery",
  "intelligence",
  "twin",
  "me",
] as const;
type RouteKey = (typeof ROUTES)[number];

function readRoute(): RouteKey {
  const hash = window.location.hash.replace(/^#\/?/, "");
  if (hash === "today") return "journey";
  return (ROUTES as readonly string[]).includes(hash) ? (hash as RouteKey) : "journey";
}

function readEvidenceState(): "verified" | "unresolved" | "stale" | null {
  const value = new URLSearchParams(window.location.search).get("evidence");
  return value === "unresolved" || value === "stale" ? value : null;
}

function readRuntimeStatus(): RuntimeStatus {
  const value = new URLSearchParams(window.location.search).get("runtime");
  const allowed: RuntimeStatus[] = [
    "ready",
    "hermes_unavailable",
    "deepseek_unavailable",
    "provider_unavailable",
    "offline_stale",
  ];
  return allowed.includes(value as RuntimeStatus) ? (value as RuntimeStatus) : "ready";
}

function findActivity(id: string) {
  return ACTIVITIES.find((activity) => activity.id === id) ?? ACTIVITIES[0];
}

export function App() {
  const t = useT();
  const { locale } = useLocale();
  const [route, setRoute] = useState<RouteKey>(readRoute);
  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatus>(readRuntimeStatus);
  const evidenceState = readEvidenceState();
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia("(max-width: 1023px)").matches : false,
  );
  const [copilotOpen, setCopilotOpen] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia("(min-width: 1024px)").matches : false,
  );
  const [activeFixture, setActiveFixture] = useState<AgentRunFixture | null>(null);

  useEffect(() => syncReducedMotionAttribute(), []);

  useEffect(() => {
    const onHash = () => setRoute(readRoute());
    const onResize = () => setIsMobile(window.matchMedia("(max-width: 1023px)").matches);
    window.addEventListener("hashchange", onHash);
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("hashchange", onHash);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  const navigate = (next: string) => {
    const target = (ROUTES as readonly string[]).includes(next) ? (next as RouteKey) : "journey";
    withViewTransition(() => {
      window.location.hash = `#/${target}`;
      setRoute(target);
      if (target === "copilot") setCopilotOpen(true);
      if (window.matchMedia("(max-width: 1023px)").matches && target !== "copilot") setCopilotOpen(false);
    });
  };

  const recoveryProposal = useMemo(
    () => (evidenceState ? { ...RECOVERY, evidence_state: evidenceState } : RECOVERY),
    [evidenceState],
  );

  const pulse = useMemo(() => {
    const nowLocalized = pick(findActivity(PULSE.now.activity.id).title, locale);
    const nextLocalized = pick(findActivity(PULSE.next.activity.id).title, locale);
    const riskLabel =
      PULSE.risk.level === "high" ? t("pulse.riskHigh") : PULSE.risk.level === "low" ? t("pulse.riskLow") : t("pulse.riskWatch");
    return { nowLocalized, nextLocalized, riskLabel };
  }, [locale, t]);

  const headingKeys: Record<RouteKey, string> = {
    journey: "today.title",
    live: "nav.live",
    map: "map.title",
    studio: "nav.studio",
    stay: "nav.stay",
    discover: "nav.discover",
    wallet: "wallet.title",
    copilot: "copilot.title",
    recovery: "recovery.title",
    intelligence: "nav.intelligence",
    twin: "nav.twin",
    me: "me.title",
  };

  return (
    <div className="app" data-testid={testIds.appShell} data-runtime-status={runtimeStatus}>
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark" aria-hidden="true">
            ◈
          </span>
          <div>
            <b>{t("app.brand")}</b>
            <small>{t("app.tagline")}</small>
          </div>
        </div>
        <div className="topbar__meta">
          <span className="pill">{t("app.reference")}</span>
          <span className="pill pill--quiet">{t("app.isolated")}</span>
          {runtimeStatus !== "ready" && (
            <span className="pill pill--warn" data-testid="topbar-runtime-status">
              {t(`runtime.status.${runtimeStatus}.title`)}
            </span>
          )}
        </div>
        <LocaleToggle />
      </header>

      <div className="layout">
        <DesktopNav active={route} onNavigate={navigate} />
        <main className="main">
          <div className="main__head">
            <div>
              <span className="kicker">{t(headingKeys[route])}</span>
              <h1 data-testid={testIds.routeHeading}>{t(headingKeys[route])}</h1>
            </div>
            <span className="muted small">
              {pick(JOURNEY.city, locale)} · {JOURNEY.planVersion}
            </span>
          </div>

          <RuntimeStatusBanner status={runtimeStatus} onAction={() => navigate("journey")} />

          {(route === "journey" || route === "live") && (
            <>
              {route === "journey" && <p className="lede">{t("today.lede")}</p>}
              <JourneyPulse
                pulse={PULSE}
                nowTitle={pulse.nowLocalized}
                nextTitle={pulse.nextLocalized}
                riskLevelLabel={pulse.riskLabel}
                actionLabel={pick(PULSE_I18N.actionLabel, locale)}
                nowNote={pick(PULSE_I18N.nowNote, locale)}
                nextNote={pick(PULSE_I18N.nextNote, locale)}
                riskTitle={pick(PULSE_I18N.riskTitle, locale)}
                riskDetail={pick(PULSE_I18N.riskDetail, locale)}
                actionReason={pick(PULSE_I18N.actionReason, locale)}
                onPrimaryAction={() => navigate("recovery")}
              />
              <div className="journey-lower">
                <TodayTimeline />
                <div className="journey-map-preview">
                  <span className="kicker">{t("today.liveMap")}</span>
                  <MapCanvas />
                </div>
              </div>
              <p className="muted small">{t("today.techDetail")}</p>
            </>
          )}
          {route === "map" && (
            <div className="map-layout">
              <MapCanvas />
              <MapBottomSheet>
                {(sheet) => (
                  <>
                    {sheet === "24" && (
                      <div className="sheet-state" data-testid="sheet-content-24">
                        <h3>{t("map.now")}</h3>
                        <p>
                          <b>{pulse.nowLocalized}</b> · {PULSE.now.time} · {PULSE.now.eta}
                        </p>
                        <h3>{t("map.nextActivity")}</h3>
                        <p>
                          <b>{pulse.nextLocalized}</b> · {PULSE.next.time} · {t("pulse.buffer", { n: PULSE.next.buffer_min })}
                        </p>
                      </div>
                    )}
                    {sheet === "55" && (
                      <div className="sheet-state" data-testid="sheet-content-55">
                        <h3>{t("map.route")}</h3>
                        <p>Wudadao → Haihe dock → Ancient Culture Street · 6.4 km</p>
                        <h3>{t("map.transport")}</h3>
                        <p>Walk 22 min · Metro line 3 · Walk 8 min · recorded fixture</p>
                        <h3>{t("map.nextCommitment")}</h3>
                        <p>
                          <b>{pulse.nextLocalized}</b> · C4 protected · {t("pulse.buffer", { n: PULSE.next.buffer_min })}
                        </p>
                      </div>
                    )}
                    {sheet === "90" && (
                      <div className="sheet-state" data-testid="sheet-content-90">
                        <h3>{t("map.fullDetails")}</h3>
                        <ol className="activity-list">
                          {ACTIVITIES.map((activity) => (
                            <li key={activity.id} className={activity.protected ? "protected" : undefined}>
                              <time>{activity.start_at.slice(11, 16)}</time>
                              <span>{pick(activity.title, locale)}</span>
                              <small>
                                {t(`environment.${activity.environment}`)} · {activity.walking_min} {t("recovery.walking")}
                              </small>
                              {activity.protected && <em>C4</em>}
                            </li>
                          ))}
                        </ol>
                        <h3>{t("map.recoveryDetails")}</h3>
                        <p>{pick(RECOVERY.trigger, locale)}</p>
                        <button type="button" className="btn btn--primary" onClick={() => navigate("recovery")}>
                          {t("pulse.openRecovery")}
                        </button>
                      </div>
                    )}
                  </>
                )}
              </MapBottomSheet>
            </div>
          )}

          {route === "wallet" && (
            <section className="card">
              <span className="kicker">{t("wallet.kicker")}</span>
              <h2>{t("wallet.title")}</h2>
              <ul className="wallet-list">
                {WALLET_ITEMS.map((item) => (
                  <li key={item.id}>
                    <b>{pick(item.type, locale)}</b>
                    <small>{item.confirmation}</small>
                    <span className="chip">{item.status}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {route === "copilot" && (
            <section className="card">
              <span className="kicker">{t("copilot.kicker")}</span>
              <h2>{t("copilot.title")}</h2>
              <p className="muted">
                The dock carries semantic interpretation, runtime truth, agent activity, proposal, and approval. Mobile
                opens the same content as a bottom sheet with a persistent mini composer.
              </p>
              <button type="button" className="btn btn--primary" onClick={() => setCopilotOpen(true)}>
                {t("copilot.open")}
              </button>
            </section>
          )}

          {route === "recovery" && <RecoveryDiff proposal={recoveryProposal} />}

          {["studio", "stay", "discover", "intelligence", "twin"].includes(route) && (
            <section className="card">
              <span className="kicker">{t(`nav.${route === "intelligence" ? "intelligence" : route === "twin" ? "twin" : route}`)}</span>
              <h2>{t(headingKeys[route])}</h2>
              <p className="muted">
                Isolated reference placeholder. Technical internals stay behind disclosure; the merge guide keeps Codex's
                authoritative implementation untouched.
              </p>
              <details className="technical">
                <summary>{t("pulse.technical")}</summary>
                <p>Reference route only. No PlanVersion, Gateway, or domain mutation is performed here.</p>
              </details>
            </section>
          )}

          {route === "me" && (
            <section className="card">
              <span className="kicker">{t("me.kicker")}</span>
              <h2>{t("me.title")}</h2>
              <p className="muted">{t("me.note")}</p>
              <dl className="settings">
                <div>
                  <dt>{t("me.locale")}</dt>
                  <dd>
                    <LocaleToggle />
                  </dd>
                </div>
                <div>
                  <dt>{t("me.reducedMotion")}</dt>
                  <dd data-testid="reduced-motion-state">{document.documentElement.dataset.reducedMotion}</dd>
                </div>
                <div>
                  <dt>Runtime reference state</dt>
                  <dd data-testid="runtime-state-value">{runtimeStatus}</dd>
                </div>
              </dl>
              <div className="runtime-demo" role="group" aria-label="Runtime reference states">
                {(
                  [
                    "ready",
                    "hermes_unavailable",
                    "deepseek_unavailable",
                    "provider_unavailable",
                    "offline_stale",
                  ] as RuntimeStatus[]
                ).map((status) => (
                  <button
                    key={status}
                    type="button"
                    className={`chip-btn${runtimeStatus === status ? " active" : ""}`}
                    data-testid={`runtime-demo-${status}`}
                    onClick={() => setRuntimeStatus(status)}
                  >
                    {status === "ready" ? t("runtime.live") : t(`runtime.status.${status}.title`)}
                  </button>
                ))}
              </div>
            </section>
          )}
        </main>
        <CopilotDock
          open={route === "copilot" ? true : copilotOpen}
          onOpenChange={setCopilotOpen}
          onNavigate={navigate}
          activeFixture={activeFixture}
          onFixtureChange={setActiveFixture}
          isMobile={isMobile}
        />
      </div>
      <MobileNav active={route} onNavigate={navigate} />
      <footer className="footer">{t("shell.footer")}</footer>
    </div>
  );
}
