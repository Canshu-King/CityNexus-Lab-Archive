/**
 * CityNexus V18.3 — Traveler Capability UX (experience layer).
 *
 * These contracts are deliberately separate from `src/types.ts`. They describe
 * what the traveler recognizes and wants Copilot to reference. They do not
 * mutate PlanVersion, Gateway, Guardian, or any backend schema.
 *
 * 中文说明：本文件仅定义体验层的能力键与元数据，不修改后端 schema。
 */

export type CapabilityLocale = "en" | "zh-CN";

export type LocalizedText = { en: string; zh: string };

/**
 * The three-category model used by setup and Copilot summary.
 *
 * - HARD_ACCESSIBILITY_NEED: never traded away automatically.
 * - PROTECTED_COMMITMENT: can be changed only through explicit approval.
 * - USER_PREFERENCE: soft signal used to rank alternatives.
 */
export type CapabilityCategory =
  | "USER_PREFERENCE"
  | "HARD_ACCESSIBILITY_NEED"
  | "PROTECTED_COMMITMENT";

/** Exactly the capability keys supported by V18.3. */
export type CapabilityKey =
  | "wheelchair_step_free"
  | "avoid_stairs"
  | "max_walking"
  | "elderly_rest"
  | "infant_nap"
  | "stroller"
  | "toilet_rest_stop"
  | "luggage"
  | "pace"
  | "quiet_sensory";

export type Pace = "relaxed" | "balanced" | "fast";
export type SensitivityLevel = "low" | "medium" | "high";

export interface ToggleCapabilityValue {
  kind: "toggle";
  enabled: boolean;
}

export interface NumberCapabilityValue {
  kind: "number";
  enabled: boolean;
  value: number;
  /** Always minutes in V18.3. The hard-threshold note lives on the definition. */
  unit: "minutes";
}

export interface ChoiceCapabilityValue {
  kind: "choice";
  value: Pace;
}

export interface SensitivityCapabilityValue {
  kind: "sensitivity";
  enabled: boolean;
  /** Optional sensitivity level. `null` means "recognized, level unspecified". */
  level: SensitivityLevel | null;
}

export type CapabilityValue =
  | ToggleCapabilityValue
  | NumberCapabilityValue
  | ChoiceCapabilityValue
  | SensitivityCapabilityValue;

/** Persisted experience state, keyed by capability key. */
export type Capabilities = Record<CapabilityKey, CapabilityValue>;

export const CAPABILITY_KEYS: readonly CapabilityKey[] = [
  "wheelchair_step_free",
  "avoid_stairs",
  "max_walking",
  "elderly_rest",
  "infant_nap",
  "stroller",
  "toilet_rest_stop",
  "luggage",
  "pace",
  "quiet_sensory",
];

export const PACE_VALUES: readonly Pace[] = ["relaxed", "balanced", "fast"];
export const SENSITIVITY_VALUES: readonly SensitivityLevel[] = ["low", "medium", "high"];

export interface PaceOption {
  value: Pace;
  label: LocalizedText;
}

export interface SensitivityOption {
  value: SensitivityLevel;
  label: LocalizedText;
}

export const PACE_OPTIONS: readonly PaceOption[] = [
  { value: "relaxed", label: { en: "Relaxed", zh: "从容" } },
  { value: "balanced", label: { en: "Balanced", zh: "均衡" } },
  { value: "fast", label: { en: "Fast", zh: "紧凑" } },
];

export const SENSITIVITY_OPTIONS: readonly SensitivityOption[] = [
  { value: "low", label: { en: "Low", zh: "低" } },
  { value: "medium", label: { en: "Medium", zh: "中" } },
  { value: "high", label: { en: "High", zh: "高" } },
];

export interface CapabilityCategoryMeta {
  key: CapabilityCategory;
  label: LocalizedText;
  badge: LocalizedText;
  description: LocalizedText;
  tone: "hard" | "protected" | "preference";
}

export const CATEGORY_ORDER: readonly CapabilityCategory[] = [
  "HARD_ACCESSIBILITY_NEED",
  "PROTECTED_COMMITMENT",
  "USER_PREFERENCE",
];

