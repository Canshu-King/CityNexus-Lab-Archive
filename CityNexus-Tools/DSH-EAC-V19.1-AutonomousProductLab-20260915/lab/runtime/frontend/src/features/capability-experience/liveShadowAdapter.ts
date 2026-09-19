import type {
  CapabilityConstraint,
  CapabilityEvidence,
  CapabilityScope,
  CapabilitySource,
  CapabilityStrength,
  CapabilityKind,
  TravelerCapability,
} from "./types";
import { makeEvidence } from "./evidence";

export type CapabilitySourceMode = "LIVE_SHADOW" | "RECORDED_FIXTURE" | "OFFLINE_STALE";

export interface BackendCapabilityDto {
  id?: string;
  traveler_id?: string;
  journey_id?: string | null;
  code: string;
  class?: string;
  severity: "HARD" | "STRONG" | "SOFT";
  params?: Record<string, unknown>;
  scope?: "TRAVELER" | "JOURNEY";
  source?: string;
  provenance?: string;
  explicit?: boolean;
  confirmed?: boolean;
  active?: boolean;
  confirmed_at?: string | null;
  updated_at?: string | null;
  created_at?: string | null;
}

export interface CapabilityApiResponse {
  traveler_id?: string;
  journey_id?: string;
  capabilities?: BackendCapabilityDto[];
  summary?: Record<string, unknown>;
  traveler_twin?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface CapabilityShadowClient {
  getTravelerCapabilities(travelerId: string): Promise<CapabilityApiResponse>;
  getJourneyCapabilities(journeyId: string): Promise<CapabilityApiResponse>;
  confirmTravelerCapabilities(travelerId: string, capabilities: Array<Record<string, unknown>>): Promise<CapabilityApiResponse>;
  confirmJourneyCapabilities(journeyId: string, capabilities: Array<Record<string, unknown>>): Promise<CapabilityApiResponse>;
  getTravelerTwin(travelerId: string): Promise<Record<string, unknown>>;
}

export interface CapabilitySourceResult {
  mode: CapabilitySourceMode;
  capabilities: TravelerCapability[];
  fetchedAt: string;
  staleAt?: string;
  error?: string;
  contractGap?: string[];
  label: string;
}

const CACHE_KEY = "citynexus.v19_1.capability.cache.v1";

const CODE_LABELS: Record<string, { zh: string; en: string; kind: CapabilityKind }> = {
  STEP_FREE_REQUIRED: { zh: "无台阶通行", en: "Step-free access", kind: "HARD_ACCESSIBILITY_NEED" },
  AVOID_STAIRS: { zh: "避免楼梯", en: "Avoid stairs", kind: "HARD_ACCESSIBILITY_NEED" },
  MAX_WALKING_PER_LEG_M: { zh: "每段最大步行", en: "Max walking per leg", kind: "PHYSICAL_LIMIT" },
  MAX_CONTINUOUS_WALKING_MIN: { zh: "最长连续步行", en: "Max continuous walking", kind: "PHYSICAL_LIMIT" },
  MAX_DAILY_WALKING_M: { zh: "每日最大步行", en: "Max daily walking", kind: "PHYSICAL_LIMIT" },
  MIDDAY_REST_WINDOW: { zh: "中午休息", en: "Midday rest window", kind: "CARE_REQUIREMENT" },
  REST_EVERY_MIN: { zh: "休息频率", en: "Rest frequency", kind: "CARE_REQUIREMENT" },
  INFANT_NAP_WINDOW: { zh: "婴儿午睡窗", en: "Infant nap window", kind: "CARE_REQUIREMENT" },
  TOILET_BREAK_EVERY_MIN: { zh: "如厕/休息间隔", en: "Toilet break interval", kind: "CARE_REQUIREMENT" },
  STROLLER: { zh: "婴儿车", en: "Stroller", kind: "TRIP_CONTEXT" },
  LARGE_LUGGAGE: { zh: "大件行李", en: "Large luggage", kind: "TRIP_CONTEXT" },
  SLOW_PACE: { zh: "慢节奏", en: "Slow pace", kind: "SOFT_PREFERENCE" },
  QUIET_ENVIRONMENT: { zh: "安静环境", en: "Quiet environment", kind: "SOFT_PREFERENCE" },
  INDOOR_PREFERRED: { zh: "偏好室内", en: "Prefer indoor", kind: "SOFT_PREFERENCE" },
  SENSORY_LOW_STIMULATION: { zh: "低感官刺激", en: "Low sensory stimulation", kind: "SOFT_PREFERENCE" },
};

export function capabilityLabelForCode(code: string, locale: "zh-CN" | "en" = "zh-CN"): string {
  const entry = CODE_LABELS[code];
  if (!entry) return code.replaceAll("_", " ").toLowerCase();
  return locale === "zh-CN" ? entry.zh : entry.en;
}

function capabilityKindForCode(code: string): CapabilityKind {
  return CODE_LABELS[code]?.kind ?? "UNKNOWN_CAPABILITY";
}

function mapScope(scope: string | undefined): CapabilityScope {
  if (scope === "TRAVELER") return "TRAVELER";
  return "THIS_JOURNEY";
}

function mapSource(source: string | undefined): CapabilitySource {
  const value = String(source ?? "").toUpperCase();
  if (value === "USER_CONFIRMED" || value === "USER_STATED") return "TRAVELER_STATED";
  if (value === "SEMANTIC" || value === "COPILOT") return "COPILOT_DETECTED";
  if (value === "LEARNED_SOFT") return "LEARNED_SOFT";
  return "IMPORTED";
}

function isAccessibilityRequirement(code: string): boolean {
  return ["STEP_FREE_REQUIRED", "AVOID_STAIRS", "STROLLER", "LARGE_LUGGAGE"].includes(code);
}

function evidenceForCapability(dto: BackendCapabilityDto): CapabilityEvidence {
  const accessibility = isAccessibilityRequirement(dto.code);
  const summary = accessibility
    ? "Requirement recorded. Provider/route evidence is still required; this row is not an accessibility claim."
    : "Traveler-stated capability context; provider/planner evidence is not yet verified.";
  return makeEvidence(
    accessibility ? "NEEDS_LIVE_EVIDENCE" : "UNVERIFIED",
    summary,
    {
      kind: "LIVE",
      label: "LIVE_SHADOW",
      sourceSystem: "capability_api",
      observedAt: dto.updated_at ?? dto.confirmed_at ?? null,
      notes: "Capability rows come from the isolated V19 API. They do not contain provider accessibility evidence by themselves.",
    },
    {
      liveChecks: accessibility
        ? ["Provider/frozen accessibility tags must verify the relevant place or route."]
        : undefined,
    },
  );
}

function constraintsFromParams(code: string, params: Record<string, unknown> | undefined): CapabilityConstraint[] {
  const value = params ?? {};
  const constraints: CapabilityConstraint[] = [];
  const push = (key: string, operator: CapabilityConstraint["operator"], raw: unknown, unit?: string) => {
    if (raw === undefined || raw === null) return;
    constraints.push({
      key,
      operator,
      value: raw as CapabilityConstraint["value"],
      unit,
      hard: false,
    });
  };
  if (typeof value.max_m === "number") push("max_walking_per_leg_m", "LTE", value.max_m, "m");
  if (typeof value.max_min === "number") {
    if (code === "REST_EVERY_MIN" || code === "TOILET_BREAK_EVERY_MIN") push("rest_frequency_min", "LTE", value.max_min, "min");
    else push("max_continuous_walking_m", "LTE", value.max_min, "min");
  }
  if (code === "MIDDAY_REST_WINDOW" || code === "INFANT_NAP_WINDOW") {
    if (value.start || value.end) push("nap_window", "BETWEEN", [String(value.start ?? ""), String(value.end ?? "")]);
  }
  if (typeof value.present === "boolean") push("present", "REQUIRED", value.present);
  if (typeof value.preferred === "boolean") push("preferred", "REQUIRED", value.preferred);
  if (typeof value.requirement === "string") push("requirement", "REQUIRED", value.requirement);
  return constraints;
}

export function mapBackendCapability(dto: BackendCapabilityDto, locale: "zh-CN" | "en" = "zh-CN"): TravelerCapability {
  const code = String(dto.code);
  const source = mapSource(dto.source);
  const confirmed = Boolean(dto.confirmed);
  const severity = (dto.severity ?? "SOFT") as CapabilityStrength;
  return {
    id: dto.id ?? `${dto.scope ?? "JOURNEY"}:${code}`,
    kind: capabilityKindForCode(code),
    label: capabilityLabelForCode(code, locale),
    strength: severity,
    scope: mapScope(dto.scope),
    source,
    sourceLabel: source === "TRAVELER_STATED" ? "Traveler stated" : source,
    evidence: evidenceForCapability(dto),
    active: dto.active !== false,
    confirmed,
    explicit: dto.explicit !== false,
    learned: source === "LEARNED_SOFT",
    travelerStated: true,
    constraints: constraintsFromParams(code, dto.params),
    extra: {
      backend_code: code,
      backend_class: dto.class,
      backend_source: dto.source,
      backend_provenance: dto.provenance,
      backend_params: dto.params,
      backend_journey_id: dto.journey_id,
      backend_traveler_id: dto.traveler_id,
      labelEn: capabilityLabelForCode(code, "en"),
    },
  };
}


export function mapBackendCapabilities(
  payload: CapabilityApiResponse | undefined,
  locale: "zh-CN" | "en" = "zh-CN",
): TravelerCapability[] {
  const rows = Array.isArray(payload?.capabilities) ? payload?.capabilities : [];
  return rows
    .filter((row): row is BackendCapabilityDto => Boolean(row && row.code))
    .map((row) => mapBackendCapability(row, locale));
}

function readCache(): { capabilities: TravelerCapability[]; savedAt: string } | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { capabilities?: TravelerCapability[]; savedAt?: string };
    if (!Array.isArray(parsed.capabilities) || !parsed.savedAt) return null;
    return { capabilities: parsed.capabilities, savedAt: parsed.savedAt };
  } catch {
    return null;
  }
}

