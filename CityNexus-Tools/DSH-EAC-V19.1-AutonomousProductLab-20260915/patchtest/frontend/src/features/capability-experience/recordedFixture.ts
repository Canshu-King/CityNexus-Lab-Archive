import type {
  CapabilityConfirmation,
  CapabilityEvidence,
  CapabilityImpact,
  CapabilityMapMarker,
  JourneySetupNeedsDraft,
  MobileCapabilityShieldModel,
  PlanCapabilityExplanationModel,
  RecoveryCapabilityDiffModel,
  TravelerCapability,
} from "./types";
import { makeEvidence } from "./evidence";
import { adaptCapability, adaptDetectedNeed, adaptImpact, adaptPlanExplanation, adaptRecoveryDiff, type CapabilityDataSource } from "./adapter";

const recordedOn = "2026-09-15";

function fixtureEvidence(summary: string, state: CapabilityEvidence["state"] = "NEEDS_LIVE_EVIDENCE", detail?: string): CapabilityEvidence {
  return makeEvidence(state, summary, {
    kind: "RECORDED_FIXTURE",
    label: "RECORDED_FIXTURE",
    sourceSystem: "citynexus_v19_capability_fixture",
    recordedOn,
  }, detail ? { detail } : {});
}

export interface CapabilityScenario {
  id: "A" | "B" | "C" | "D" | "E";
  titleZh: string;
  titleEn: string;
  summaryZh: string;
  summaryEn: string;
  sourceLabel: string;
  setup: JourneySetupNeedsDraft;
  detected: CapabilityConfirmation[];
  capabilities: TravelerCapability[];
  plan: PlanCapabilityExplanationModel;
  recovery: RecoveryCapabilityDiffModel;
  mobile: {
    shield: MobileCapabilityShieldModel;
    mapMarkers: CapabilityMapMarker[];
  };
}

function capability(
  id: string,
  labelZh: string,
  labelEn: string,
  kind: TravelerCapability["kind"],
  strength: TravelerCapability["strength"],
  scope: TravelerCapability["scope"],
  evidence: CapabilityEvidence,
  source: TravelerCapability["source"] = "RECORDED_FIXTURE",
  extras: Partial<TravelerCapability> = {},
): TravelerCapability {
  const base = adaptCapability(
    {
      id,
      label: labelZh,
      kind,
      strength,
      scope,
      source,
      source_label: "RECORDED_FIXTURE",
      explicit: true,
      traveler_stated: true,
      active: true,
      confirmed: true,
      evidence,
    },
    0,
  );
  return { ...base, label: labelZh, extra: { labelEn, ...(base.extra ?? {}) }, ...extras };
}

function impact(
  id: string,
  capabilityId: string,
  labelZh: string,
  labelEn: string,
  kind: TravelerCapability["kind"],
  status: CapabilityImpact["status"],
  explanationZh: string,
  explanationEn: string,
  evidence: CapabilityEvidence,
  extras: Partial<CapabilityImpact> = {},
): CapabilityImpact {
  const base = adaptImpact(
    {
      id,
      capability_id: capabilityId,
      capability_label: labelZh,
      kind,
      status,
      explanation: explanationZh,
      evidence,
      ...extras,
    },
    0,
  );
  return { ...base, ...extras, explanation: explanationZh };
}


