/**
 * CityNexus V19 Traveler Capability / Accessibility UI contract.
 *
 * UI-facing only. Nothing here writes localStorage or claims planning
 * authority. UNKNOWN != ACCESSIBLE: missing / unrecognised / stale /
 * conflicting evidence normalises to NEEDS_LIVE_EVIDENCE or CONFLICT.
 */

export const CAPABILITY_KINDS = [
  "HARD_ACCESSIBILITY_NEED",
  "CARE_REQUIREMENT",
  "PHYSICAL_LIMIT",
  "TRIP_CONTEXT",
  "SOFT_PREFERENCE",
  "PROTECTED_COMMITMENT",
  "UNKNOWN_CAPABILITY",
] as const;
export type CapabilityKind = (typeof CAPABILITY_KINDS)[number];

export const EVIDENCE_STATES = [
  "VERIFIED",
  "UNVERIFIED",
  "CONFLICT",
  "NEEDS_LIVE_EVIDENCE",
] as const;
export type CapabilityEvidenceState = (typeof EVIDENCE_STATES)[number];

export const CAPABILITY_STRENGTHS = ["HARD", "STRONG", "SOFT", "AMBIGUOUS"] as const;
export type CapabilityStrength = (typeof CAPABILITY_STRENGTHS)[number];

export const CAPABILITY_SCOPES = ["THIS_JOURNEY", "FUTURE_JOURNEYS", "TRAVELER"] as const;
export type CapabilityScope = (typeof CAPABILITY_SCOPES)[number];

export const CAPABILITY_SOURCES = [
  "TRAVELER_STATED",
  "COPILOT_DETECTED",
  "PROVIDER_EVIDENCE",
  "RECORDED_FIXTURE",
  "LEARNED_SOFT",
  "IMPORTED",
] as const;
export type CapabilitySource = (typeof CAPABILITY_SOURCES)[number];

export type ProvenanceKind = "LIVE" | "RECORDED_FIXTURE" | "LOCAL_UI_ONLY";

export interface CapabilityProvenance {
  kind: ProvenanceKind;
  label: string;
  sourceSystem: string;
  observedAt?: string | null;
  expiresAt?: string | null;
  providerKey?: string | null;
  recordedOn?: string | null;
  notes?: string;
}

export interface CapabilityEvidence {
  state: CapabilityEvidenceState;
  provenance: CapabilityProvenance;
  summary: string;
  detail?: string;
  lastVerifiedAt?: string | null;
  liveChecks?: string[];
  conflictsWith?: string[];
  facts?: Record<string, unknown>;
}

export type CapabilityConstraintOperator = "LTE" | "GTE" | "BETWEEN" | "REQUIRED" | "FORBIDDEN";

export interface CapabilityConstraint {
  key:
    | "max_walking_per_leg_m"
    | "max_continuous_walking_m"
    | "rest_frequency_min"
    | "nap_window"
    | "toilet_frequency_min"
    | "pace"
    | "quiet_sensory"
    | string;
  operator: CapabilityConstraintOperator;
  value: number | string | boolean | [number, number];
  unit?: string;
  hard: boolean;
}

export interface TravelerCapability {
  id: string;
  kind: CapabilityKind;
  label: string;
  description?: string;
  strength: CapabilityStrength;
  scope: CapabilityScope;
  source: CapabilitySource;
  sourceLabel: string;
  evidence: CapabilityEvidence;
  active: boolean;
  confirmed: boolean;
  explicit: boolean;
  learned: boolean;
  travelerStated: boolean;
  appliesToActivityIds?: string[];
  constraints?: CapabilityConstraint[];
  confidence?: number;
  strengthScore?: number;
  evidenceCount?: number;
  createdAt?: string;
  updatedAt?: string;
  extra?: Record<string, unknown>;
}

export type CapabilityImpactStatus =
  | "PRESERVED"
  | "IMPROVED"
  | "AT_RISK"
  | "VIOLATED"
  | "UNKNOWN";

export interface CapabilityImpact {
  id: string;
  capabilityId: string;
  capabilityLabel: string;
  kind: CapabilityKind;
  status: CapabilityImpactStatus;
  explanation: string;
  evidence: CapabilityEvidence;
  candidateId?: string;
  candidateLabel?: string;
  observedValue?: string;
  limitValue?: string;
  plannedValue?: string;
}

export interface CapabilityConflict {
  id: string;
  capabilityId: string;
  capabilityLabel: string;
  summary: string;
  severity: "INFO" | "WARNING" | "BLOCKING";
  evidence: CapabilityEvidence;
}

export interface CapabilityConfirmation {
  id: string;
  statement: string;
  detectedLabel: string;
  capability: TravelerCapability;
  ambiguous: boolean;
  ambiguityPrompt?: string;
  ambiguityOptions?: Array<{
    id: string;
    label: string;
    description?: string;
    capabilityPatch: Partial<TravelerCapability>;
  }>;
  selectedOptionId?: string;
}

export interface CapabilityConfirmationDecision {
  id: string;
  action: "CONFIRM" | "JOURNEY_ONLY" | "DISMISS" | "EDIT";
  capabilities: TravelerCapability[];
  acknowledgedFuturePersistence?: boolean;
}

export interface PlanCapabilityExplanationModel {
  candidateId: string;
  candidateLabel: string;
  candidateSubtitle?: string;
  selected: boolean;
  why: CapabilityImpact[];
  rejected: CapabilityImpact[];
  unknown: CapabilityEvidence[];
  protectedCommitments: Array<{
    id: string;
    label: string;
    level: string;
    preserved: boolean;
    detail?: string;
  }>;
  authority: "BACKEND_PLANNING" | "RECORDED_FIXTURE_REFERENCE" | "UI_LOCAL_DRAFT";
}