function writeCache(capabilities: TravelerCapability[]): string {
  const savedAt = new Date().toISOString();
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ capabilities, savedAt }));
  } catch {
    // Cache is best-effort. OFFLINE_STALE will report unavailable if absent.
  }
  return savedAt;
}

export async function loadCapabilitySource(
  client: CapabilityShadowClient,
  options: {
    mode: CapabilitySourceMode;
    travelerId?: string;
    journeyId?: string;
    locale?: "zh-CN" | "en";
    fixtureCapabilities?: TravelerCapability[];
    fetcher?: () => Promise<CapabilityApiResponse>;
  },
): Promise<CapabilitySourceResult> {
  const locale = options.locale ?? "zh-CN";
  const now = new Date().toISOString();
  if (options.mode === "RECORDED_FIXTURE") {
    return {
      mode: "RECORDED_FIXTURE",
      capabilities: options.fixtureCapabilities ?? [],
      fetchedAt: now,
      label: "RECORDED_FIXTURE",
      contractGap: ["Fixture mode is explicitly labelled and is not live planning authority."],
    };
  }
  if (options.mode === "OFFLINE_STALE") {
    const cached = readCache();
    if (!cached) {
      return {
        mode: "OFFLINE_STALE",
        capabilities: [],
        fetchedAt: now,
        label: "OFFLINE_STALE",
        error: "No last-known capability data in cache.",
      };
    }
    return {
      mode: "OFFLINE_STALE",
      capabilities: cached.capabilities,
      fetchedAt: cached.savedAt,
      staleAt: cached.savedAt,
      label: "OFFLINE_STALE",
      contractGap: ["Showing last-known authoritative data; not a live claim."],
    };
  }

  try {
    const response = options.fetcher
      ? await options.fetcher()
      : options.travelerId
        ? await client.getTravelerCapabilities(options.travelerId)
        : options.journeyId
          ? await client.getJourneyCapabilities(options.journeyId)
          : { capabilities: [] };
    const capabilities = mapBackendCapabilities(response, locale);
    const savedAt = writeCache(capabilities);
    return {
      mode: "LIVE_SHADOW",
      capabilities,
      fetchedAt: savedAt,
      label: "LIVE_SHADOW",
      contractGap: response.capabilities?.length
        ? []
        : ["Live contract responded with zero capability rows for this journey."],
    };
  } catch (error) {
    const cached = readCache();
    const message = error instanceof Error ? error.message : String(error);
    if (cached) {
      return {
        mode: "OFFLINE_STALE",
        capabilities: cached.capabilities,
        fetchedAt: cached.savedAt,
        staleAt: cached.savedAt,
        label: "OFFLINE_STALE",
        error: `LIVE_SHADOW failed (${message}); showing last-known data at ${cached.savedAt}.`,
        contractGap: ["Live backend unavailable. Cached data is stale and never labelled live."],
      };
    }
    return {
      mode: "LIVE_SHADOW",
      capabilities: [],
      fetchedAt: now,
      label: "LIVE_SHADOW",
      error: `LIVE_SHADOW unavailable: ${message}`,
      contractGap: ["No live capability backend and no cached last-known data. CONTRACT_NOT_AVAILABLE."],
    };
  }
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { headers: { Accept: "application/json" }, ...init });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${text.slice(0, 180)}`);
  }
  return (await response.json()) as T;
}

export function createHttpShadowClient(baseUrl = ""): CapabilityShadowClient & {
  getPlaceAccessibilityEvidence(placeId: string): Promise<Record<string, unknown>>;
  getJourneyAccessibilityEvidence(journeyId: string): Promise<Record<string, unknown>>;
  getCapabilityPlanImpact(journeyId: string, planVersionId?: string): Promise<Record<string, unknown>>;
} {
  const root = baseUrl.replace(/\/+$/, "");
  return {
    getTravelerCapabilities: (travelerId) => fetchJson(`${root}/api/v1/travelers/${encodeURIComponent(travelerId)}/capabilities`),
    getJourneyCapabilities: (journeyId) => fetchJson(`${root}/api/v1/journeys/${encodeURIComponent(journeyId)}/capabilities`),
    confirmTravelerCapabilities: (travelerId, capabilities) =>
      fetchJson(`${root}/api/v1/travelers/${encodeURIComponent(travelerId)}/capabilities/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(capabilities),
      }),
    confirmJourneyCapabilities: (journeyId, capabilities) =>
      fetchJson(`${root}/api/v1/journeys/${encodeURIComponent(journeyId)}/capabilities/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(capabilities),
      }),
    getTravelerTwin: (travelerId) => fetchJson(`${root}/api/v1/travelers/${encodeURIComponent(travelerId)}/traveler-twin`),
    getPlaceAccessibilityEvidence: (placeId) =>
      fetchJson(`${root}/api/v1/places/${encodeURIComponent(placeId)}/accessibility-evidence`),
    getJourneyAccessibilityEvidence: (journeyId) =>
      fetchJson(`${root}/api/v1/journeys/${encodeURIComponent(journeyId)}/accessibility-evidence`),
    getCapabilityPlanImpact: (journeyId, planVersionId) => {
      const query = planVersionId ? `?plan_version_id=${encodeURIComponent(planVersionId)}` : "";
      return fetchJson(`${root}/api/v1/journeys/${encodeURIComponent(journeyId)}/capability-plan-impact${query}`);
    },
  };
}

export function mapJourneySetupDraftToBackend(draft: {
  quickNeedIds: string[];
  advanced: {
    maxWalkingPerLegM?: number;
    maxContinuousWalkingM?: number;
    restFrequencyMin?: number;
    napWindow?: { start: string; end: string } | null;
    toiletFrequencyMin?: number;
    pace?: string;
    quietSensory?: boolean;
  };
}): Array<Record<string, unknown>> {
  const payload: Array<Record<string, unknown>> = [];
  const add = (code: string, klass: string, severity: string, params: Record<string, unknown>, scope = "JOURNEY") => {
    payload.push({
      code,
      class: klass,
      severity,
      params,
      scope,
      source: "USER_STATED",
      provenance: "USER_STATED",
      explicit: true,
      active: true,
      confirmed: false,
    });
  };
  for (const id of draft.quickNeedIds) {
    if (id === "less_walking") add("MAX_WALKING_PER_LEG_M", "PHYSICAL_LIMIT", "STRONG", { max_m: draft.advanced.maxWalkingPerLegM ?? null });
    if (id === "wheelchair_access") add("STEP_FREE_REQUIRED", "HARD_ACCESSIBILITY_NEED", "HARD", { requirement: "step_free" });
    if (id === "avoid_stairs") add("AVOID_STAIRS", "HARD_ACCESSIBILITY_NEED", "HARD", { avoid: true });
    if (id === "stroller") add("STROLLER", "TRIP_CONTEXT", "STRONG", { present: true });
    if (id === "large_luggage") add("LARGE_LUGGAGE", "TRIP_CONTEXT", "STRONG", { present: true });
    if (id === "midday_rest") add("MIDDAY_REST_WINDOW", "CARE_REQUIREMENT", "STRONG", { start: draft.advanced.napWindow?.start ?? "12:00", end: draft.advanced.napWindow?.end ?? "14:00" });
    if (id === "baby_nap") add("INFANT_NAP_WINDOW", "CARE_REQUIREMENT", "STRONG", { start: draft.advanced.napWindow?.start ?? "13:00", end: draft.advanced.napWindow?.end ?? "15:00" });
  }
  if (draft.advanced.maxContinuousWalkingM !== undefined) add("MAX_CONTINUOUS_WALKING_MIN", "PHYSICAL_LIMIT", "STRONG", { max_min: draft.advanced.maxContinuousWalkingM });
  if (draft.advanced.restFrequencyMin !== undefined) add("REST_EVERY_MIN", "CARE_REQUIREMENT", "STRONG", { max_min: draft.advanced.restFrequencyMin });
  if (draft.advanced.toiletFrequencyMin !== undefined) add("TOILET_BREAK_EVERY_MIN", "CARE_REQUIREMENT", "STRONG", { max_min: draft.advanced.toiletFrequencyMin });
  if (draft.advanced.pace) add("SLOW_PACE", "SOFT_PREFERENCE", "SOFT", { preferred: true });
  if (draft.advanced.quietSensory) add("QUIET_ENVIRONMENT", "SOFT_PREFERENCE", "SOFT", { preferred: true });
  return payload;
}
