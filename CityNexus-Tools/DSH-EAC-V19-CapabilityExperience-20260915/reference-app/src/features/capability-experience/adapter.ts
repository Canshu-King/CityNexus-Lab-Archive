import type {
  CapabilityConfirmation,
  CapabilityConstraint,
  CapabilityEvidence,
  CapabilityEvidenceState,
  CapabilityImpact,
  CapabilityKind,
  CapabilityScope,
  CapabilitySource,
  CapabilityStrength,
  JourneySetupNeedsDraft,
  PlanCapabilityExplanationModel,
  ProvenanceKind,
  QuickNeedId,
  RecoveryCapabilityDiffModel,
  TravelerCapability,
} from "./types";
import { EVIDENCE_STATES, QUICK_NEEDS } from "./types";
import { makeEvidence, makeLiveEvidence, makeRecordedEvidence, makeUiOnlyEvidence } from "./evidence";

export class CapabilityAdapterNotConfiguredError extends Error {
  readonly code = "CAPABILITY_CONTRACT_NOT_AVAILABLE";
  constructor(message = "Capability backend contract is not available; use RECORDED_FIXTURE explicitly.") {
    super(message);
    this.name = "CapabilityAdapterNotConfiguredError";
  }
}

export interface CapabilityDataSource {
  readonly sourceKind: ProvenanceKind;
  fetchCapabilities(travelerId: string): Promise<TravelerCapability[]>;
  fetchPlanExplanation(journeyId: string): Promise<PlanCapabilityExplanationModel>;
  fetchRecoveryDiff(journeyId: string): Promise<RecoveryCapabilityDiffModel>;
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

export function asNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

export function asBoolean(value: unknown, fallback = false): boolean {
  return typeof value === "boolean" ? value : fallback;
}

export function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

export function asRecord(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

const EVIDENCE_STATE_ALIASES: Record<string, CapabilityEvidenceState> = {
  verified: "VERIFIED",
  live_verified: "VERIFIED",
  provider_verified: "VERIFIED",
  accessible: "VERIFIED",
  unverified: "UNVERIFIED",
  not_verified: "UNVERIFIED",
  unknown: "NEEDS_LIVE_EVIDENCE",
  missing: "NEEDS_LIVE_EVIDENCE",
  needs_live_evidence: "NEEDS_LIVE_EVIDENCE",
  needs_live: "NEEDS_LIVE_EVIDENCE",
  stale: "NEEDS_LIVE_EVIDENCE",
  expired: "NEEDS_LIVE_EVIDENCE",
  conflict: "CONFLICT",
  conflicting: "CONFLICT",
  contradicted: "CONFLICT",
};

export function normalizeEvidenceState(value: unknown): CapabilityEvidenceState {
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase().replace(/[\s-]+/g, "_");
    if ((EVIDENCE_STATES as readonly string[]).includes(value.trim().toUpperCase())) {
      return value.trim().toUpperCase() as CapabilityEvidenceState;
    }
    return EVIDENCE_STATE_ALIASES[normalized] ?? "NEEDS_LIVE_EVIDENCE";
  }
  if (isRecord(value)) {
    return normalizeEvidenceState(value.state ?? value.status ?? value.evidence_state ?? value.evidenceStatus);
  }
  return "NEEDS_LIVE_EVIDENCE";
}

const KIND_ALIASES: Record<string, CapabilityKind> = {
  hard_accessibility_need: "HARD_ACCESSIBILITY_NEED",
  accessibility: "HARD_ACCESSIBILITY_NEED",
  wheelchair: "HARD_ACCESSIBILITY_NEED",
  step_free: "HARD_ACCESSIBILITY_NEED",
  care_requirement: "CARE_REQUIREMENT",
  care: "CARE_REQUIREMENT",
  physical_limit: "PHYSICAL_LIMIT",
  mobility_limit: "PHYSICAL_LIMIT",
  trip_context: "TRIP_CONTEXT",
  soft_preference: "SOFT_PREFERENCE",
  preference: "SOFT_PREFERENCE",
  protected_commitment: "PROTECTED_COMMITMENT",
  commitment: "PROTECTED_COMMITMENT",
};

export function normalizeKind(value: unknown): CapabilityKind {
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase().replace(/[\s-]+/g, "_");
    const direct = normalized.toUpperCase() as CapabilityKind;
    if (direct === "UNKNOWN_CAPABILITY") return direct;
    if (KIND_ALIASES[normalized]) return KIND_ALIASES[normalized];
  }
  return "UNKNOWN_CAPABILITY";
}

