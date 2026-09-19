import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import { useLocale, useT } from "./i18n";
import { syncReducedMotionAttribute, withViewTransition } from "./motion";
import { testIds } from "./testids";
import type { PulseState, RuntimeStatus } from "./types";
import { DesktopNav, LocaleToggle, MobileNav } from "./components/TravelerNav";
import type { TodayTimelineItem } from "./components/TodayTimeline";
import { CopilotDock } from "./components/CopilotDock";
import { RuntimeStatusBanner } from "./components/RuntimeTruthBadge";
import { useExperienceAdapter, useJourneyPulse, useRuntimeStatus } from "./adapters/ExperienceAdapterContext";
import { useOnlineStatus } from "./pwa/onlineStatus";
import { ACTIVITY_TITLES, PULSE_COPY, WALLET_COPY } from "./experience/copy";
import { pick } from "./experience/locale";

const JourneyRoute = lazy(() => import("./routes/JourneyRoute"));
const MapRoute = lazy(() => import("./routes/MapRoute"));
const RecoveryRoute = lazy(() => import("./routes/RecoveryRoute"));
const CapabilityRoute = lazy(() => import("./routes/CapabilityRoute"));
const TimelineLabRoute = lazy(() => import("./routes/TimelineLabRoute"));

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
  "capability",
  "timeline-lab",
  "me",
] as const;
type RouteKey = (typeof ROUTES)[number];