export const CATEGORY_META: Record<CapabilityCategory, CapabilityCategoryMeta> = {
  HARD_ACCESSIBILITY_NEED: {
    key: "HARD_ACCESSIBILITY_NEED",
    label: { en: "Hard accessibility need", zh: "硬性无障碍需求" },
    badge: { en: "HARD ACCESSIBILITY NEED", zh: "硬性无障碍需求" },
    description: {
      en: "Non-negotiable. CityNexus keeps these out of automatic trade-offs.",
      zh: "不可协商。CityNexus 不会将其放入自动取舍。",
    },
    tone: "hard",
  },
  PROTECTED_COMMITMENT: {
    key: "PROTECTED_COMMITMENT",
    label: { en: "Protected commitment", zh: "受保护承诺" },
    badge: { en: "PROTECTED COMMITMENT", zh: "受保护承诺" },
    description: {
      en: "Protected from silent compression. Changes require explicit approval.",
      zh: "不会被静默压缩。变更需要明确批准。",
    },
    tone: "protected",
  },
  USER_PREFERENCE: {
    key: "USER_PREFERENCE",
    label: { en: "Preference", zh: "偏好" },
    badge: { en: "PREFERENCE", zh: "偏好" },
    description: {
      en: "Soft signal used to rank alternatives. It may change in a preview.",
      zh: "用于排序替代方案的软信号，可在试算中变化。",
    },
    tone: "preference",
  },
};

export interface CapabilityDefinition {
  key: CapabilityKey;
  category: CapabilityCategory;
  /** Which setup-mode control the panel should render. */
  control: "toggle" | "number" | "select" | "sensitivity";
  label: LocalizedText;
  description: LocalizedText;
  /** Human-readable reason for the chosen category. Shown as a tooltip and in docs. */
  categoryRationale: LocalizedText;
  /** Numeric unit for `max_walking`; present only for number controls. */
  unit?: "minutes";
  /** Visible note: the number is a preference, but conflicts must be surfaced. */
  hardThresholdNote?: LocalizedText;
  min?: number;
  max?: number;
  step?: number;
  options?: readonly PaceOption[];
  sensitivityOptions?: readonly SensitivityOption[];
}