export function normalizeStrength(value: unknown): CapabilityStrength {
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase().replace(/[\s-]+/g, "_");
    if (normalized === "hard" || normalized === "hard_accessibility_need") return "HARD";
    if (normalized === "strong" || normalized === "care_requirement") return "STRONG";
    if (normalized === "soft" || normalized === "preference") return "SOFT";
    if (normalized === "ambiguous" || normalized === "needs_confirmation") return "AMBIGUOUS";
  }
  if (isRecord(value)) {
    if (asBoolean(value.hard, false)) return "HARD";
    return normalizeStrength(value.strength ?? value.class ?? value.level);
  }
  return "AMBIGUOUS";
}

export function normalizeScope(value: unknown): CapabilityScope {
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase().replace(/[\s-]+/g, "_");
    if (["this_journey", "journey", "current_journey"].includes(normalized)) return "THIS_JOURNEY";
    if (["future_journeys", "future", "standing"].includes(normalized)) return "FUTURE_JOURNEYS";
    if (["traveler", "profile", "traveler_profile", "global"].includes(normalized)) return "TRAVELER";
  }
  return "THIS_JOURNEY";
}

export function normalizeSource(value: unknown): CapabilitySource {
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase().replace(/[\s-]+/g, "_");
    if (["traveler_stated", "user_stated", "explicit"].includes(normalized)) return "TRAVELER_STATED";
    if (["copilot_detected", "detected", "ai_detected"].includes(normalized)) return "COPILOT_DETECTED";
    if (["provider_evidence", "provider", "verified_provider"].includes(normalized)) return "PROVIDER_EVIDENCE";
    if (["recorded_fixture", "fixture"].includes(normalized)) return "RECORDED_FIXTURE";
    if (["learned_soft", "learned"].includes(normalized)) return "LEARNED_SOFT";
  }
  return "IMPORTED";
}

export function adaptEvidence(raw: unknown, fallbackSummary: string): CapabilityEvidence {
  if (typeof raw === "string") {
    const state = normalizeEvidenceState(raw);
    return makeEvidence(state, fallbackSummary, {
      kind: "LOCAL_UI_ONLY",
      label: "LOCAL_UI_ONLY",
      sourceSystem: "capability_experience_ui",
    });
  }
  const record = asRecord(raw);
  const state = normalizeEvidenceState(record.state ?? record.status ?? record.evidence_state ?? raw);
  const summary = asString(record.summary ?? record.label, fallbackSummary);
  const provenanceCandidate = isRecord(record.provenance) ? record.provenance : record;
  const sourceKind = asString(provenanceCandidate.kind ?? provenanceCandidate.source_kind, "LOCAL_UI_ONLY");
  const provenanceKind: ProvenanceKind =
    sourceKind === "LIVE" || sourceKind === "RECORDED_FIXTURE" || sourceKind === "LOCAL_UI_ONLY"
      ? sourceKind
      : "LOCAL_UI_ONLY";
  const evidence: CapabilityEvidence = {
    state,
    summary,
    provenance: {
      kind: provenanceKind,
      label: asString(provenanceCandidate.label, provenanceKind),
      sourceSystem: asString(provenanceCandidate.source_system ?? provenanceCandidate.sourceSystem, "unknown"),
      observedAt: asString(provenanceCandidate.observed_at ?? provenanceCandidate.observedAt, "") || null,
      expiresAt: asString(provenanceCandidate.expires_at ?? provenanceCandidate.expiresAt, "") || null,
      providerKey: asString(provenanceCandidate.provider_key ?? provenanceCandidate.providerKey, "") || null,
      recordedOn: asString(provenanceCandidate.recorded_on ?? provenanceCandidate.recordedOn, "") || null,
      notes: asString(provenanceCandidate.notes, "") || undefined,
    },
  };
  const detail = asString(record.detail ?? record.description, "");
  if (detail) evidence.detail = detail;
  const lastVerifiedAt = asString(record.last_verified_at ?? record.lastVerifiedAt, "");
  if (lastVerifiedAt) evidence.lastVerifiedAt = lastVerifiedAt;
  const liveChecks = asArray(record.live_checks ?? record.liveChecks).filter((item): item is string => typeof item === "string");
  if (liveChecks.length) evidence.liveChecks = liveChecks;
  const conflictsWith = asArray(record.conflicts_with ?? record.conflictsWith).filter((item): item is string => typeof item === "string");
  if (conflictsWith.length) evidence.conflictsWith = conflictsWith;
  if (isRecord(record.facts)) evidence.facts = record.facts;
  else if (isRecord(record.extra)) evidence.facts = record.extra;
  return evidence;
}

