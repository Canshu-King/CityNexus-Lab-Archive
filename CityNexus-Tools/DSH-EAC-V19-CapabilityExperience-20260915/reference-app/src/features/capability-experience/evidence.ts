import type { CapabilityCopy, CapabilityEvidence, CapabilityEvidenceState, ProvenanceKind } from "./types";

export interface EvidenceVisual {
  state: CapabilityEvidenceState;
  label: string;
  shortLabel: string;
  glyph: string;
  tone: "verified" | "unknown" | "conflict" | "live";
  ariaDescription: string;
}

export function evidenceVisual(state: CapabilityEvidenceState, copy: CapabilityCopy): EvidenceVisual {
  switch (state) {
    case "VERIFIED":
      return {
        state,
        label: copy.evidence.verified,
        shortLabel: copy.evidence.verifiedShort,
        glyph: "✓",
        tone: "verified",
        ariaDescription: copy.evidence.verified,
      };
    case "CONFLICT":
      return {
        state,
        label: copy.evidence.conflict,
        shortLabel: copy.evidence.conflictShort,
        glyph: "!",
        tone: "conflict",
        ariaDescription: copy.evidence.conflict,
      };
    case "UNVERIFIED":
      return {
        state,
        label: copy.evidence.unverified,
        shortLabel: copy.evidence.unverifiedShort,
        glyph: "?",
        tone: "unknown",
        ariaDescription: copy.evidence.unverified,
      };
    case "NEEDS_LIVE_EVIDENCE":
      return {
        state,
        label: copy.evidence.needsLiveEvidence,
        shortLabel: copy.evidence.needsLiveShort,
        glyph: "⌛",
        tone: "live",
        ariaDescription: copy.evidence.needsLiveEvidence,
      };
    default:
      // Unknown future evidence states are never promoted to VERIFIED.
      return {
        state: "NEEDS_LIVE_EVIDENCE",
        label: copy.evidence.needsLiveEvidence,
        shortLabel: copy.evidence.needsLiveShort,
        glyph: "⌛",
        tone: "live",
        ariaDescription: copy.evidence.needsLiveEvidence,
      };
  }
}

export function provenanceKindLabel(kind: ProvenanceKind, copy: CapabilityCopy): string {
  if (kind === "LIVE") return copy.evidence.live;
  if (kind === "RECORDED_FIXTURE") return copy.evidence.recordedFixture;
  return "LOCAL_UI_ONLY";
}

export function makeEvidence(
  state: CapabilityEvidenceState,
  summary: string,
  provenance: CapabilityEvidence["provenance"],
  extras: Partial<CapabilityEvidence> = {},
): CapabilityEvidence {
  return { state, summary, provenance, ...extras };
}

export function makeRecordedEvidence(summary: string, extras: Partial<CapabilityEvidence> = {}): CapabilityEvidence {
  return makeEvidence("NEEDS_LIVE_EVIDENCE", summary, {
    kind: "RECORDED_FIXTURE",
    label: "RECORDED_FIXTURE",
    sourceSystem: "citynexus_v19_capability_fixture",
    recordedOn: "2026-09-15",
  }, extras);
}

export function makeLiveEvidence(summary: string, sourceSystem: string, extras: Partial<CapabilityEvidence> = {}): CapabilityEvidence {
  return makeEvidence("NEEDS_LIVE_EVIDENCE", summary, {
    kind: "LIVE",
    label: "LIVE",
    sourceSystem,
    observedAt: new Date().toISOString(),
  }, extras);
}

export function makeUiOnlyEvidence(summary: string, extras: Partial<CapabilityEvidence> = {}): CapabilityEvidence {
  return makeEvidence("NEEDS_LIVE_EVIDENCE", summary, {
    kind: "LOCAL_UI_ONLY",
    label: "LOCAL_UI_ONLY",
    sourceSystem: "capability_experience_ui",
  }, { liveChecks: ["Backend capability contract has not returned this evidence yet."], ...extras });
}

export function isUnknownEvidence(evidence: CapabilityEvidence): boolean {
  return evidence.state === "UNVERIFIED" || evidence.state === "NEEDS_LIVE_EVIDENCE";
}

export function isEvidenceGap(evidence: CapabilityEvidence): boolean {
  return evidence.state !== "VERIFIED";
}

export function evidenceNeedsLiveCheck(evidence: CapabilityEvidence): boolean {
  return evidence.state === "NEEDS_LIVE_EVIDENCE" || evidence.state === "UNVERIFIED";
}

export function evidenceAriaLabel(evidence: CapabilityEvidence, copy: CapabilityCopy): string {
  const visual = evidenceVisual(evidence.state, copy);
  return `${visual.label}: ${evidence.summary}`;
}

export function capabilityKindLabel(kind: string, copy: CapabilityCopy): string {
  const zh = copy.locale === "zh-CN";
  switch (kind) {
    case "HARD_ACCESSIBILITY_NEED":
      return zh ? "硬性无障碍需求" : "Hard accessibility need";
    case "CARE_REQUIREMENT":
      return zh ? "照护要求" : "Care requirement";
    case "PHYSICAL_LIMIT":
      return zh ? "身体限制" : "Physical limit";
    case "TRIP_CONTEXT":
      return zh ? "行程背景" : "Trip context";
    case "SOFT_PREFERENCE":
      return zh ? "软偏好" : "Soft preference";
    case "PROTECTED_COMMITMENT":
      return zh ? "受保护承诺" : "Protected commitment";
    default:
      return zh ? "未知能力类型" : "Unknown capability type";
  }
}

export function strengthLabel(strength: string, copy: CapabilityCopy): string {
  switch (strength) {
    case "HARD":
      return copy.confirmation.hard;
    case "STRONG":
      return copy.confirmation.strong;
    case "SOFT":
      return copy.confirmation.soft;
    default:
      return copy.confirmation.ambiguous;
  }
}

export function scopeLabel(scope: string, copy: CapabilityCopy): string {
  switch (scope) {
    case "THIS_JOURNEY":
      return copy.confirmation.thisJourney;
    case "FUTURE_JOURNEYS":
      return copy.confirmation.futureJourneys;
    case "TRAVELER":
      return copy.confirmation.travelerProfile;
    default:
      return copy.confirmation.thisJourney;
  }
}

export function impactStatusLabel(status: string, copy: CapabilityCopy): string {
  const zh = copy.locale === "zh-CN";
  switch (status) {
    case "PRESERVED":
      return zh ? "已保护" : "Preserved";
    case "IMPROVED":
      return zh ? "改善" : "Improved";
    case "AT_RISK":
      return zh ? "有风险" : "At risk";
    case "VIOLATED":
      return zh ? "被违反" : "Violated";
    default:
      return zh ? "未知" : "Unknown";
  }
}

export function capabilityLabel(capability: { label: string; extra?: Record<string, unknown> }, locale: "zh-CN" | "en"): string {
  if (locale === "en") {
    const english = capability.extra?.labelEn ?? capability.extra?.label_en;
    if (typeof english === "string" && english.trim()) return english;
  }
  return capability.label;
}

export function capabilityDescription(capability: { description?: string; extra?: Record<string, unknown> }, locale: "zh-CN" | "en"): string | undefined {
  if (locale === "en") {
    const english = capability.extra?.descriptionEn ?? capability.extra?.description_en;
    if (typeof english === "string" && english.trim()) return english;
  }
  return capability.description;
}