function readRoute(): RouteKey {
  const hash = window.location.hash.replace(/^#\/?/, "");
  if (hash === "today") return "journey";
  return (ROUTES as readonly string[]).includes(hash) ? (hash as RouteKey) : "journey";
}

function readRuntimeOverride(): RuntimeStatus | null {
  const value = new URLSearchParams(window.location.search).get("runtime");
  const allowed: RuntimeStatus[] = ["ready", "hermes_unavailable", "deepseek_unavailable", "provider_unavailable", "offline_stale"];
  return allowed.includes(value as RuntimeStatus) ? (value as RuntimeStatus) : null;
}

function titleFor(activityId: string, fallback: string, locale: "en" | "zh-CN"): string {
  const copy = ACTIVITY_TITLES[activityId];
  return copy ? pick(copy, locale) : fallback;
}

function fallbackTimeline(pulse: PulseState): TodayTimelineItem[] {
  return [pulse.now.activity, pulse.next.activity].map((activity, index) => ({
    id: activity.id,
    time: index === 0 ? pulse.now.time : pulse.next.time,
    title: ACTIVITY_TITLES[activity.id] ?? { en: activity.title, zh: activity.title },
    environment: activity.environment,
    protected: activity.protected,
    status: index === 0 ? "current" : "upcoming",
  }));
}

export function App() {
  const t = useT();
  const { locale } = useLocale();
  const adapter = useExperienceAdapter();
  const { online } = useOnlineStatus();
  const pulse = useJourneyPulse();
  const runtime = useRuntimeStatus();
  const [route, setRoute] = useState<RouteKey>(readRoute);
  const [runtimeOverride, setRuntimeOverride] = useState<RuntimeStatus | null>(readRuntimeOverride);
  const [copilotOpen, setCopilotOpen] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia("(min-width: 1024px)").matches : false,
  );
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia("(max-width: 1023px)").matches : false,
  );
  const [timelineItems, setTimelineItems] = useState<TodayTimelineItem[]>([]);

  useEffect(() => syncReducedMotionAttribute(), []);

  useEffect(() => {
    const onHash = () => setRoute(readRoute());
    const onResize = () => setIsMobile(window.matchMedia("(max-width: 1023px)").matches);
    window.addEventListener("hashchange", onHash);
    window.addEventListener("resize", onResize);
    window.addEventListener("orientationchange", onResize);
    return () => {
      window.removeEventListener("hashchange", onHash);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("orientationchange", onResize);
    };
  }, []);

  useEffect(() => {
    if (!pulse.data) return undefined;
    let cancelled = false;
    const request = adapter.getTodayTimeline?.() ?? Promise.resolve(fallbackTimeline(pulse.data));
    request
      .then((items) => {
        if (!cancelled) setTimelineItems(items ?? fallbackTimeline(pulse.data as PulseState));
      })
      .catch(() => {
        if (!cancelled) setTimelineItems(fallbackTimeline(pulse.data as PulseState));
      });
    return () => {
      cancelled = true;
    };
  }, [adapter, pulse.data]);

  const runtimeStatus: RuntimeStatus = runtimeOverride ?? (!online ? "offline_stale" : runtime.data?.status ?? "ready");

  const navigate = (next: string) => {
    const target = (ROUTES as readonly string[]).includes(next) ? (next as RouteKey) : "journey";
    withViewTransition(() => {
      window.location.hash = `#/${target}`;
      setRoute(target);
      if (target === "copilot") setCopilotOpen(true);
      if (window.matchMedia("(max-width: 1023px)").matches && target !== "copilot") setCopilotOpen(false);
    });
  };

  const journeyCopy = useMemo(() => {
    if (!pulse.data) return null;
    const nowTitle = titleFor(pulse.data.now.activity.id, pulse.data.now.activity.title, locale);
    const nextTitle = titleFor(pulse.data.next.activity.id, pulse.data.next.activity.title, locale);
    return {
      nowTitle,
      nextTitle,
      riskLevelLabel:
        pulse.data.risk.level === "high" ? t("pulse.riskHigh") : pulse.data.risk.level === "low" ? t("pulse.riskLow") : t("pulse.riskWatch"),
      actionLabel: pick(PULSE_COPY.actionLabel, locale),
      nowNote: pick(PULSE_COPY.nowNote, locale),
      nextNote: pick(PULSE_COPY.nextNote, locale),
      riskTitle: pick(PULSE_COPY.riskTitle, locale),
      riskDetail: pick(PULSE_COPY.riskDetail, locale),
      actionReason: pick(PULSE_COPY.actionReason, locale),
    };
  }, [pulse.data, locale, t]);

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
    capability: "capability.title",
    "timeline-lab": "timeline.lab",
    me: "me.title",
  };

  return (
    <div className="app citynexus-experience" data-testid={testIds.appShell} data-runtime-status={runtimeStatus}>
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark" aria-hidden="true">◈</span>
          <div>
            <b>{t("app.brand")}</b>
            <small>{t("app.tagline")}</small>
          </div>
        </div>
        <div className="topbar__meta">
          <span className="pill">{t("app.reference")}</span>
          {runtimeStatus !== "ready" && <span className="pill pill--warn" data-testid="topbar-runtime-status">{t(`runtime.status.${runtimeStatus}.title`)}</span>}
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
            <span className="muted small">{adapter.mode} · {adapter.source}</span>
          </div>

          <RuntimeStatusBanner status={runtimeStatus} onAction={() => navigate("journey")} />

          <Suspense fallback={<section className="card" data-testid="route-loading">Loading route chunk…</section>}>
            {route === "journey" && pulse.data && journeyCopy && (
              <JourneyRoute pulse={pulse.data} copy={journeyCopy} items={timelineItems} onNavigate={navigate} />
            )}
            {route === "map" && <MapRoute onNavigate={navigate} />}
            {route === "recovery" && <RecoveryRoute />}
            {route === "capability" && <CapabilityRoute />}
            {route === "timeline-lab" && (
              <TimelineLabRoute count={Number(new URLSearchParams(window.location.search).get("events") ?? 1000)} />
            )}
          </Suspense>

          {route === "journey" && !pulse.data && <section className="card">Loading Journey Pulse…</section>}

          {route === "live" && (
            <section className="card">
              <span className="kicker">{t("nav.live")}</span>
              <h2>{pulse.data?.now.activity.title ?? "—"}</h2>
              <p className="muted">Server-derived runtime labels only. Recorded fixtures stay marked RECORDED_FIXTURE.</p>
              <button type="button" className="btn btn--primary" onClick={() => navigate("copilot")}>{t("copilot.open")}</button>
            </section>
          )}

          {route === "wallet" && (
            <section className="card">
              <span className="kicker">{t("wallet.kicker")}</span>
              <h2>{t("wallet.title")}</h2>
              <ul className="wallet-list">
                {WALLET_COPY.map((item) => (
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
              <p className="muted">The dock carries semantic interpretation, runtime truth, agent activity, proposal and approval.</p>
              <button type="button" className="btn btn--primary" onClick={() => setCopilotOpen(true)}>{t("copilot.open")}</button>
            </section>
          )}

          {["studio", "stay", "discover", "intelligence", "twin"].includes(route) && (
            <section className="card">
              <span className="kicker">{t(headingKeys[route])}</span>
              <h2>{t(headingKeys[route])}</h2>
              <p className="muted">Isolated reference placeholder. Technical internals stay behind disclosure.</p>
            </section>
          )}


          {route === "me" && (
            <section className="card">
              <span className="kicker">{t("me.kicker")}</span>
              <h2>{t("me.title")}</h2>
              <dl className="settings">
                <div><dt>{t("me.locale")}</dt><dd><LocaleToggle /></dd></div>
                <div><dt>{t("me.reducedMotion")}</dt><dd data-testid="reduced-motion-state">{document.documentElement.dataset.reducedMotion}</dd></div>
                <div><dt>Runtime reference state</dt><dd data-testid="runtime-state-value">{runtimeStatus}</dd></div>
              </dl>
              <div className="runtime-demo" role="group" aria-label="Runtime reference states">
                {(["ready", "hermes_unavailable", "deepseek_unavailable", "provider_unavailable", "offline_stale"] as RuntimeStatus[]).map((status) => (
                  <button key={status} type="button" className={`chip-btn${runtimeStatus === status ? " active" : ""}`} data-testid={`runtime-demo-${status}`} onClick={() => setRuntimeOverride(status)}>
                    {status === "ready" ? t("runtime.live") : t(`runtime.status.${status}.title`)}
                  </button>
                ))}
              </div>
            </section>
          )}
        </main>
        <CopilotDock open={route === "copilot" ? true : copilotOpen} onOpenChange={setCopilotOpen} onNavigate={navigate} isMobile={isMobile} />
      </div>
      <MobileNav active={route} onNavigate={navigate} />
      <footer className="footer">{t("shell.footer")}</footer>
    </div>
  );
}