export function adaptCapability(raw: unknown, index = 0, defaults: Partial<TravelerCapability> = {}): TravelerCapability {
  const record = isRecord(raw) ? raw : {};
  const source = normalizeSource(record.source ?? record.source_type ?? defaults.source);
  const kind = normalizeKind(record.kind ?? record.capability_kind ?? record.type ?? defaults.kind);
  const strength = normalizeStrength(record.strength ?? record.class ?? record.level ?? record.priority ?? defaults.strength);
  const scope = normalizeScope(record.scope ?? record.applies_to ?? defaults.scope);
  const explicit = asBoolean(record.explicit, defaults.explicit ?? source === "TRAVELER_STATED");
  const learned = asBoolean(record.learned, defaults.learned ?? source === "LEARNED_SOFT");
  const travelerStated = asBoolean(record.traveler_stated ?? record.travelerStated, defaults.travelerStated ?? explicit);
  const label = asString(record.label ?? record.name ?? record.dimension ?? defaults.label, `Capability ${index + 1}`);
  const id = asString(record.id ?? record.capability_id ?? record.dimension, defaults.id ?? `capability-${index + 1}`);
  const evidence = adaptEvidence(
    record.evidence ?? record.provenance ?? record.capability_evidence,
    asString(record.evidence_summary, label),
  );
  const capability: TravelerCapability = {
    id,
    kind,
    label,
    strength,
    scope,
    source,
    sourceLabel: asString(record.source_label ?? record.sourceLabel, source),
    evidence,
    active: asBoolean(record.active, defaults.active ?? true),
    confirmed: asBoolean(record.confirmed, defaults.confirmed ?? false),
    explicit,
    learned,
    travelerStated,
  };
  const description = asString(record.description, "");
  if (description) capability.description = description;
  const appliesTo = asArray(record.applies_to_activity_ids ?? record.appliesToActivityIds).filter(
    (item): item is string => typeof item === "string",
  );
  if (appliesTo.length) capability.appliesToActivityIds = appliesTo;
  const rawConstraints = asArray(record.constraints).filter(isRecord);
  if (rawConstraints.length) {
    capability.constraints = rawConstraints.map((item) => {
      const constraint: CapabilityConstraint = {
        key: asString(item.key ?? item.name, "unknown_constraint"),
        operator: (["LTE", "GTE", "BETWEEN", "REQUIRED", "FORBIDDEN"].includes(String(item.operator).toUpperCase())
          ? String(item.operator).toUpperCase()
          : "REQUIRED") as CapabilityConstraint["operator"],
        value: (typeof item.value === "number" || typeof item.value === "string" || typeof item.value === "boolean" || Array.isArray(item.value))
          ? (item.value as CapabilityConstraint["value"])
          : true,
        hard: asBoolean(item.hard, strength === "HARD"),
      };
      const unit = asString(item.unit, "");
      if (unit) constraint.unit = unit;
      return constraint;
    });
  }
  const confidence = asNumber(record.confidence);
  if (learned && confidence !== undefined) capability.confidence = confidence;
  const strengthScore = asNumber(record.strength_score ?? record.strengthScore);
  if (learned && strengthScore !== undefined) capability.strengthScore = strengthScore;
  const evidenceCount = asNumber(record.evidence_count ?? record.evidenceCount);
  if (evidenceCount !== undefined) capability.evidenceCount = evidenceCount;
  const createdAt = asString(record.created_at ?? record.createdAt, "");
  if (createdAt) capability.createdAt = createdAt;
  const updatedAt = asString(record.updated_at ?? record.updatedAt, "");
  if (updatedAt) capability.updatedAt = updatedAt;
  const extra = Object.fromEntries(Object.entries(record).filter(([key]) => !KNOWN_CAPABILITY_KEYS.has(key)));
  if (Object.keys(extra).length) capability.extra = extra;
  return capability;
}