export const CAPABILITY_DEFINITIONS: Record<CapabilityKey, CapabilityDefinition> = {
  wheelchair_step_free: {
    key: "wheelchair_step_free",
    category: "HARD_ACCESSIBILITY_NEED",
    control: "toggle",
    label: { en: "Wheelchair step-free route", zh: "轮椅无台阶路线" },
    description: {
      en: "Every leg must be step-free and physically usable with a wheelchair.",
      zh: "每一段都必须无台阶，并可实际使用轮椅。",
    },
    categoryRationale: {
      en: "Mandatory hard need. It is never placed into a preference trade-off.",
      zh: "强制硬性需求，绝不进入偏好取舍。",
    },
  },
  avoid_stairs: {
    key: "avoid_stairs",
    category: "HARD_ACCESSIBILITY_NEED",
    control: "toggle",
    label: { en: "Avoid stairs", zh: "避免楼梯" },
    description: {
      en: "Prefer routes, stations, and venues without stairs or stepped access.",
      zh: "优先选择没有楼梯或台阶的路线、车站与场所。",
    },
    categoryRationale: {
      en: "Mandatory hard need. Stairs are treated as a route blocker, not a preference.",
      zh: "强制硬性需求。楼梯是路线阻断因素，而非偏好。",
    },
  },
  max_walking: {
    key: "max_walking",
    category: "USER_PREFERENCE",
    control: "number",
    label: { en: "Maximum walking", zh: "最大步行时间" },
    description: {
      en: "Preferred maximum total walking for the day. The value is a preference, but a hard threshold conflict must be surfaced.",
      zh: "当天偏好的最大总步行时间。该数值是偏好，但触及硬性阈值冲突时必须展示。",
    },
    categoryRationale: {
      en: "Numeric user preference with a hard conflict threshold note; it is not a backend constraint.",
      zh: "带硬性冲突阈值说明的数值偏好，不是后端约束。",
    },
    unit: "minutes",
    hardThresholdNote: {
      en: "Hard threshold note: if any candidate exceeds this number, CityNexus must show the conflict instead of silently trading it away.",
      zh: "硬性阈值说明：若候选方案超过此数值，CityNexus 必须展示冲突，而不是静默取舍。",
    },
    min: 5,
    max: 240,
    step: 5,
  },
  elderly_rest: {
    key: "elderly_rest",
    category: "PROTECTED_COMMITMENT",
    control: "toggle",
    label: { en: "Elderly rest break", zh: "长者休息" },
    description: {
      en: "Keep a comfortable rest window for an elderly traveler during the day.",
      zh: "为长者保留一天中舒适的休息时间窗。",
    },
    categoryRationale: {
      en: "Chosen as a protected commitment: declared rest windows are protected from automatic compression.",
      zh: "选择为受保护承诺：已声明的休息时间窗不会被自动压缩。",
    },
  },
  infant_nap: {
    key: "infant_nap",
    category: "PROTECTED_COMMITMENT",
    control: "toggle",
    label: { en: "Infant nap window", zh: "婴儿午睡时间" },
    description: {
      en: "Anchor the day around the infant nap window so it is not silently moved.",
      zh: "以婴儿午睡时间窗为锚点，避免被静默移动。",
    },
    categoryRationale: {
      en: "Chosen as a protected commitment: the nap window anchors the day and needs explicit approval to change.",
      zh: "选择为受保护承诺：午睡时间窗是一天的锚点，变更需明确批准。",
    },
  },
  stroller: {
    key: "stroller",
    category: "HARD_ACCESSIBILITY_NEED",
    control: "toggle",
    label: { en: "Stroller access", zh: "婴儿车通行" },
    description: {
      en: "Routes and vehicles must fit a stroller without stairs or unavoidable carrying.",
      zh: "路线与车辆必须可通行婴儿车，避免楼梯或必须搬抬。",
    },
    categoryRationale: {
      en: "Chosen as a hard need beyond the two mandatory keys because a stroller changes which routes are physically usable.",
      zh: "在两项强制键之外，选择为硬性需求：婴儿车会改变哪些路线可物理通行。",
    },
  },
  toilet_rest_stop: {
    key: "toilet_rest_stop",
    category: "PROTECTED_COMMITMENT",
    control: "toggle",
    label: { en: "Toilet / rest stop", zh: "厕所 / 休息站" },
    description: {
      en: "Plan a toilet or rest stop on legs longer than the traveler's comfortable interval.",
      zh: "在超过旅行者舒适间隔的行程段安排厕所或休息站。",
    },
    categoryRationale: {
      en: "Logistics need promoted to protected commitment because a missed stop affects health, dignity, and downstream timing.",
      zh: "物流需求提升为受保护承诺：错过休息站会影响健康、尊严与后续时间。",
    },
  },
  luggage: {
    key: "luggage",
    category: "USER_PREFERENCE",
    control: "toggle",
    label: { en: "Luggage-aware routing", zh: "行李友好路线" },
    description: {
      en: "Prefer routes, vehicles, and transfers that make luggage handling easier.",
      zh: "优先选择更便于处理行李的路线、车辆与换乘。",
    },
    categoryRationale: {
      en: "Logistics preference: it shapes vehicle, storage, and transfer choices but may be traded in a preview.",
      zh: "物流偏好：影响车辆、寄存与换乘选择，可在试算中被取舍。",
    },
  },
  pace: {
    key: "pace",
    category: "USER_PREFERENCE",
    control: "select",
    label: { en: "Travel pace", zh: "行程节奏" },
    description: {
      en: "Relaxed, balanced, or fast. This shapes timing and buffers, not protected commitments.",
      zh: "从容、均衡或紧凑。影响时间安排与缓冲，不改变受保护承诺。",
    },
    categoryRationale: {
      en: "Soft preference; it can change route timing but not hard needs or protected commitments.",
      zh: "软偏好：可改变路线时间，但不改变硬性需求或受保护承诺。",
    },
    options: PACE_OPTIONS,
  },
  quiet_sensory: {
    key: "quiet_sensory",
    category: "USER_PREFERENCE",
    control: "sensitivity",
    label: { en: "Quiet / sensory preference", zh: "安静 / 感官偏好" },
    description: {
      en: "Prefer quieter, lower-stimulation environments. Sensitivity level is optional.",
      zh: "偏好更安静、刺激更低的环境。感官敏感等级可选。",
    },
    categoryRationale: {
      en: "Soft preference with optional sensitivity level; it shapes environment scoring, never hard needs.",
      zh: "带可选敏感等级的软偏好，仅影响环境评分，不改变硬性需求。",
    },
    sensitivityOptions: SENSITIVITY_OPTIONS,
  },
};

export const CAPABILITY_STORAGE_KEY = "citynexus.v18.3.capabilities";

export const CAPABILITY_DISCLAIMER: LocalizedText = {
  en: "CityNexus keeps hard needs and protected commitments out of automatic trade-offs, but this reference UI does not mutate backend schema.",
  zh: "CityNexus 不会将硬性需求与受保护承诺放入自动取舍，但此参考界面不会修改后端 schema。",
};

export const CAPABILITY_AUTHORITY_NOTE: LocalizedText = {
  en: "Recognized reference, not a backend authority.",
  zh: "已识别参考，而非后端权威。",
};

export const CAPABILITY_NO_SCHEMA_NOTE: LocalizedText = {
  en: "Experience-layer reference only. Values are stored in localStorage; no backend schema or PlanVersion is changed.",
  zh: "仅为体验层参考。数值保存在 localStorage；不会修改后端 schema 或 PlanVersion。",
};

