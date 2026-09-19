import { useEffect, useMemo, useState } from "react";
import { useLocale, useT } from "./i18n";
import { syncReducedMotionAttribute, withViewTransition } from "./motion";
import { testIds } from "./testids";
import type { AgentRunFixture } from "./types";
import { ACTIVITIES, JOURNEY, PULSE, PULSE_I18N, RECOVERY, WALLET_ITEMS, pick } from "./data/journey";
import { JourneyPulse } from "./components/JourneyPulse";
import { DesktopNav, LocaleToggle, MobileNav } from "./components/TravelerNav";
import { CopilotDock } from "./components/CopilotDock";
import { RecoveryDiff } from "./components/RecoveryDiff";
import { MapCanvas } from "./components/MapCanvas";
import { MapBottomSheet } from "./components/MapBottomSheet";

const ROUTES = ["today", "live", "map", "studio", "discover", "wallet", "copilot", "recovery", "me"] as const;
type RouteKey = (typeof ROUTES)[number];

function readRoute(): RouteKey {
  const hash = window.location.hash.replace(/^#\/?/, "");
  return (ROUTES as readonly string[]).includes(hash) ? (hash as RouteKey) : "today";
}

function findActivity(id: string) {
  return ACTIVITIES.find((activity) => activity.id === id) ?? ACTIVITIES[0];
}

export function App() {
  const t = useT();
  const { locale } = useLocale();
  const [route, setRoute] = useState<RouteKey>(readRoute);
  const [copilotOpen, setCopilotOpen] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia("(min-width: 1024px)").matches : false,
  );
  const [activeFixture, setActiveFixture] = useState<AgentRunFixture | null>(null);

  useEffect(() => syncReducedMotionAttribute(), []);

  useEffect(() => {
    const onHash = () => setRoute(readRoute());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const navigate = (next: string) => {
    const target = (ROUTES as readonly string[]).includes(next) ? (next as RouteKey) : "today";
    withViewTransition(() => {
      window.location.hash = `#/${target}`;
      setRoute(target);
      if (target === "copilot") setCopilotOpen(true);
      if (window.matchMedia("(max-width: 1023px)").matches && target !== "copilot") setCopilotOpen(false);
    });
  };

  const pulse = useMemo(() => {
    const nowLocalized = pick(findActivity(PULSE.now.activity.id).title, locale);
    const nextLocalized = pick(findActivity(PULSE.next.activity.id).title, locale);
    const riskLabel =
      PULSE.risk.level === "high"
        ? t("pulse.riskHigh")
        : PULSE.risk.level === "low"
          ? t("pulse.riskLow")
          : t("pulse.riskWatch");
    return { nowLocalized, nextLocalized, riskLabel };
  }, [locale, t]);

  const headingKeys: Record<RouteKey, string> = {
    today: "today.title",
    live: "nav.liveJourney",
    map: "map.title",
    studio: "nav.tripStudio",
    discover: "nav.tripStudio",
    wallet: "wallet.title",
    copilot: "copilot.title",
    recovery: "recovery.title",
    me: "me.title",
  };

  return (
    <div className="app" data-testid={testIds.appShell}>
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

          {route === "today" && (
            <>
              <p className="lede">{t("today.lede")}</p>
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
            </>
          )}

          {route === "live" && (
            <section className="card">
              <span className="kicker">{t("nav.liveJourney")}</span>
              <h2>{pulse.nowLocalized}</h2>
              <p className="muted">
                Server-derived runtime labels only. Reference fixture is marked RECORDED_FIXTURE; no LIVE badge is
                fabricated.
              </p>
              <button type="button" className="btn btn--primary" onClick={() => navigate("copilot")}>
                {t("copilot.open")}
              </button>
            </section>
          )}

          {route === "map" && (
            <div className="map-layout">
              <MapCanvas />
              <MapBottomSheet>
                <h3>{t("map.title")}</h3>
                <ol className="activity-list">
                  {ACTIVITIES.map((activity) => (
                    <li key={activity.id} className={activity.protected ? "protected" : undefined}>
                      <time>{activity.start_at.slice(11, 16)}</time>
                      <span>{pick(activity.title, locale)}</span>
                      <small>{pick(activity.place, locale)}</small>
                      {activity.protected && <em>C4</em>}
                    </li>
                  ))}
                </ol>
              </MapBottomSheet>
            </div>
          )}

          {(route === "studio" || route === "discover") && (
            <section className="card">
              <span className="kicker">{t("nav.plan")}</span>
              <h2>{t("nav.tripStudio")}</h2>
              <p className="muted">
                Isolated reference placeholder. The merge guide keeps Codex's authoritative Trip Studio untouched.
              </p>
            </section>
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
                The persistent dock is open. On mobile it becomes a bottom sheet above the traveler navigation.
              </p>
              <button type="button" className="btn btn--primary" onClick={() => setCopilotOpen(true)}>
                {t("copilot.open")}
              </button>
            </section>
          )}

          {route === "recovery" && <RecoveryDiff proposal={RECOVERY} />}

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
              </dl>
            </section>
          )}
        </main>
        <CopilotDock
          open={route === "copilot" ? true : copilotOpen}
          onOpenChange={setCopilotOpen}
          onNavigate={navigate}
          activeFixture={activeFixture}
          onFixtureChange={setActiveFixture}
        />
      </div>
      <MobileNav active={route} onNavigate={navigate} />
      <footer className="footer">{t("shell.footer")}</footer>
    </div>
  );
}