const KNOWN_CAPABILITY_KEYS = new Set([
  "id", "capability_id", "dimension", "kind", "capability_kind", "type", "strength", "class", "level", "priority",
  "scope", "applies_to", "explicit", "learned", "traveler_stated", "travelerStated", "label", "name",
  "source", "source_type", "source_label", "sourceLabel", "evidence", "provenance", "capability_evidence",
  "evidence_summary", "active", "confirmed", "description", "applies_to_activity_ids", "appliesToActivityIds",
  "constraints", "confidence", "strength_score", "strengthScore", "evidence_count", "evidenceCount",
  "created_at", "createdAt", "updated_at", "updatedAt",
]);

export function adaptCapabilities(raw: unknown, defaults: Partial<TravelerCapability> = {}): TravelerCapability[] {
  return asArray(raw).map((item, index) => adaptCapability(item, index, defaults));
}

export function adaptTravelerTwinEvidence(twin: unknown): TravelerCapability[] {
  const record = asRecord(twin);
  const output: TravelerCapability[] = [];
  asArray(record.explicit_preferences).forEach((item, index) => {
    const raw = asRecord(item);
    const label = asString(raw.dimension ?? raw.label ?? raw.name, `Explicit preference ${index + 1}`);
    output.push(
      adaptCapability(
        {
          id: asString(raw.id, `twin-explicit-${index + 1}`),
          label,
          kind: "SOFT_PREFERENCE",
          strength: "STRONG",
          scope: "TRAVELER",
          source: "TRAVELER_STATED",
          explicit: true,
          traveler_stated: true,
          active: true,
          confirmed: true,
          evidence: {
            state: "UNVERIFIED",
            summary: `Traveler Twin explicit dimension: ${label}; planning evidence still requires the capability contract.`,
            provenance: {
              kind: "LIVE",
              label: "LIVE",
              sourceSystem: "traveler_twin_explicit",
              observedAt: asString(record.updated_at, "") || null,
            },
          },
        },
        index,
      ),
    );
  });
  asArray(record.learned_soft_preferences).forEach((item, index) => {
    const raw = asRecord(item);
    const label = asString(raw.dimension ?? raw.label ?? raw.name, `Learned soft preference ${index + 1}`);
    output.push(
      adaptCapability(
        {
          id: asString(raw.id, `twin-learned-${index + 1}`),
          label,
          kind: "SOFT_PREFERENCE",
          strength: "SOFT",
          scope: "TRAVELER",
          source: "LEARNED_SOFT",
          learned: true,
          active: true,
          confidence: asNumber(raw.confidence),
          strength_score: asNumber(raw.strength),
          evidence_count: asNumber(raw.evidence_count),
          evidence: {
            state: "UNVERIFIED",
            summary: asString(raw.explanation, `Learned soft preference: ${label}`),
            provenance: {
              kind: "LIVE",
              label: "LIVE",
              sourceSystem: "traveler_twin_learned_soft",
              observedAt: asString(raw.last_evidence_at, "") || null,
              expiresAt: asString(raw.expires_at, "") || null,
            },
          },
        },
        index,
      ),
    );
  });
  return output;
}