export interface CapabilitySummaryItem {
  key: CapabilityKey;
  category: CapabilityCategory;
  definition: CapabilityDefinition;
  value: CapabilityValue;
  displayValue: LocalizedText;
  recognized: boolean;
}

export interface CapabilitySummaryModel {
  /** All ten keys, including unrecognized ones. */
  all: CapabilitySummaryItem[];
  hardAccessibilityNeeds: CapabilitySummaryItem[];
  protectedCommitments: CapabilitySummaryItem[];
  preferences: CapabilitySummaryItem[];
  recognizedCount: number;
  disclaimer: LocalizedText;
  authorityNote: LocalizedText;
  noSchemaNote: LocalizedText;
}

/* ------------------------------------------------------------------ */
/* Small pure helpers                                                  */
/* ------------------------------------------------------------------ */

const CAPABILITY_KEY_SET = new Set<string>(CAPABILITY_KEYS);
const CAPABILITY_CATEGORY_SET = new Set<string>(CATEGORY_ORDER);

export function isCapabilityKey(value: unknown): value is CapabilityKey {
  return typeof value === "string" && CAPABILITY_KEY_SET.has(value);
}

export function isCapabilityCategory(value: unknown): value is CapabilityCategory {
  return typeof value === "string" && CAPABILITY_CATEGORY_SET.has(value);
}

export function isPace(value: unknown): value is Pace {
  return typeof value === "string" && (PACE_VALUES as readonly string[]).includes(value);
}

export function isSensitivityLevel(value: unknown): value is SensitivityLevel {
  return typeof value === "string" && (SENSITIVITY_VALUES as readonly string[]).includes(value);
}

export function getCapabilityDefinition(key: CapabilityKey): CapabilityDefinition {
  return CAPABILITY_DEFINITIONS[key];
}

export function getCapabilityCategory(key: CapabilityKey): CapabilityCategory {
  return CAPABILITY_DEFINITIONS[key].category;
}

export function pickLocalized(text: LocalizedText, locale: CapabilityLocale = "en"): string {
  return locale === "zh-CN" ? text.zh : text.en;
}

export function createDefaultCapabilities(): Capabilities {
  return {
    wheelchair_step_free: { kind: "toggle", enabled: false },
    avoid_stairs: { kind: "toggle", enabled: false },
    max_walking: { kind: "number", enabled: false, value: 30, unit: "minutes" },
    elderly_rest: { kind: "toggle", enabled: false },
    infant_nap: { kind: "toggle", enabled: false },
    stroller: { kind: "toggle", enabled: false },
    toilet_rest_stop: { kind: "toggle", enabled: false },
    luggage: { kind: "toggle", enabled: false },
    pace: { kind: "choice", value: "balanced" },
    quiet_sensory: { kind: "sensitivity", enabled: false, level: null },
  };
}

/** A frozen snapshot for read-only consumers and tests. */
export const DEFAULT_CAPABILITIES: Capabilities = Object.freeze(
  createDefaultCapabilities(),
) as Capabilities;

export function isCapabilityRecognized(value: CapabilityValue): boolean {
  switch (value.kind) {
    case "toggle":
      return value.enabled;
    case "number":
      return value.enabled;
    case "choice":
      return true;
    case "sensitivity":
      return value.enabled;
    default:
      return false;
  }
}

function paceLabel(value: Pace): LocalizedText {
  return PACE_OPTIONS.find((option) => option.value === value)?.label ?? { en: value, zh: value };
}

function sensitivityLabel(value: SensitivityLevel): LocalizedText {
  return SENSITIVITY_OPTIONS.find((option) => option.value === value)?.label ?? { en: value, zh: value };
}

export function describeCapabilityValue(value: CapabilityValue): LocalizedText {
  switch (value.kind) {
    case "toggle":
      return value.enabled
        ? { en: "Recognized", zh: "已识别" }
        : { en: "Not recognized", zh: "未识别" };
    case "number": {
      const minutes = Number.isFinite(value.value) ? value.value : 0;
      return {
        en: `${minutes} min`,
        zh: `${minutes} 分钟`,
      };
    }
    case "choice":
      return paceLabel(value.value);
    case "sensitivity": {
      if (!value.enabled) return { en: "Not recognized", zh: "未识别" };
      if (!value.level) return { en: "Level not specified", zh: "未指定等级" };
      return sensitivityLabel(value.level);
    }
    default:
      return { en: "Not recognized", zh: "未识别" };
  }
}