const scenarioA: CapabilityScenario = {
  id: "A",
  titleZh: "A · 老人 / 膝盖不好",
  titleEn: "A · Older adult / knee pain",
  summaryZh: "低步行上限 + 中午休息。系统必须区分硬性限制与偏好，并把未知无障碍证据说清楚。",
  summaryEn: "Low walking limit + midday rest. Hard limit and preference must be distinct; unknown evidence must stay unknown.",
  sourceLabel: "RECORDED_FIXTURE",
  setup: {
    quickNeedIds: ["less_walking", "midday_rest"],
    advanced: { maxWalkingPerLegM: 500, maxContinuousWalkingM: 500, restFrequencyMin: 90, napWindow: { start: "12:00", end: "14:00" } },
    note: "我妈膝盖不好，不能走太多，中午最好休息。",
  },
  detected: [
    adaptDetectedNeed({
      id: "detected-a-low-walking",
      statement: "我妈膝盖不好，不能走太多，中午最好休息。",
      detected_label: "Low walking",
      kind: "PHYSICAL_LIMIT",
      strength: "HARD",
      scope: "THIS_JOURNEY",
      evidence: fixtureEvidence("Copilot language detection requires confirmation and route evidence.", "NEEDS_LIVE_EVIDENCE"),
    }),
    adaptDetectedNeed({
      id: "detected-a-midday-rest",
      statement: "中午最好休息。",
      detected_label: "Midday rest",
      kind: "CARE_REQUIREMENT",
      strength: "STRONG",
      scope: "THIS_JOURNEY",
      evidence: fixtureEvidence("Copilot language detection requires confirmation.", "NEEDS_LIVE_EVIDENCE"),
    }),
  ],
  capabilities: [
    capability("cap-a-walking", "低步行上限", "Low walking limit", "PHYSICAL_LIMIT", "HARD", "THIS_JOURNEY", fixtureEvidence("Traveler-stated. Live route walking must be checked.", "NEEDS_LIVE_EVIDENCE", "Max walking per leg 500 m."), "TRAVELER_STATED", { constraints: [{ key: "max_walking_per_leg_m", operator: "LTE", value: 500, unit: "m", hard: true }] }),
    capability("cap-a-rest", "中午休息", "Midday rest", "CARE_REQUIREMENT", "STRONG", "THIS_JOURNEY", fixtureEvidence("Traveler-stated nap window. Provider opening hours not yet checked.", "NEEDS_LIVE_EVIDENCE"), "TRAVELER_STATED", { constraints: [{ key: "nap_window", operator: "BETWEEN", value: [720, 840], hard: false }] }),
  ],
  plan: adaptPlanExplanation({
    candidate_id: "candidate-a-1",
    candidate_label: "Indoor museum + short taxi legs",
    candidate_subtitle: "320 m longest walking leg",
    selected: true,
    authority: "RECORDED_FIXTURE_REFERENCE",
    why: [
      {
        id: "why-a-walk",
        capability_id: "cap-a-walking",
        capability_label: "Low walking",
        kind: "PHYSICAL_LIMIT",
        status: "PRESERVED",
        explanation: "walking leg 320m < 500m limit",
        observed_value: "320 m",
        limit_value: "500 m",
        evidence: fixtureEvidence("Recorded route fixture. Live provider evidence required before release.", "NEEDS_LIVE_EVIDENCE"),
      },
      {
        id: "why-a-indoor",
        capability_id: "cap-a-rest",
        capability_label: "Indoor rest context",
        kind: "TRIP_CONTEXT",
        status: "PRESERVED",
        explanation: "indoor and close to a rest stop",
        evidence: fixtureEvidence("Indoor tag from recorded place fixture.", "UNVERIFIED"),
      },
      {
        id: "why-a-rest",
        capability_id: "cap-a-rest",
        capability_label: "Midday rest",
        kind: "CARE_REQUIREMENT",
        status: "PRESERVED",
        explanation: "rest window preserved 12:00–14:00",
        evidence: fixtureEvidence("Recorded schedule fixture; live schedule not checked.", "NEEDS_LIVE_EVIDENCE"),
      },
    ],
    rejected: [
      {
        id: "reject-a-walk",
        capability_id: "cap-a-walking",
        capability_label: "Low walking",
        kind: "PHYSICAL_LIMIT",
        status: "VIOLATED",
        explanation: "route walking 780m exceeds hard limit",
        observed_value: "780 m",
        limit_value: "500 m",
        evidence: fixtureEvidence("Recorded route fixture shows a hard-limit violation.", "VERIFIED"),
      },
    ],
    unknown: [
      fixtureEvidence("step-free evidence unavailable for Candidate B", "NEEDS_LIVE_EVIDENCE"),
    ],
    protected_commitments: [
      { id: "c4-a-dinner", label: "Family dinner reservation", level: "C4_ANCHORED", preserved: true, detail: "Kept as a separate protected commitment." },
    ],
  }),
  recovery: adaptRecoveryDiff({
    journey_id: "journey-a",
    authority: "RECORDED_FIXTURE_REFERENCE",
    before: [
      { id: "before-a-walk", capability_id: "cap-a-walking", capability_label: "Low walking", kind: "PHYSICAL_LIMIT", status: "PRESERVED", explanation: "320 m before recovery", evidence: fixtureEvidence("Recorded before fixture.", "NEEDS_LIVE_EVIDENCE") },
      { id: "before-a-rest", capability_id: "cap-a-rest", capability_label: "Midday rest", kind: "CARE_REQUIREMENT", status: "PRESERVED", explanation: "Rest window preserved", evidence: fixtureEvidence("Recorded before fixture.", "NEEDS_LIVE_EVIDENCE") },
    ],
    after: [
      { id: "after-a-walk", capability_id: "cap-a-walking", capability_label: "Low walking", kind: "PHYSICAL_LIMIT", status: "PRESERVED", explanation: "310 m after recovery", evidence: fixtureEvidence("Recorded recovery fixture. Live evidence required.", "NEEDS_LIVE_EVIDENCE") },
      { id: "after-a-rest", capability_id: "cap-a-rest", capability_label: "Midday rest", kind: "CARE_REQUIREMENT", status: "PRESERVED", explanation: "Rest window preserved 12:00–13:50", evidence: fixtureEvidence("Recorded recovery fixture.", "NEEDS_LIVE_EVIDENCE") },
      { id: "after-a-stepfree", capability_id: "cap-a-stepfree", capability_label: "Step-free access", kind: "HARD_ACCESSIBILITY_NEED", status: "UNKNOWN", explanation: "step-free evidence unavailable after recovery", evidence: fixtureEvidence("No provider evidence in fixture.", "NEEDS_LIVE_EVIDENCE") },
    ],
    preserved: [
      { id: "preserved-a-walk", capability_id: "cap-a-walking", capability_label: "Low walking", kind: "PHYSICAL_LIMIT", status: "PRESERVED", explanation: "310 m < 500 m", evidence: fixtureEvidence("Recorded recovery fixture.", "NEEDS_LIVE_EVIDENCE") },
    ],
    at_risk: [
      { id: "risk-a-stepfree", capability_id: "cap-a-stepfree", capability_label: "Step-free access", kind: "HARD_ACCESSIBILITY_NEED", status: "AT_RISK", explanation: "evidence gap could hide a step-free conflict", evidence: fixtureEvidence("Unknown, not accessible.", "NEEDS_LIVE_EVIDENCE") },
    ],
    evidence_gaps: [
      fixtureEvidence("step-free evidence unavailable after recovery", "NEEDS_LIVE_EVIDENCE"),
    ],
    protected_commitments: [
      { id: "c4-a-dinner", label: "Family dinner reservation", level: "C4_ANCHORED", preserved: true },
    ],
  }),
  mobile: {
    shield: {
      protectedCount: 2,
      needs: [
        capability("cap-a-walking", "低步行上限", "Low walking limit", "PHYSICAL_LIMIT", "HARD", "THIS_JOURNEY", fixtureEvidence("Traveler-stated hard limit.", "NEEDS_LIVE_EVIDENCE"), "TRAVELER_STATED"),
        capability("cap-a-rest", "中午休息", "Midday rest", "CARE_REQUIREMENT", "STRONG", "THIS_JOURNEY", fixtureEvidence("Traveler-stated rest window.", "NEEDS_LIVE_EVIDENCE"), "TRAVELER_STATED"),
      ],
      evidenceGap: { label: "Step-free access not verified", capabilityId: "cap-a-stepfree", evidence: fixtureEvidence("Live provider evidence required.", "NEEDS_LIVE_EVIDENCE") },
      primaryActionLabel: "查看或修改需求",
    },
    mapMarkers: [
      { id: "map-a-verified", kind: "VERIFIED_ACCESSIBILITY", label: "Tianjin Museum step-free entrance", detail: "Verified step-free evidence", evidence: fixtureEvidence("Verified in recorded fixture.", "VERIFIED"), longitude: 117.22, latitude: 39.08 },
      { id: "map-a-unknown", kind: "UNKNOWN_ACCESSIBILITY", label: "Candidate B accessibility not verified", detail: "Unknown is not accessible", evidence: fixtureEvidence("No provider evidence.", "NEEDS_LIVE_EVIDENCE"), longitude: 117.21, latitude: 39.09 },
      { id: "map-a-conflict", kind: "CONFLICT", label: "Candidate C known stairs conflict", detail: "Recorded stairs conflict", evidence: fixtureEvidence("Conflict recorded in fixture.", "CONFLICT"), longitude: 117.2, latitude: 39.1 },
      { id: "map-a-rest", kind: "REST_STOP", label: "Rest stop", detail: "Seating and toilet", evidence: fixtureEvidence("Recorded place tag.", "UNVERIFIED"), longitude: 117.19, latitude: 39.11 },
      { id: "map-a-nap", kind: "NAP_WINDOW", label: "Midday nap / rest window", detail: "12:00–14:00", evidence: fixtureEvidence("Traveler-stated.", "UNVERIFIED") },
      { id: "map-a-walk", kind: "WALKING_LIMIT_WARNING", label: "Walking limit warning", detail: "Candidate C: 780 m exceeds 500 m hard limit", evidence: fixtureEvidence("Recorded route fixture.", "VERIFIED") },
    ],
  },
};