export function adaptDetectedNeed(raw: unknown, index = 0): CapabilityConfirmation {
  const record = asRecord(raw);
  const ambiguous = asBoolean(record.ambiguous ?? record.needs_confirmation, false);
  const label = asString(record.detected_label ?? record.label ?? record.name, `Detected need ${index + 1}`);
  const strength = ambiguous ? "AMBIGUOUS" : normalizeStrength(record.strength ?? record.class ?? record.level);
  const capability = adaptCapability(
    {
      id: asString(record.id, `detected-${index + 1}`),
      label,
      kind: normalizeKind(record.kind ?? record.capability_kind),
      strength,
      scope: normalizeScope(record.scope),
      source: "COPILOT_DETECTED",
      source_label: "You told CityNexus",
      explicit: false,
      traveler_stated: true,
      confirmed: false,
      active: false,
      evidence: record.evidence ?? {
        state: "NEEDS_LIVE_EVIDENCE",
        summary: "Copilot language detection is not planning evidence.",
        provenance: {
          kind: "LOCAL_UI_ONLY",
          label: "COPILOT_DETECTION",
          sourceSystem: "copilot",
        },
      },
    },
    index,
  );
  return {
    id: capability.id,
    statement: asString(record.statement ?? record.user_text, ""),
    detectedLabel: label,
    capability,
    ambiguous,
    ambiguityPrompt: asString(record.ambiguity_prompt ?? record.ambiguityPrompt, "") || undefined,
    ambiguityOptions: asArray(record.ambiguity_options ?? record.ambiguityOptions)
      .filter(isRecord)
      .map((item, optionIndex) => ({
        id: asString(item.id, `option-${optionIndex + 1}`),
        label: asString(item.label, `Option ${optionIndex + 1}`),
        description: asString(item.description, "") || undefined,
        capabilityPatch: isRecord(item.capability_patch) ? (item.capability_patch as Partial<TravelerCapability>) : {},
      })),
  };
}

export function adaptDetectedNeeds(raw: unknown): CapabilityConfirmation[] {
  return asArray(raw).map((item, index) => adaptDetectedNeed(item, index));
}

export function adaptImpact(raw: unknown, index = 0): CapabilityImpact {
  const record = asRecord(raw);
  const statusRaw = asString(record.status ?? record.impact, "UNKNOWN").toUpperCase();
  const status = (["PRESERVED", "IMPROVED", "AT_RISK", "VIOLATED", "UNKNOWN"].includes(statusRaw)
    ? statusRaw
    : "UNKNOWN") as CapabilityImpact["status"];
  return {
    id: asString(record.id, `impact-${index + 1}`),
    capabilityId: asString(record.capability_id ?? record.capabilityId, `impact-capability-${index + 1}`),
    capabilityLabel: asString(record.capability_label ?? record.label, `Capability ${index + 1}`),
    kind: normalizeKind(record.kind),
    status,
    explanation: asString(record.explanation ?? record.reason, ""),
    evidence: adaptEvidence(record.evidence, asString(record.explanation, "Evidence state unknown")),
    candidateId: asString(record.candidate_id ?? record.candidateId, "") || undefined,
    candidateLabel: asString(record.candidate_label ?? record.candidateLabel, "") || undefined,
    observedValue: asString(record.observed_value ?? record.observedValue, "") || undefined,
    limitValue: asString(record.limit_value ?? record.limitValue, "") || undefined,
    plannedValue: asString(record.planned_value ?? record.plannedValue, "") || undefined,
  };
}

export function adaptPlanExplanation(raw: unknown): PlanCapabilityExplanationModel {
  const record = asRecord(raw);
  const authorityRaw = asString(record.authority, "RECORDED_FIXTURE_REFERENCE");
  return {
    candidateId: asString(record.candidate_id ?? record.candidateId, "candidate-unknown"),
    candidateLabel: asString(record.candidate_label ?? record.candidateLabel, "Candidate"),
    candidateSubtitle: asString(record.candidate_subtitle ?? record.candidateSubtitle, "") || undefined,
    selected: asBoolean(record.selected, true),
    why: asArray(record.why).map((item, index) => adaptImpact(item, index)),
    rejected: asArray(record.rejected).map((item, index) => adaptImpact(item, index)),
    unknown: asArray(record.unknown).map((item) => adaptEvidence(item, "Evidence unavailable")),
    protectedCommitments: asArray(record.protected_commitments ?? record.protectedCommitments).filter(isRecord).map((item, index) => ({
      id: asString(item.id, `commitment-${index + 1}`),
      label: asString(item.label, `Protected commitment ${index + 1}`),
      level: asString(item.level, "C4_ANCHORED"),
      preserved: asBoolean(item.preserved, true),
      detail: asString(item.detail, "") || undefined,
    })),
    authority: authorityRaw === "BACKEND_PLANNING" || authorityRaw === "UI_LOCAL_DRAFT"
      ? authorityRaw
      : "RECORDED_FIXTURE_REFERENCE",
  };
}

