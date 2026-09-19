import { Suspense, lazy } from "react";
import { useLocale, useT } from "../i18n";
import { useJourneyPulse, useMapState, useRecoveryDiff } from "../adapters/ExperienceAdapterContext";
import { useOnlineStatus } from "../pwa/onlineStatus";
import { MapBottomSheet } from "../components/MapBottomSheet";
import { pick } from "../experience/locale";

const MapCanvas = lazy(() => import("../components/MapCanvas"));

export default function MapRoute({ onNavigate }: { onNavigate: (route: string) => void }) {
  const t = useT();
  const { locale } = useLocale();
  const { online } = useOnlineStatus();
  const pulse = useJourneyPulse();
  const mapState = useMapState();
  const recovery = useRecoveryDiff();

  const state = mapState.data;
  const now = pulse.data?.now;
  const next = pulse.data?.next;

  return (
    <div className="map-layout" data-testid="map-route">
      <Suspense fallback={<div className="map map--loading" data-testid="map-loading">Loading lazy map chunk…</div>}>
        <MapCanvas source={state?.source ?? "RECORDED_FIXTURE"} offline={!online} lastUpdated={state?.last_updated ?? null} />
      </Suspense>
      <MapBottomSheet>
        {(sheet) => (
          <>
            {sheet === "24" && (
              <div className="sheet-state" data-testid="sheet-content-24">
                <h3>{t("map.now")}</h3>
                <p>
                  <b>{now ? now.activity.title : "—"}</b> · {now?.time ?? "—"} · {now?.eta ?? "—"}
                </p>
                <h3>{t("map.nextActivity")}</h3>
                <p>
                  <b>{next ? next.activity.title : "—"}</b> · {next?.time ?? "—"}
                </p>
              </div>
            )}
            {sheet === "55" && (
              <div className="sheet-state" data-testid="sheet-content-55">
                <h3>{t("map.route")}</h3>
                <p>{state ? `${state.stops.length} stops · recorded route evidence` : "route unavailable"}</p>
                <h3>{t("map.transport")}</h3>
                <p>Walk 22 min · Metro line 3 · Walk 8 min · {state?.source ?? "OFFLINE"}</p>
                <h3>{t("map.nextCommitment")}</h3>
                <p>
                  <b>{next ? next.activity.title : "—"}</b> · C4 protected
                </p>
              </div>
            )}
            {sheet === "90" && (
              <div className="sheet-state" data-testid="sheet-content-90">
                <h3>{t("map.fullDetails")}</h3>
                <ol className="activity-list">
                  {(state?.stops ?? []).map((stop) => (
                    <li key={stop.id} className={stop.protected ? "protected" : undefined}>
                      <span>{stop.name}</span>
                      {stop.protected && <em>C4</em>}
                    </li>
                  ))}
                </ol>
                <h3>{t("map.recoveryDetails")}</h3>
                <p>{recovery.data ? pick(recovery.data.trigger, locale) : "recovery unavailable"}</p>
                <button type="button" className="btn btn--primary" onClick={() => onNavigate("recovery")}>
                  {t("pulse.openRecovery")}
                </button>
              </div>
            )}
          </>
        )}
      </MapBottomSheet>
    </div>
  );
}