const scenarioB: CapabilityScenario = {
  id: "B",
  titleZh: "B · 轮椅 / 无障碍",
  titleEn: "B · Wheelchair / step-free",
  summaryZh: "必须区分已核实的无台阶入口、未核实候选和被排除的楼梯冲突。",
  summaryEn: "Verified step-free entrance, unverified candidate, and known stairs conflict must be visually distinct.",
  sourceLabel: "RECORDED_FIXTURE",
  setup: {
    quickNeedIds: ["wheelchair_access", "avoid_stairs"],
    advanced: { maxWalkingPerLegM: 400, maxContinuousWalkingM: 400, restFrequencyMin: 60 },
    note: "需要轮椅，不能走楼梯。",
  },
  detected: [
    adaptDetectedNeed({
      id: "detected-b-stepfree",
      statement: "需要轮椅，不能走楼梯。",
      detected_label: "Step-free requirement",
      kind: "HARD_ACCESSIBILITY_NEED",
      strength: "HARD",
      scope: "THIS_JOURNEY",
      evidence: fixtureEvidence("Copilot detection; provider step-free evidence required.", "NEEDS_LIVE_EVIDENCE"),
    }),
  ],
  capabilities: [
    capability("cap-b-stepfree", "无台阶通行", "Step-free access", "HARD_ACCESSIBILITY_NEED", "HARD", "THIS_JOURNEY", fixtureEvidence("Tianjin Museum verified step-free evidence in recorded fixture.", "VERIFIED"), "PROVIDER_EVIDENCE"),
    capability("cap-b-stairs", "避免楼梯", "Avoid stairs", "HARD_ACCESSIBILITY_NEED", "HARD", "THIS_JOURNEY", fixtureEvidence("Traveler-stated; live venue evidence required.", "NEEDS_LIVE_EVIDENCE"), "TRAVELER_STATED"),
  ],
  plan: adaptPlanExplanation({
    candidate_id: "candidate-b-1",
    candidate_label: "Candidate A · Tianjin Museum",
    candidate_subtitle: "Verified step-free entrance",
    selected: true,
    authority: "RECORDED_FIXTURE_REFERENCE",
    why: [
      { id: "why-b-stepfree", capability_id: "cap-b-stepfree", capability_label: "Step-free requirement", kind: "HARD_ACCESSIBILITY_NEED", status: "PRESERVED", explanation: "Tianjin Museum: verified step-free evidence", evidence: fixtureEvidence("Recorded provider evidence.", "VERIFIED") },
      { id: "why-b-walk", capability_id: "cap-b-stepfree", capability_label: "Wheelchair walking limit", kind: "PHYSICAL_LIMIT", status: "PRESERVED", explanation: "walking leg 180m < 400m limit", observed_value: "180 m", limit_value: "400 m", evidence: fixtureEvidence("Recorded route fixture; live route required.", "NEEDS_LIVE_EVIDENCE") },
    ],
    rejected: [
      { id: "reject-b-stairs", capability_id: "cap-b-stairs", capability_label: "Avoid stairs", kind: "HARD_ACCESSIBILITY_NEED", status: "VIOLATED", explanation: "Candidate C: known stairs conflict", evidence: fixtureEvidence("Provider-recorded stairs conflict.", "CONFLICT") },
    ],
    unknown: [
      fixtureEvidence("Candidate B: accessibility not verified", "UNVERIFIED"),
    ],
    protected_commitments: [
      { id: "c4-b-train", label: "Outbound train reservation", level: "C4_ANCHORED", preserved: true },
    ],
  }),
  recovery: adaptRecoveryDiff({
    journey_id: "journey-b",
    authority: "RECORDED_FIXTURE_REFERENCE",
    before: [
      { id: "before-b-stepfree", capability_id: "cap-b-stepfree", capability_label: "Step-free requirement", kind: "HARD_ACCESSIBILITY_NEED", status: "PRESERVED", explanation: "Verified step-free entrance before recovery", evidence: fixtureEvidence("Recorded provider evidence.", "VERIFIED") },
    ],
    after: [
      { id: "after-b-stepfree", capability_id: "cap-b-stepfree", capability_label: "Step-free requirement", kind: "HARD_ACCESSIBILITY_NEED", status: "PRESERVED", explanation: "Recovery keeps verified step-free entrance", evidence: fixtureEvidence("Recorded recovery provider evidence.", "VERIFIED") },
      { id: "after-b-unknown", capability_id: "cap-b-unknown", capability_label: "Candidate B step-free access", kind: "HARD_ACCESSIBILITY_NEED", status: "UNKNOWN", explanation: "Candidate B accessibility not verified", evidence: fixtureEvidence("Unknown is not accessible.", "NEEDS_LIVE_EVIDENCE") },
    ],
    preserved: [
      { id: "pres-b-stepfree", capability_id: "cap-b-stepfree", capability_label: "Step-free requirement", kind: "HARD_ACCESSIBILITY_NEED", status: "PRESERVED", explanation: "Verified entrance retained", evidence: fixtureEvidence("Recorded provider evidence.", "VERIFIED") },
    ],
    at_risk: [
      { id: "risk-b-unknown", capability_id: "cap-b-unknown", capability_label: "Candidate B step-free access", kind: "HARD_ACCESSIBILITY_NEED", status: "AT_RISK", explanation: "Unknown step-free evidence cannot be treated as accessible", evidence: fixtureEvidence("Unknown is not accessible.", "NEEDS_LIVE_EVIDENCE") },
    ],
    evidence_gaps: [fixtureEvidence("Candidate B: accessibility not verified", "UNVERIFIED")],
    protected_commitments: [{ id: "c4-b-train", label: "Outbound train reservation", level: "C4_ANCHORED", preserved: true }],
  }),
  mobile: {
    shield: {
      protectedCount: 1,
      needs: [capability("cap-b-stepfree", "无台阶通行", "Step-free access", "HARD_ACCESSIBILITY_NEED", "HARD", "THIS_JOURNEY", fixtureEvidence("Verified recorded provider evidence.", "VERIFIED"), "PROVIDER_EVIDENCE")],
      evidenceGap: { label: "Candidate B step-free access not verified", capabilityId: "cap-b-unknown", evidence: fixtureEvidence("Unknown is not accessible.", "UNVERIFIED") },
      primaryActionLabel: "查看无障碍证据",
    },
    mapMarkers: [
      { id: "map-b-verified", kind: "VERIFIED_ACCESSIBILITY", label: "Tianjin Museum: Verified step-free evidence", detail: "Verified step-free entrance", evidence: fixtureEvidence("Recorded provider evidence.", "VERIFIED"), longitude: 117.22, latitude: 39.08 },
      { id: "map-b-unknown", kind: "UNKNOWN_ACCESSIBILITY", label: "Candidate B: Accessibility not verified", detail: "Unknown is not accessible", evidence: fixtureEvidence("No provider evidence.", "NEEDS_LIVE_EVIDENCE"), longitude: 117.205, latitude: 39.095 },
      { id: "map-b-conflict", kind: "CONFLICT", label: "Candidate C: Known stairs conflict", detail: "Rejected by HARD avoid-stairs", evidence: fixtureEvidence("Provider-recorded conflict.", "CONFLICT"), longitude: 117.19, latitude: 39.105 },
      { id: "map-b-walk", kind: "WALKING_LIMIT_WARNING", label: "Wheelchair walking limit", detail: "180 m < 400 m for selected candidate", evidence: fixtureEvidence("Recorded route fixture.", "NEEDS_LIVE_EVIDENCE") },
    ],
  },
};