export function adaptRecoveryDiff(raw: unknown): RecoveryCapabilityDiffModel {
  const record = asRecord(raw);
  const authorityRaw = asString(record.authority, "RECORDED_FIXTURE_REFERENCE");
  return {
    journeyId: asString(record.journey_id ?? record.journeyId, "journey-unknown"),
    before: asArray(record.before).map((item, index) => adaptImpact(item, index)),
    after: asArray(record.after).map((item, index) => adaptImpact(item, index)),
    preserved: asArray(record.preserved).map((item, index) => adaptImpact(item, index)),
    atRisk: asArray(record.at_risk ?? record.atRisk).map((item, index) => adaptImpact(item, index)),
    evidenceGaps: asArray(record.evidence_gaps ?? record.evidenceGaps).map((item) => adaptEvidence(item, "Evidence unavailable")),
    protectedCommitments: asArray(record.protected_commitments ?? record.protectedCommitments).filter(isRecord).map((item, index) => ({
      id: asString(item.id, `commitment-${index + 1}`),
      label: asString(item.label, `Protected commitment ${index + 1}`),
      level: asString(item.level, "C4_ANCHORED"),
      preserved: asBoolean(item.preserved, true),
      detail: asString(item.detail, "") || undefined,
    })),
    authority: authorityRaw === "BACKEND_PLANNING" || authorityRaw === "UI_LOCAL_DRAFT"
      ? authorityRaw
      : "RECORDED_FIXTURE_REFERENCE",
  };
}

function quickNeed(id: QuickNeedId) {
  return QUICK_NEEDS.find((item) => item.id === id);
}

function draftEvidence(summary: string): CapabilityEvidence {
  return makeUiOnlyEvidence(summary, {
    liveChecks: ["Backend capability contract must confirm this setup selection before planning uses it."],
  });
}

export function draftToCapabilities(
  draft: JourneySetupNeedsDraft,
  locale: "zh-CN" | "en" = "zh-CN",
): TravelerCapability[] {
  const capabilities: TravelerCapability[] = [];
  draft.quickNeedIds.forEach((id, index) => {
    const item = quickNeed(id as QuickNeedId);
    if (!item) return;
    const isHard = item.id === "wheelchair_access" || item.id === "avoid_stairs";
    const strength: CapabilityStrength = isHard
      ? "HARD"
      : item.id === "less_walking" || item.id === "midday_rest" || item.id === "baby_nap" || item.id === "stroller"
        ? "STRONG"
        : "SOFT";
    capabilities.push(
      adaptCapability(
        {
          id: `setup-${item.id}`,
          label: locale === "zh-CN" ? item.labelZh : item.labelEn,
          kind: item.kind,
          strength,
          scope: "THIS_JOURNEY",
          source: "TRAVELER_STATED",
          source_label: locale === "zh-CN" ? "出行需求设置" : "Journey setup",
          explicit: true,
          traveler_stated: true,
          active: true,
          confirmed: false,
          evidence: draftEvidence(
            locale === "zh-CN"
              ? "来自本地 UI 草稿；尚未由后端能力契约确认。"
              : "Local UI draft; not yet confirmed by the backend capability contract.",
          ),
        },
        index,
      ),
    );
  });
  const advanced = draft.advanced;
  const pushConstraint = (
    id: string,
    labelZh: string,
    labelEn: string,
    kind: CapabilityKind,
    key: CapabilityConstraint["key"],
    operator: CapabilityConstraint["operator"],
    value: CapabilityConstraint["value"],
    unit?: string,
  ) => {
    const label = locale === "zh-CN" ? labelZh : labelEn;
    capabilities.push(
      adaptCapability(
        {
          id: `setup-advanced-${id}`,
          label,
          kind,
          strength: "STRONG",
          scope: "THIS_JOURNEY",
          source: "TRAVELER_STATED",
          source_label: locale === "zh-CN" ? "出行需求设置 · 高级" : "Journey setup · advanced",
          explicit: true,
          traveler_stated: true,
          active: true,
          confirmed: false,
          constraints: [{ key, operator, value, unit, hard: false }],
          evidence: draftEvidence(
            locale === "zh-CN"
              ? "高级设置是 UI 草稿，需后端规划验证后才会成为约束。"
              : "Advanced setup is a UI draft; backend planning must validate it before it becomes a constraint.",
          ),
        },
        capabilities.length,
      ),
    );
  };
  if (advanced.maxWalkingPerLegM !== undefined) pushConstraint("max-walk-leg", "每段最大步行", "Max walking per leg", "PHYSICAL_LIMIT", "max_walking_per_leg_m", "LTE", advanced.maxWalkingPerLegM, "m");
  if (advanced.maxContinuousWalkingM !== undefined) pushConstraint("max-walk-continuous", "最长连续步行", "Max continuous walking", "PHYSICAL_LIMIT", "max_continuous_walking_m", "LTE", advanced.maxContinuousWalkingM, "m");
  if (advanced.restFrequencyMin !== undefined) pushConstraint("rest-frequency", "休息频率", "Rest frequency", "CARE_REQUIREMENT", "rest_frequency_min", "LTE", advanced.restFrequencyMin, "min");
  if (advanced.napWindow) pushConstraint("nap-window", "午睡时间窗", "Nap window", "CARE_REQUIREMENT", "nap_window", "BETWEEN", [0, 0]);
  if (advanced.toiletFrequencyMin !== undefined) pushConstraint("toilet-frequency", "如厕/休息间隔", "Toilet / rest interval", "CARE_REQUIREMENT", "toilet_frequency_min", "LTE", advanced.toiletFrequencyMin, "min");
  if (advanced.pace) pushConstraint("pace", "节奏", "Pace", "SOFT_PREFERENCE", "pace", "REQUIRED", advanced.pace);
  if (advanced.quietSensory) pushConstraint("quiet-sensory", "安静/低感官环境", "Quiet / low-sensory", "SOFT_PREFERENCE", "quiet_sensory", "REQUIRED", true);
  return capabilities;
}

