import { JourneyPulse } from "../components/JourneyPulse";
import { TodayTimeline, type TodayTimelineItem } from "../components/TodayTimeline";
import type { PulseState } from "../types";
import type { LocalizedCopy } from "../types";

export interface JourneyRouteCopy {
  nowTitle: string;
  nextTitle: string;
  riskLevelLabel: string;
  actionLabel: string;
  nowNote: string;
  nextNote: string;
  riskTitle: string;
  riskDetail: string;
  actionReason: string;
}

export default function JourneyRoute({
  pulse,
  copy,
  items,
  onNavigate,
}: {
  pulse: PulseState;
  copy: JourneyRouteCopy;
  items: TodayTimelineItem[];
  onNavigate: (route: string) => void;
  fallbackCopy?: LocalizedCopy;
}) {
  return (
    <>
      <p className="lede">A calm, evidence-backed day. Open the map only when you need it.</p>
      <JourneyPulse
        pulse={pulse}
        nowTitle={copy.nowTitle}
        nextTitle={copy.nextTitle}
        riskLevelLabel={copy.riskLevelLabel}
        actionLabel={copy.actionLabel}
        nowNote={copy.nowNote}
        nextNote={copy.nextNote}
        riskTitle={copy.riskTitle}
        riskDetail={copy.riskDetail}
        actionReason={copy.actionReason}
        onPrimaryAction={() => onNavigate("recovery")}
      />
      <TodayTimeline items={items} />
      <section className="card" data-testid="journey-map-teaser">
        <span className="kicker">LIVE MAP</span>
        <h2>MapLibre is lazy-loaded only on the Map route</h2>
        <p className="muted">
          This Journey screen never initializes WebGL. The map chunk and maplibre-gl are requested only when
          you open Map.
        </p>
        <button type="button" className="btn btn--primary" onClick={() => onNavigate("map")}>
          Open map
        </button>
      </section>
      <p className="muted small">Technical detail stays collapsed until you need it.</p>
    </>
  );
}