const scenarioC: CapabilityScenario = {
  id: "C",
  titleZh: "C · 婴儿家庭",
  titleEn: "C · Family with infant",
  summaryZh: "婴儿车、午睡、如厕/休息频率。照护需求不等于医疗诊断。",
  summaryEn: "Stroller, nap, and toilet/rest frequency. Care needs are not a medical diagnosis.",
  sourceLabel: "RECORDED_FIXTURE",
  setup: {
    quickNeedIds: ["stroller", "baby_nap", "midday_rest"],
    advanced: { maxContinuousWalkingM: 300, napWindow: { start: "13:00", end: "15:00" }, toiletFrequencyMin: 60, quietSensory: true },
    note: "带婴儿车，中午要午睡，别安排太久的户外步行。",
  },
  detected: [
    adaptDetectedNeed({ id: "detected-c-stroller", statement: "带婴儿车。", detected_label: "Stroller access", kind: "CARE_REQUIREMENT", strength: "STRONG", scope: "THIS_JOURNEY", evidence: fixtureEvidence("Copilot detection; venue stroller access not verified.", "NEEDS_LIVE_EVIDENCE") }),
    adaptDetectedNeed({ id: "detected-c-nap", statement: "中午要午睡。", detected_label: "Baby nap", kind: "CARE_REQUIREMENT", strength: "HARD", scope: "THIS_JOURNEY", evidence: fixtureEvidence("Copilot detection; schedule evidence required.", "NEEDS_LIVE_EVIDENCE") }),
  ],
  capabilities: [
    capability("cap-c-stroller", "婴儿车可通行", "Stroller accessible", "CARE_REQUIREMENT", "STRONG", "THIS_JOURNEY", fixtureEvidence("Traveler-stated; venue elevator/step-free data required.", "NEEDS_LIVE_EVIDENCE"), "TRAVELER_STATED"),
    capability("cap-c-nap", "婴儿午睡窗", "Baby nap window", "CARE_REQUIREMENT", "HARD", "THIS_JOURNEY", fixtureEvidence("Traveler-stated; live schedule feasibility required.", "NEEDS_LIVE_EVIDENCE"), "TRAVELER_STATED", { constraints: [{ key: "nap_window", operator: "BETWEEN", value: [780, 900], hard: true }] }),
  ],
  plan: adaptPlanExplanation({
    candidate_id: "candidate-c-1",
    candidate_label: "Indoor museum + nearby park rest",
    candidate_subtitle: "Nap window preserved",
    selected: true,
    authority: "RECORDED_FIXTURE_REFERENCE",
    why: [
      { id: "why-c-nap", capability_id: "cap-c-nap", capability_label: "Baby nap", kind: "CARE_REQUIREMENT", status: "PRESERVED", explanation: "nap window 13:00–15:00 preserved", evidence: fixtureEvidence("Recorded schedule fixture; live schedule required.", "NEEDS_LIVE_EVIDENCE") },
      { id: "why-c-walk", capability_id: "cap-c-stroller", capability_label: "Stroller walking", kind: "PHYSICAL_LIMIT", status: "PRESERVED", explanation: "continuous walking 220m < 300m limit", observed_value: "220 m", limit_value: "300 m", evidence: fixtureEvidence("Recorded route fixture.", "NEEDS_LIVE_EVIDENCE") },
      { id: "why-c-indoor", capability_id: "cap-c-indoor", capability_label: "Indoor / quiet option", kind: "TRIP_CONTEXT", status: "PRESERVED", explanation: "indoor backup space with restroom", evidence: fixtureEvidence("Recorded place tags.", "UNVERIFIED") },
    ],
    rejected: [
      { id: "reject-c-walk", capability_id: "cap-c-stroller", capability_label: "Stroller walking", kind: "PHYSICAL_LIMIT", status: "VIOLATED", explanation: "outdoor route continuous walking 640m exceeds 300m", observed_value: "640 m", limit_value: "300 m", evidence: fixtureEvidence("Recorded route fixture.", "VERIFIED") },
    ],
    unknown: [fixtureEvidence("stroller elevator availability not verified", "UNVERIFIED"), fixtureEvidence("quiet/sensory evidence unavailable", "NEEDS_LIVE_EVIDENCE")],
    protected_commitments: [{ id: "c4-c-hotel", label: "Hotel check-in window", level: "C4_ANCHORED", preserved: true }],
  }),
  recovery: adaptRecoveryDiff({
    journey_id: "journey-c",
    authority: "RECORDED_FIXTURE_REFERENCE",
    before: [
      { id: "before-c-nap", capability_id: "cap-c-nap", capability_label: "Baby nap", kind: "CARE_REQUIREMENT", status: "PRESERVED", explanation: "Nap window preserved", evidence: fixtureEvidence("Recorded before fixture.", "NEEDS_LIVE_EVIDENCE") },
      { id: "before-c-stroller", capability_id: "cap-c-stroller", capability_label: "Stroller accessible", kind: "CARE_REQUIREMENT", status: "PRESERVED", explanation: "Stroller route available", evidence: fixtureEvidence("Recorded before fixture.", "UNVERIFIED") },
    ],
    after: [
      { id: "after-c-nap", capability_id: "cap-c-nap", capability_label: "Baby nap", kind: "CARE_REQUIREMENT", status: "PRESERVED", explanation: "Nap window preserved after recovery", evidence: fixtureEvidence("Recorded recovery fixture.", "NEEDS_LIVE_EVIDENCE") },
      { id: "after-c-stepfree", capability_id: "cap-c-stepfree", capability_label: "Stroller step-free route", kind: "CARE_REQUIREMENT", status: "UNKNOWN", explanation: "stroller elevator evidence unavailable", evidence: fixtureEvidence("No provider evidence.", "NEEDS_LIVE_EVIDENCE") },
    ],
    preserved: [{ id: "pres-c-nap", capability_id: "cap-c-nap", capability_label: "Baby nap", kind: "CARE_REQUIREMENT", status: "PRESERVED", explanation: "Nap remains protected", evidence: fixtureEvidence("Recorded recovery fixture.", "NEEDS_LIVE_EVIDENCE") }],
    at_risk: [{ id: "risk-c-stroller", capability_id: "cap-c-stroller", capability_label: "Stroller accessible", kind: "CARE_REQUIREMENT", status: "AT_RISK", explanation: "elevator/step-free evidence unknown", evidence: fixtureEvidence("Unknown is not accessible.", "UNVERIFIED") }],
    evidence_gaps: [fixtureEvidence("stroller elevator availability not verified", "UNVERIFIED")],
    protected_commitments: [{ id: "c4-c-hotel", label: "Hotel check-in window", level: "C4_ANCHORED", preserved: true }],
  }),
  mobile: {
    shield: {
      protectedCount: 2,
      needs: [
        capability("cap-c-stroller", "婴儿车可通行", "Stroller accessible", "CARE_REQUIREMENT", "STRONG", "THIS_JOURNEY", fixtureEvidence("Traveler-stated.", "NEEDS_LIVE_EVIDENCE"), "TRAVELER_STATED"),
        capability("cap-c-nap", "婴儿午睡窗", "Baby nap window", "CARE_REQUIREMENT", "HARD", "THIS_JOURNEY", fixtureEvidence("Traveler-stated.", "NEEDS_LIVE_EVIDENCE"), "TRAVELER_STATED"),
      ],
      evidenceGap: { label: "Stroller access not verified", capabilityId: "cap-c-stroller", evidence: fixtureEvidence("Elevator/step-free evidence required.", "UNVERIFIED") },
      primaryActionLabel: "查看或修改需求",
    },
    mapMarkers: [
      { id: "map-c-unknown", kind: "UNKNOWN_ACCESSIBILITY", label: "Stroller elevator not verified", detail: "Unknown is not accessible", evidence: fixtureEvidence("No provider evidence.", "UNVERIFIED"), longitude: 117.2, latitude: 39.08 },
      { id: "map-c-rest", kind: "REST_STOP", label: "Rest / changing area", detail: "Recorded family rest stop", evidence: fixtureEvidence("Recorded place tag.", "UNVERIFIED"), longitude: 117.21, latitude: 39.09 },
      { id: "map-c-nap", kind: "NAP_WINDOW", label: "Baby nap window", detail: "13:00–15:00", evidence: fixtureEvidence("Traveler-stated.", "UNVERIFIED") },
      { id: "map-c-walk", kind: "WALKING_LIMIT_WARNING", label: "Continuous walking warning", detail: "Rejected route 640 m exceeds 300 m", evidence: fixtureEvidence("Recorded route fixture.", "VERIFIED") },
    ],
  },
};

