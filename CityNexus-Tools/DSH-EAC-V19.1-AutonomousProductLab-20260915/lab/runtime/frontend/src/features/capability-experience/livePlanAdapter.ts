import type {
  CapabilityEvidence,
  CapabilityImpact,
  PlanCapabilityExplanationModel,
  RecoveryCapabilityDiffModel,
} from "./types";
import { mapBackendCapabilities, type BackendCapabilityDto } from "./liveShadowAdapter";

export interface BackendImpactDto {
  id: string;
  capability_id: string;
  capability_label: string;
  kind: string;
  status: "PRESERVED" | "IMPROVED" | "AT_RISK" | "VIOLATED" | "UNKNOWN";
  explanation: string;
  candidate_id?: string;
  failure?: string | null;
  evidence?: {
    state?: string;
    summary?: string;
    failure?: string | null;
    provenance?: Record<string, unknown>;
  };
}

export interface BackendPlanImpactResponse {
  journey_id: string;
  plan_version_id?: string;
  status: "PASS" | "FAIL" | "CONTRACT_NOT_AVAILABLE";
  gate_failures: string[];
  capabilities: BackendCapabilityDto[];
  impacts?: {
    candidate_id: string;
    authority: string;
    gate_failures: string[];
    why: BackendImpactDto[];
    rejected: BackendImpactDto[];
    unknown: BackendImpactDto[];
    capabilities: BackendCapabilityDto[];
    unknown_accessibility_is_not_accessible?: boolean;
  } | null;
  reason?: string;
  unknown_accessibility_is_not_accessible?: boolean;
}

function mapEvidence(evidence: BackendImpactDto["evidence"], fallback: string): CapabilityEvidence {
  const stateRaw = String(evidence?.state ?? "NEEDS_LIVE_EVIDENCE").toUpperCase();
  const state = ["VERIFIED", "UNVERIFIED", "CONFLICT", "NEEDS_LIVE_EVIDENCE"].includes(stateRaw)
    ? (stateRaw as CapabilityEvidence["state"])
    : "NEEDS_LIVE_EVIDENCE";
  return {
    state,
    summary: evidence?.summary ?? fallback,
    provenance: {
      kind: "LIVE",
      label: "BACKEND_GATE",
      sourceSystem: "capability-plan-impact",
      notes: "Derived from the isolated V19 deterministic feasibility gate.",
    },
    detail: evidence?.failure ?? undefined,
    facts: evidence?.provenance,
  };
}

function mapImpact(dto: BackendImpactDto): CapabilityImpact {
  const kind = (
    ["HARD_ACCESSIBILITY_NEED", "CARE_REQUIREMENT", "PHYSICAL_LIMIT", "TRIP_CONTEXT", "SOFT_PREFERENCE", "PROTECTED_COMMITMENT"].includes(dto.kind)
      ? dto.kind
      : "SOFT_PREFERENCE"
  ) as CapabilityImpact["kind"];
  return {
    id: dto.id,
    capabilityId: dto.capability_id,
    capabilityLabel: dto.capability_label,
    kind,
    status: dto.status,
    explanation: dto.explanation,
    evidence: mapEvidence(dto.evidence, dto.explanation),
    candidateId: dto.candidate_id,
  };
}

export function mapPlanImpactResponse(response: BackendPlanImpactResponse): PlanCapabilityExplanationModel | null {
  if (!response.impacts) return null;
  const why = (response.impacts.why ?? []).map(mapImpact);
  const rejected = (response.impacts.rejected ?? []).map(mapImpact);
  const unknownImpacts = (response.impacts.unknown ?? []).map(mapImpact);
  return {
    candidateId: response.impacts.candidate_id || response.plan_version_id || "live-plan",
    candidateLabel: response.plan_version_id ? `Plan ${response.plan_version_id.slice(0, 8)}` : "Live plan",
    candidateSubtitle: `gate=${response.status}`,
    selected: true,
    why,
    rejected,
    unknown: unknownImpacts.map((item) => item.evidence),
    protectedCommitments: (response.gate_failures ?? [])
      .filter((failure) => failure.includes("LOCKED_COMMITMENT") || failure.includes("JOURNEY_END_BY"))
      .map((failure, index) => ({
        id: `c4-gate-${index}`,
        label: failure,
        level: "C4_ANCHORED",
        preserved: false,
        detail: "Protected commitment/Journey boundary failure from the live gate.",
      })),
    authority: "BACKEND_PLANNING",
  };
}

export function mapRecoveryDiffFromPlan(
  response: BackendPlanImpactResponse,
  journeyId: string,
): RecoveryCapabilityDiffModel {
  const mapped = mapPlanImpactResponse(response);
  const all = mapped ? [...mapped.why, ...mapped.rejected] : [];
  return {
    journeyId,
    before: all,
    after: all,
    preserved: all.filter((impact) => impact.status === "PRESERVED" || impact.status === "IMPROVED"),
    atRisk: all.filter((impact) => impact.status === "AT_RISK" || impact.status === "VIOLATED"),
    evidenceGaps: mapped?.unknown ?? [],
    protectedCommitments: mapped?.protectedCommitments ?? [],
    authority: "BACKEND_PLANNING",
  };
}
