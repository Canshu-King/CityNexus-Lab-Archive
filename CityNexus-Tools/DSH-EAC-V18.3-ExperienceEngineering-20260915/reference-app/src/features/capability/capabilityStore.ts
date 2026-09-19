/**
 * CityNexus V18.3 — capability persistence and summary helpers.
 *
 * localStorage key: `citynexus.v18.3.capabilities`
 * 中文说明：仅使用 localStorage，不触碰后端 schema。
 */

import {
  CAPABILITY_AUTHORITY_NOTE,
  CAPABILITY_DEFINITIONS,
  CAPABILITY_DISCLAIMER,
  CAPABILITY_KEYS,
  CAPABILITY_NO_SCHEMA_NOTE,
  CAPABILITY_STORAGE_KEY,
  createDefaultCapabilities,
  describeCapabilityValue,
  isCapabilityRecognized,
  isPace,
  isSensitivityLevel,
  type Capabilities,
  type CapabilityKey,
  type CapabilitySummaryItem,
  type CapabilitySummaryModel,
  type CapabilityValue,
} from "./capabilityTypes";

export { CAPABILITY_STORAGE_KEY };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** Deep clone in the experience layer so callers never share value objects. */
export function cloneCapabilities(source: Capabilities): Capabilities {
  const next = {} as Capabilities;
  for (const key of CAPABILITY_KEYS) {
    const value = source[key];
    switch (value.kind) {
      case "toggle":
        next[key] = { kind: "toggle", enabled: value.enabled };
        break;
      case "number":
        next[key] = {
          kind: "number",
          enabled: value.enabled,
          value: value.value,
          unit: "minutes",
        };
        break;
      case "choice":
        next[key] = { kind: "choice", value: value.value };
        break;
      case "sensitivity":
        next[key] = { kind: "sensitivity", enabled: value.enabled, level: value.level };
        break;
    }
  }
  return next;
}

function normalizeValue(key: CapabilityKey, raw: unknown): CapabilityValue | null {
  const definition = CAPABILITY_DEFINITIONS[key];

  if (definition.control === "toggle") {
    if (typeof raw === "boolean") return { kind: "toggle", enabled: raw };
    if (isRecord(raw) && typeof raw.enabled === "boolean") {
      return { kind: "toggle", enabled: raw.enabled };
    }
    return null;
  }

  if (definition.control === "number") {
    let candidate: unknown = raw;
    let enabled = true;
    if (isRecord(raw)) {
      candidate = raw.value;
      if (typeof raw.enabled === "boolean") enabled = raw.enabled;
    }
    if (typeof candidate === "string" && candidate.trim() !== "") candidate = Number(candidate);
    if (typeof candidate !== "number" || !Number.isFinite(candidate)) return null;
    const min = definition.min ?? 5;
    const max = definition.max ?? 240;
    const value = Math.min(max, Math.max(min, Math.round(candidate)));
    return { kind: "number", enabled, value, unit: "minutes" };
  }

  if (definition.control === "select") {
    const candidate = isRecord(raw) ? raw.value : raw;
    if (!isPace(candidate)) return null;
    return { kind: "choice", value: candidate };
  }

  // sensitivity control
  if (typeof raw === "boolean") return { kind: "sensitivity", enabled: raw, level: null };
  if (isRecord(raw)) {
    const enabled = typeof raw.enabled === "boolean" ? raw.enabled : false;
    const level = raw.level;
    if (level == null) return { kind: "sensitivity", enabled, level: null };
    return {
      kind: "sensitivity",
      enabled,
      level: isSensitivityLevel(level) ? level : null,
    };
  }
  return null;
}

/** Normalizes unknown localStorage JSON into a complete, safe state. */
export function normalizeCapabilities(raw: unknown): Capabilities {
  const next = createDefaultCapabilities();
  if (!isRecord(raw)) return next;
  for (const key of CAPABILITY_KEYS) {
    const normalized = normalizeValue(key, raw[key]);
    if (normalized) next[key] = normalized;
  }
  return next;
}

function resolveStorage(storage?: Storage | null): Storage | null {
  if (storage) return storage;
  if (typeof window !== "undefined" && window.localStorage) return window.localStorage;
  // Useful for isolated tests that provide a global localStorage mock.
  if (typeof localStorage !== "undefined") return localStorage;
  return null;
}

export function loadCapabilities(storage?: Storage | null): Capabilities {
  const target = resolveStorage(storage);
  if (!target) return createDefaultCapabilities();
  try {
    const raw = target.getItem(CAPABILITY_STORAGE_KEY);
    if (!raw) return createDefaultCapabilities();
    return normalizeCapabilities(JSON.parse(raw));
  } catch {
    // Corrupt or unavailable storage falls back to defaults; never throw at UI level.
    return createDefaultCapabilities();
  }
}

export function saveCapabilities(capabilities: Capabilities, storage?: Storage | null): boolean {
  const target = resolveStorage(storage);
  if (!target) return false;
  try {
    target.setItem(CAPABILITY_STORAGE_KEY, JSON.stringify(capabilities));
    return true;
  } catch {
    return false;
  }
}

export function summarizeCapabilities(
  capabilities?: Partial<Capabilities> | null,
): CapabilitySummaryModel {
  const normalized = normalizeCapabilities(capabilities ?? loadCapabilities());

  const all: CapabilitySummaryItem[] = CAPABILITY_KEYS.map((key) => {
    const definition = CAPABILITY_DEFINITIONS[key];
    const value = normalized[key];
    return {
      key,
      category: definition.category,
      definition,
      value,
      displayValue: describeCapabilityValue(value),
      recognized: isCapabilityRecognized(value),
    };
  });

  const recognized = all.filter((item) => item.recognized);
  return {
    all,
    hardAccessibilityNeeds: recognized.filter(
      (item) => item.category === "HARD_ACCESSIBILITY_NEED",
    ),
    protectedCommitments: recognized.filter(
      (item) => item.category === "PROTECTED_COMMITMENT",
    ),
    preferences: recognized.filter((item) => item.category === "USER_PREFERENCE"),
    recognizedCount: recognized.length,
    disclaimer: CAPABILITY_DISCLAIMER,
    authorityNote: CAPABILITY_AUTHORITY_NOTE,
    noSchemaNote: CAPABILITY_NO_SCHEMA_NOTE,
  };
}