const scenarioD: CapabilityScenario = {
  id: "D",
  titleZh: "D · 大件行李",
  titleEn: "D · Large luggage",
  summaryZh: "行李是行程背景，但可能升级为照护/无障碍需求，例如换乘楼梯。",
  summaryEn: "Luggage is trip context, but can become a care or accessibility need when stairs or transfers are involved.",
  sourceLabel: "RECORDED_FIXTURE",
  setup: {
    quickNeedIds: ["large_luggage", "avoid_stairs", "less_walking"],
    advanced: { maxWalkingPerLegM: 600, restFrequencyMin: 90 },
    note: "带两个大箱子，尽量少换乘、不要楼梯。",
  },
  detected: [
    adaptDetectedNeed({ id: "detected-d-luggage", statement: "带两个大箱子。", detected_label: "Large luggage", kind: "TRIP_CONTEXT", strength: "STRONG", scope: "THIS_JOURNEY", evidence: fixtureEvidence("Copilot detection; station transfer evidence not verified.", "NEEDS_LIVE_EVIDENCE") }),
    adaptDetectedNeed({ id: "detected-d-stairs", statement: "不要楼梯。", detected_label: "Avoid stairs", kind: "HARD_ACCESSIBILITY_NEED", strength: "HARD", scope: "THIS_JOURNEY", evidence: fixtureEvidence("Copilot detection; step-free evidence required.", "NEEDS_LIVE_EVIDENCE") }),
  ],
  capabilities: [
    capability("cap-d-luggage", "大件行李友好", "Large luggage friendly", "TRIP_CONTEXT", "STRONG", "THIS_JOURNEY", fixtureEvidence("Traveler-stated; transfer lift/escalator evidence required.", "NEEDS_LIVE_EVIDENCE"), "TRAVELER_STATED"),
    capability("cap-d-stairs", "避免楼梯/换乘", "Avoid stairs / transfers", "HARD_ACCESSIBILITY_NEED", "HARD", "THIS_JOURNEY", fixtureEvidence("Traveler-stated; live transfer evidence required.", "NEEDS_LIVE_EVIDENCE"), "TRAVELER_STATED"),
  ],
  plan: adaptPlanExplanation({
    candidate_id: "candidate-d-1",
    candidate_label: "Direct taxi with luggage space",
    candidate_subtitle: "No station stairs",
    selected: true,
    authority: "RECORDED_FIXTURE_REFERENCE",
    why: [
      { id: "why-d-taxi", capability_id: "cap-d-luggage", capability_label: "Large luggage", kind: "TRIP_CONTEXT", status: "PRESERVED", explanation: "direct taxi with confirmed luggage capacity in fixture", evidence: fixtureEvidence("Recorded provider fixture.", "VERIFIED") },
      { id: "why-d-stairs", capability_id: "cap-d-stairs", capability_label: "Avoid stairs", kind: "HARD_ACCESSIBILITY_NEED", status: "PRESERVED", explanation: "no station stairs in selected route", evidence: fixtureEvidence("Recorded route fixture.", "NEEDS_LIVE_EVIDENCE") },
    ],
    rejected: [
      { id: "reject-d-transfer", capability_id: "cap-d-stairs", capability_label: "Avoid stairs / transfers", kind: "HARD_ACCESSIBILITY_NEED", status: "VIOLATED", explanation: "metro transfer includes 42 stairs", evidence: fixtureEvidence("Recorded station conflict.", "CONFLICT") },
      { id: "reject-d-walk", capability_id: "cap-d-luggage", capability_label: "Large luggage", kind: "PHYSICAL_LIMIT", status: "VIOLATED", explanation: "walking leg 900m exceeds 600m with luggage", observed_value: "900 m", limit_value: "600 m", evidence: fixtureEvidence("Recorded route fixture.", "VERIFIED") },
    ],
    unknown: [fixtureEvidence("taxi luggage capacity live availability not verified", "UNVERIFIED")],
    protected_commitments: [{ id: "c4-d-flight", label: "Flight departure", level: "C4_ANCHORED", preserved: true }],
  }),
  recovery: adaptRecoveryDiff({
    journey_id: "journey-d",
    authority: "RECORDED_FIXTURE_REFERENCE",
    before: [
      { id: "before-d-stairs", capability_id: "cap-d-stairs", capability_label: "Avoid stairs", kind: "HARD_ACCESSIBILITY_NEED", status: "PRESERVED", explanation: "No stairs in before route", evidence: fixtureEvidence("Recorded before fixture.", "NEEDS_LIVE_EVIDENCE") },
    ],
    after: [
      { id: "after-d-stairs", capability_id: "cap-d-stairs", capability_label: "Avoid stairs", kind: "HARD_ACCESSIBILITY_NEED", status: "PRESERVED", explanation: "Recovery keeps no-stairs route", evidence: fixtureEvidence("Recorded recovery fixture.", "NEEDS_LIVE_EVIDENCE") },
      { id: "after-d-luggage", capability_id: "cap-d-luggage", capability_label: "Large luggage", kind: "TRIP_CONTEXT", status: "AT_RISK", explanation: "replacement taxi luggage capacity not live-verified", evidence: fixtureEvidence("Unknown taxi availability.", "UNVERIFIED") },
    ],
    preserved: [{ id: "pres-d-stairs", capability_id: "cap-d-stairs", capability_label: "Avoid stairs", kind: "HARD_ACCESSIBILITY_NEED", status: "PRESERVED", explanation: "No stairs preserved", evidence: fixtureEvidence("Recorded recovery fixture.", "NEEDS_LIVE_EVIDENCE") }],
    at_risk: [{ id: "risk-d-luggage", capability_id: "cap-d-luggage", capability_label: "Large luggage", kind: "TRIP_CONTEXT", status: "AT_RISK", explanation: "luggage capacity unknown", evidence: fixtureEvidence("Unknown is not a guarantee.", "UNVERIFIED") }],
    evidence_gaps: [fixtureEvidence("replacement taxi luggage capacity not verified", "UNVERIFIED")],
    protected_commitments: [{ id: "c4-d-flight", label: "Flight departure", level: "C4_ANCHORED", preserved: true }],
  }),
  mobile: {
    shield: {
      protectedCount: 2,
      needs: [
        capability("cap-d-luggage", "大件行李友好", "Large luggage friendly", "TRIP_CONTEXT", "STRONG", "THIS_JOURNEY", fixtureEvidence("Traveler-stated.", "NEEDS_LIVE_EVIDENCE"), "TRAVELER_STATED"),
        capability("cap-d-stairs", "避免楼梯/换乘", "Avoid stairs / transfers", "HARD_ACCESSIBILITY_NEED", "HARD", "THIS_JOURNEY", fixtureEvidence("Traveler-stated.", "NEEDS_LIVE_EVIDENCE"), "TRAVELER_STATED"),
      ],
      evidenceGap: { label: "Taxi luggage capacity not verified", capabilityId: "cap-d-luggage", evidence: fixtureEvidence("Live provider evidence required.", "UNVERIFIED") },
      primaryActionLabel: "查看行李方案",
    },
    mapMarkers: [
      { id: "map-d-conflict", kind: "CONFLICT", label: "Metro transfer: 42 stairs", detail: "Rejected by HARD avoid-stairs", evidence: fixtureEvidence("Recorded station conflict.", "CONFLICT"), longitude: 117.21, latitude: 39.09 },
      { id: "map-d-unknown", kind: "UNKNOWN_ACCESSIBILITY", label: "Taxi luggage capacity not verified", detail: "Unknown", evidence: fixtureEvidence("No live taxi evidence.", "UNVERIFIED"), longitude: 117.23, latitude: 39.07 },
      { id: "map-d-walk", kind: "WALKING_LIMIT_WARNING", label: "Walking with luggage warning", detail: "Rejected route 900 m exceeds 600 m", evidence: fixtureEvidence("Recorded route fixture.", "VERIFIED") },
    ],
  },
};