export interface LiveCapabilityAdapterOptions {
  baseUrl?: string;
  fetcher?: typeof fetch;
}

function trimBaseUrl(baseUrl?: string): string {
  return (baseUrl ?? "").replace(/\/+$/, "");
}

async function requestCapabilityJson(
  path: string,
  options: LiveCapabilityAdapterOptions,
): Promise<unknown> {
  const fetcher = options.fetcher ?? fetch;
  const response = await fetcher(`${trimBaseUrl(options.baseUrl)}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (response.status === 404) {
    throw new CapabilityAdapterNotConfiguredError(
      `Capability endpoint not implemented yet: ${path}. Use RECORDED_FIXTURE explicitly.`,
    );
  }
  if (!response.ok) {
    throw new Error(`Capability request failed: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as unknown;
}

/**
 * Live adapter for the proposed capability contract. It maps only known fields
 * and does not infer hard accessibility needs from soft Traveler Twin data.
 */
export function createLiveCapabilityAdapter(options: LiveCapabilityAdapterOptions = {}): CapabilityDataSource {
  return {
    sourceKind: "LIVE",
    async fetchCapabilities(travelerId: string): Promise<TravelerCapability[]> {
      const payload = await requestCapabilityJson(`/api/v1/travelers/${encodeURIComponent(travelerId)}/capabilities`, options);
      const record = asRecord(payload);
      const items = record.items ?? record.capabilities ?? payload;
      const mapped = adaptCapabilities(items, { confirmed: true, active: true });
      if (record.traveler_twin && mapped.length === 0) {
        return adaptTravelerTwinEvidence(record.traveler_twin);
      }
      return mapped;
    },
    async fetchPlanExplanation(journeyId: string): Promise<PlanCapabilityExplanationModel> {
      const payload = await requestCapabilityJson(`/api/v1/journeys/${encodeURIComponent(journeyId)}/capability-plan`, options);
      return adaptPlanExplanation(payload);
    },
    async fetchRecoveryDiff(journeyId: string): Promise<RecoveryCapabilityDiffModel> {
      const payload = await requestCapabilityJson(`/api/v1/journeys/${encodeURIComponent(journeyId)}/recovery/capability-diff`, options);
      return adaptRecoveryDiff(payload);
    },
  };
}

export function describeAdapterSource(source: CapabilityDataSource): string {
  return source.sourceKind;
}
