import type { CapabilitySourceMode } from "./liveShadowAdapter";

export interface ProviderEvidenceRaw {
  key: string | null;
  value: string | null;
}

export interface ProviderEvidenceItem {
  state: "ACCESSIBILITY_VERIFIED" | "ACCESSIBILITY_UNVERIFIED" | "ACCESSIBILITY_CONFLICT" | "NEEDS_LIVE_EVIDENCE";
  code: string;
  subject: string;
  summary: string;
  raw: ProviderEvidenceRaw;
  provider: string;
  source_key: string;
  place_id?: string | null;
  city_code?: string | null;
  captured_at: string;
  confidence_type: string;
  provenance: Record<string, unknown>;
}

export interface ProviderEvidenceResponse {
  place_id?: string;
  place_name?: string;
  journey_id?: string;
  city_code?: string;
  provider?: string;
  source_key?: string;
  captured_at?: string | null;
  items?: ProviderEvidenceItem[];
  overall_state?: ProviderEvidenceItem["state"];
  unknown_is_not_accessible?: boolean;
  [key: string]: unknown;
}

export interface ProviderEvidenceResult {
  mode: CapabilitySourceMode;
  items: ProviderEvidenceItem[];
  overallState: ProviderEvidenceItem["state"];
  fetchedAt: string;
  staleAt?: string;
  label: string;
  error?: string;
  contractGap?: string[];
}

const CACHE_KEY = "citynexus.v19_1.provider_evidence.cache.v1";

export function resolveOverallState(items: ProviderEvidenceItem[]): ProviderEvidenceItem["state"] {
  const states = new Set(items.map((item) => item.state));
  if (states.has("ACCESSIBILITY_CONFLICT")) return "ACCESSIBILITY_CONFLICT";
  if (states.has("NEEDS_LIVE_EVIDENCE")) return "NEEDS_LIVE_EVIDENCE";
  if (states.has("ACCESSIBILITY_UNVERIFIED")) return "ACCESSIBILITY_UNVERIFIED";
  if (states.has("ACCESSIBILITY_VERIFIED")) return "ACCESSIBILITY_VERIFIED";
  return "NEEDS_LIVE_EVIDENCE";
}

function readCache(): { items: ProviderEvidenceItem[]; savedAt: string } | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { items?: ProviderEvidenceItem[]; savedAt?: string };
    if (!Array.isArray(parsed.items) || !parsed.savedAt) return null;
    return { items: parsed.items, savedAt: parsed.savedAt };
  } catch {
    return null;
  }
}

function writeCache(items: ProviderEvidenceItem[]): string {
  const savedAt = new Date().toISOString();
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ items, savedAt }));
  } catch {
    // Best-effort cache only.
  }
  return savedAt;
}

function normalizeResponse(response: ProviderEvidenceResponse): ProviderEvidenceItem[] {
  const rows = Array.isArray(response.items) ? response.items : [];
  return rows.filter((item): item is ProviderEvidenceItem => Boolean(item && item.state && item.code));
}

export async function loadProviderEvidence(
  options: {
    mode: CapabilitySourceMode;
    placeId?: string;
    journeyId?: string;
    fetcher: () => Promise<ProviderEvidenceResponse>;
    fixtureItems?: ProviderEvidenceItem[];
  },
): Promise<ProviderEvidenceResult> {
  const now = new Date().toISOString();
  if (options.mode === "RECORDED_FIXTURE") {
    const items = options.fixtureItems ?? [];
    return {
      mode: "RECORDED_FIXTURE",
      items,
      overallState: resolveOverallState(items),
      fetchedAt: now,
      label: "RECORDED_FIXTURE",
      contractGap: ["Provider evidence fixture mode is explicitly labelled and not a live claim."],
    };
  }
  if (options.mode === "OFFLINE_STALE") {
    const cached = readCache();
    if (!cached) {
      return {
        mode: "OFFLINE_STALE",
        items: [],
        overallState: "NEEDS_LIVE_EVIDENCE",
        fetchedAt: now,
        label: "OFFLINE_STALE",
        error: "No last-known provider evidence cache.",
      };
    }
    return {
      mode: "OFFLINE_STALE",
      items: cached.items,
      overallState: resolveOverallState(cached.items),
      fetchedAt: cached.savedAt,
      staleAt: cached.savedAt,
      label: "OFFLINE_STALE",
      contractGap: ["Showing last-known provider evidence; not a live provider response."],
    };
  }
  try {
    const response = await options.fetcher();
    const items = normalizeResponse(response);
    const savedAt = writeCache(items);
    return {
      mode: "LIVE_SHADOW",
      items,
      overallState: response.overall_state ?? resolveOverallState(items),
      fetchedAt: savedAt,
      label: "LIVE_SHADOW",
      contractGap: items.length ? [] : ["Live accessibility-evidence contract returned no facts."],
    };
  } catch (error) {
    const cached = readCache();
    const message = error instanceof Error ? error.message : String(error);
    if (cached) {
      return {
        mode: "OFFLINE_STALE",
        items: cached.items,
        overallState: resolveOverallState(cached.items),
        fetchedAt: cached.savedAt,
        staleAt: cached.savedAt,
        label: "OFFLINE_STALE",
        error: `LIVE_SHADOW provider evidence failed (${message}); showing last-known data at ${cached.savedAt}.`,
      };
    }
    return {
      mode: "LIVE_SHADOW",
      items: [],
      overallState: "NEEDS_LIVE_EVIDENCE",
      fetchedAt: now,
      label: "LIVE_SHADOW",
      error: `LIVE_SHADOW provider evidence unavailable: ${message}`,
      contractGap: ["CONTRACT_NOT_AVAILABLE: accessibility evidence endpoint did not answer."],
    };
  }
}