export interface RecoveryCapabilityDiffModel {
  journeyId: string;
  before: CapabilityImpact[];
  after: CapabilityImpact[];
  preserved: CapabilityImpact[];
  atRisk: CapabilityImpact[];
  evidenceGaps: CapabilityEvidence[];
  protectedCommitments: Array<{
    id: string;
    label: string;
    level: string;
    preserved: boolean;
    detail?: string;
  }>;
  authority: "BACKEND_PLANNING" | "RECORDED_FIXTURE_REFERENCE" | "UI_LOCAL_DRAFT";
}

export interface MobileCapabilityShieldModel {
  protectedCount: number;
  needs: TravelerCapability[];
  evidenceGap: {
    label: string;
    capabilityId: string;
    evidence: CapabilityEvidence;
  } | null;
  primaryActionLabel: string;
  onPrimaryAction?: () => void;
}

export interface CapabilityMapMarker {
  id: string;
  kind:
    | "VERIFIED_ACCESSIBILITY"
    | "UNKNOWN_ACCESSIBILITY"
    | "CONFLICT"
    | "REST_STOP"
    | "NAP_WINDOW"
    | "WALKING_LIMIT_WARNING"
    | "PROTECTED_COMMITMENT";
  label: string;
  detail?: string;
  evidence?: CapabilityEvidence;
  longitude?: number;
  latitude?: number;
}

export interface JourneySetupNeedsDraft {
  quickNeedIds: string[];
  advanced: {
    maxWalkingPerLegM?: number;
    maxContinuousWalkingM?: number;
    restFrequencyMin?: number;
    napWindow?: { start: string; end: string } | null;
    toiletFrequencyMin?: number;
    pace?: "RELAXED" | "BALANCED" | "BRISK";
    quietSensory?: boolean;
  };
  note?: string;
}

export const QUICK_NEEDS = [
  { id: "less_walking", labelZh: "少走路", labelEn: "Less walking", kind: "PHYSICAL_LIMIT" },
  { id: "wheelchair_access", labelZh: "无障碍/轮椅", labelEn: "Step-free / wheelchair", kind: "HARD_ACCESSIBILITY_NEED" },
  { id: "avoid_stairs", labelZh: "避免楼梯", labelEn: "Avoid stairs", kind: "HARD_ACCESSIBILITY_NEED" },
  { id: "stroller", labelZh: "婴儿车", labelEn: "Stroller", kind: "CARE_REQUIREMENT" },
  { id: "large_luggage", labelZh: "大件行李", labelEn: "Large luggage", kind: "TRIP_CONTEXT" },
  { id: "midday_rest", labelZh: "中午休息", labelEn: "Midday rest", kind: "CARE_REQUIREMENT" },
  { id: "baby_nap", labelZh: "婴儿午睡", labelEn: "Baby nap", kind: "CARE_REQUIREMENT" },
] as const satisfies ReadonlyArray<{
  id: string;
  labelZh: string;
  labelEn: string;
  kind: CapabilityKind;
}>;
export type QuickNeedId = (typeof QUICK_NEEDS)[number]["id"];

export interface CapabilityCopy {
  locale: "zh-CN" | "en";
  journeySetup: {
    title: string; lede: string; optional: string; quickTitle: string; quickHelp: string;
    advancedToggle: string; advancedHelp: string; maxWalkingPerLeg: string; maxContinuousWalking: string;
    restFrequency: string; napWindow: string; toiletFrequency: string; pace: string;
    paceRelaxed: string; paceBalanced: string; paceBrisk: string; quietSensory: string;
    note: string; notePlaceholder: string; save: string; clear: string; sourceNotice: string; activeSummary: string;
  };
  confirmation: {
    title: string; detected: string; classLabel: string; scopeLabel: string; sourceLabel: string; sourceValue: string;
    actions: { confirm: string; edit: string; journeyOnly: string; dismiss: string; cancel: string; saveEdit: string };
    ambiguity: string; hardPersistenceWarning: string; hardPersistenceAcknowledge: string;
    thisJourney: string; futureJourneys: string; travelerProfile: string;
    hard: string; strong: string; soft: string; ambiguous: string; sheetTitle: string;
    confirmed: string; journeyOnlyConfirmed: string; dismissed: string;
  };
  evidence: {
    verified: string; unverified: string; conflict: string; needsLiveEvidence: string;
    verifiedShort: string; unverifiedShort: string; conflictShort: string; needsLiveShort: string;
    details: string; unknownIsNotAccessible: string; recordedFixture: string; live: string;
  };
  plan: {
    title: string; whySelected: string; rejected: string; unknown: string; evidenceGap: string;
    capabilityPreserved: string; capabilityAtRisk: string; hardLimit: string; noRejections: string; noUnknowns: string;
    protectedCommitments: string; commitmentPreserved: string; commitmentAtRisk: string;
  };
  recovery: {
    title: string; before: string; after: string; preserved: string; atRisk: string; evidenceGaps: string;
    noAtRisk: string; noGaps: string;
  };
  twin: {
    title: string; explicitCapability: string; explicitPreference: string; learnedSoft: string;
    hardAccessibility: string; travelerStated: string; active: string; scope: string; evidence: string;
    learnedStrength: string; confidence: string; evidenceCount: string; noExplicit: string; noLearned: string;
    authorityNotice: string; explicit: string; learned: string;
  };
  mobile: {
    protectedTitle: string; protectedCount: string; noNeeds: string; evidenceGapTitle: string;
    evidenceGapNotVerified: string; primaryAction: string; openDetails: string;
  };
  map: {
    legendTitle: string; verified: string; unknown: string; conflict: string; restStop: string;
    napWindow: string; walkingLimit: string; protectedCommitment: string; mapSummary: string;
  };
}
