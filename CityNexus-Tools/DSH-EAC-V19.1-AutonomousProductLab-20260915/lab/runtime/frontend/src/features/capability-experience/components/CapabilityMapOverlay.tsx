import { useId } from "react";
import type { CapabilityMapMarker } from "../types";
import { capabilityCopy } from "../copy";
import { EvidenceBadge } from "./EvidenceBadge";
import "../styles/capability-experience.css";

function markerVisual(kind: CapabilityMapMarker["kind"], copy: ReturnType<typeof capabilityCopy>) {
  switch (kind) {
    case "VERIFIED_ACCESSIBILITY":
      return { glyph: "♿", label: copy.map.verified, tone: "verified" };
    case "UNKNOWN_ACCESSIBILITY":
      return { glyph: "?", label: copy.map.unknown, tone: "unknown" };
    case "CONFLICT":
      return { glyph: "!", label: copy.map.conflict, tone: "conflict" };
    case "REST_STOP":
      return { glyph: "R", label: copy.map.restStop, tone: "rest" };
    case "NAP_WINDOW":
      return { glyph: "Zz", label: copy.map.napWindow, tone: "rest" };
    case "WALKING_LIMIT_WARNING":
      return { glyph: "△", label: copy.map.walkingLimit, tone: "warning" };
    case "PROTECTED_COMMITMENT":
      return { glyph: "C4", label: copy.map.protectedCommitment, tone: "commitment" };
    default:
      return { glyph: "?", label: copy.map.unknown, tone: "unknown" };
  }
}

export function CapabilityMapMarker({
  marker,
  locale = "zh-CN",
  onSelect,
}: {
  marker: CapabilityMapMarker;
  locale?: "zh-CN" | "en";
  onSelect?: (marker: CapabilityMapMarker) => void;
}) {
  const copy = capabilityCopy(locale);
  const visual = markerVisual(marker.kind, copy);
  const label = `${visual.label}: ${marker.label}${marker.detail ? `. ${marker.detail}` : ""}`;
  const className = `cne-map-marker cne-map-marker--${visual.tone}`;
  const content = <><span aria-hidden="true" className="cne-map-marker__glyph">{visual.glyph}</span><span className="cne-map-marker__label">{marker.label}</span></>;
  if (onSelect) {
    return <button type="button" className={className} aria-label={label} data-marker-kind={marker.kind} onClick={() => onSelect(marker)}>{content}</button>;
  }
  return <span className={className} role="img" aria-label={label} data-marker-kind={marker.kind}>{content}</span>;
}

export function CapabilityMapLegend({ locale = "zh-CN" }: { locale?: "zh-CN" | "en" }) {
  const copy = capabilityCopy(locale);
  const kinds: CapabilityMapMarker["kind"][] = [
    "VERIFIED_ACCESSIBILITY",
    "UNKNOWN_ACCESSIBILITY",
    "CONFLICT",
    "REST_STOP",
    "NAP_WINDOW",
    "WALKING_LIMIT_WARNING",
    "PROTECTED_COMMITMENT",
  ];
  return (
    <section className="cne-map-legend" aria-labelledby="cne-map-legend-title" data-testid="capability-map-legend">
      <h3 id="cne-map-legend-title">{copy.map.legendTitle}</h3>
      <ul>
        {kinds.map((kind) => {
          const visual = markerVisual(kind, copy);
          return <li key={kind}><span className={`cne-map-legend__swatch cne-map-legend__swatch--${visual.tone}`} aria-hidden="true">{visual.glyph}</span><span>{visual.label}</span></li>;
        })}
      </ul>
      <p>{copy.map.mapSummary}</p>
    </section>
  );
}

export function CapabilityMapOverlay({
  markers,
  locale = "zh-CN",
  onSelect,
}: {
  markers: CapabilityMapMarker[];
  locale?: "zh-CN" | "en";
  onSelect?: (marker: CapabilityMapMarker) => void;
}) {
  const copy = capabilityCopy(locale);
  const titleId = useId();
  return (
    <section className="cne-map" aria-labelledby={titleId} data-testid="capability-map-overlay">
      <h3 id={titleId}>{locale === "zh-CN" ? "地图证据标记" : "Map evidence markers"}</h3>
      <div className="cne-map__canvas" role="group" aria-label={copy.map.mapSummary}>
        {markers.map((marker, index) => (
          <div
            key={marker.id}
            className="cne-map__pin"
            style={{ left: `${8 + (index % 3) * 30}%`, top: `${14 + Math.floor(index / 3) * 28}%` }}
          >
            <CapabilityMapMarker marker={marker} locale={locale} onSelect={onSelect} />
            {marker.evidence ? <EvidenceBadge state={marker.evidence.state} evidence={marker.evidence} locale={locale} /> : null}
          </div>
        ))}
      </div>
      <CapabilityMapLegend locale={locale} />
    </section>
  );
}