const scenarioE: CapabilityScenario = {
  id: "E",
  titleZh: "E · 普通软偏好",
  titleEn: "E · Ordinary soft preference",
  summaryZh: "没有 HARD 需求时，不能把未知或默认状态包装成“全程无障碍”。",
  summaryEn: "When there is no HARD need, the UI still must not turn unknown or default state into an accessibility claim.",
  sourceLabel: "RECORDED_FIXTURE",
  setup: {
    quickNeedIds: [],
    advanced: { pace: "RELAXED", quietSensory: true },
    note: "想安静一点，最好室内，别太赶。",
  },
  detected: [
    adaptDetectedNeed({ id: "detected-e-quiet", statement: "想安静一点，最好室内，别太赶。", detected_label: "Quiet / sensory preference", kind: "SOFT_PREFERENCE", strength: "SOFT", scope: "FUTURE_JOURNEYS", evidence: fixtureEvidence("Soft preference; never treated as accessibility evidence.", "UNVERIFIED") }),
    adaptDetectedNeed({ id: "detected-e-indoor", statement: "最好室内。", detected_label: "Prefer indoor", kind: "SOFT_PREFERENCE", strength: "SOFT", scope: "THIS_JOURNEY", evidence: fixtureEvidence("Soft preference; no provider evidence required for planning authority.", "UNVERIFIED") }),
  ],
  capabilities: [
    capability("cap-e-quiet", "安静/低感官", "Quiet / low-sensory", "SOFT_PREFERENCE", "SOFT", "FUTURE_JOURNEYS", fixtureEvidence("Traveler-stated soft preference.", "UNVERIFIED"), "TRAVELER_STATED", { confidence: 0.74, strengthScore: 0.6, learned: false }),
    capability("cap-e-indoor", "偏好室内", "Prefer indoor", "SOFT_PREFERENCE", "SOFT", "THIS_JOURNEY", fixtureEvidence("Traveler-stated soft preference.", "UNVERIFIED"), "TRAVELER_STATED"),
  ],
  plan: adaptPlanExplanation({
    candidate_id: "candidate-e-1",
    candidate_label: "Quiet indoor afternoon",
    candidate_subtitle: "No hard constraints",
    selected: true,
    authority: "RECORDED_FIXTURE_REFERENCE",
    why: [
      { id: "why-e-indoor", capability_id: "cap-e-indoor", capability_label: "Prefer indoor", kind: "SOFT_PREFERENCE", status: "PRESERVED", explanation: "indoor venue selected for comfort", evidence: fixtureEvidence("Soft preference; not an accessibility claim.", "UNVERIFIED") },
      { id: "why-e-quiet", capability_id: "cap-e-quiet", capability_label: "Quiet / low-sensory", kind: "SOFT_PREFERENCE", status: "PRESERVED", explanation: "scheduled outside known peak noise window in fixture", evidence: fixtureEvidence("Recorded noise fixture; live noise evidence not available.", "UNVERIFIED") },
    ],
    rejected: [],
    unknown: [fixtureEvidence("live noise level not verified", "UNVERIFIED")],
    protected_commitments: [],
  }),
  recovery: adaptRecoveryDiff({
    journey_id: "journey-e",
    authority: "RECORDED_FIXTURE_REFERENCE",
    before: [
      { id: "before-e-quiet", capability_id: "cap-e-quiet", capability_label: "Quiet / low-sensory", kind: "SOFT_PREFERENCE", status: "PRESERVED", explanation: "soft preference preserved", evidence: fixtureEvidence("Recorded before fixture.", "UNVERIFIED") },
    ],
    after: [
      { id: "after-e-quiet", capability_id: "cap-e-quiet", capability_label: "Quiet / low-sensory", kind: "SOFT_PREFERENCE", status: "PRESERVED", explanation: "soft preference still ranked", evidence: fixtureEvidence("Recorded recovery fixture.", "UNVERIFIED") },
    ],
    preserved: [{ id: "pres-e-quiet", capability_id: "cap-e-quiet", capability_label: "Quiet / low-sensory", kind: "SOFT_PREFERENCE", status: "PRESERVED", explanation: "Soft preference remains a ranking input", evidence: fixtureEvidence("Recorded recovery fixture.", "UNVERIFIED") }],
    at_risk: [],
    evidence_gaps: [fixtureEvidence("live noise level not verified", "UNVERIFIED")],
    protected_commitments: [],
  }),
  mobile: {
    shield: {
      protectedCount: 0,
      needs: [],
      evidenceGap: null,
      primaryActionLabel: "添加出行需求",
    },
    mapMarkers: [
      { id: "map-e-unknown", kind: "UNKNOWN_ACCESSIBILITY", label: "Noise level not verified", detail: "Unknown is not a quiet guarantee", evidence: fixtureEvidence("No live noise evidence.", "UNVERIFIED"), longitude: 117.2, latitude: 39.08 },
      { id: "map-e-rest", kind: "REST_STOP", label: "Quiet rest corner", detail: "Soft preference only", evidence: fixtureEvidence("Recorded place tag.", "UNVERIFIED"), longitude: 117.21, latitude: 39.09 },
    ],
  },
};

export const RECORDED_SCENARIOS: CapabilityScenario[] = [scenarioA, scenarioB, scenarioC, scenarioD, scenarioE];

export function scenarioById(id: string): CapabilityScenario {
  return RECORDED_SCENARIOS.find((scenario) => scenario.id === id) ?? RECORDED_SCENARIOS[0];
}

export function createRecordedFixtureAdapter(scenario: CapabilityScenario = scenarioA): CapabilityDataSource {
  return {
    sourceKind: "RECORDED_FIXTURE",
    async fetchCapabilities() {
      return scenario.capabilities;
    },
    async fetchPlanExplanation() {
      return scenario.plan;
    },
    async fetchRecoveryDiff() {
      return scenario.recovery;
    },
  };
}
