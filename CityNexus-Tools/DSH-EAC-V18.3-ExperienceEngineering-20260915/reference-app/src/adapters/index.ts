/**
 * Adapter layer barrel.
 *
 * This module deliberately contains no JSX, so it can be imported by both the
 * browser bundle and the `node --experimental-strip-types` contract test.
 * The React bindings live in `ExperienceAdapterContext.tsx`, which imports
 * `createExperienceAdapter` from here.
 */

import { LiveCityNexusAdapter } from "./liveCityNexusAdapter";
import { OfflineSnapshotAdapter } from "./offlineSnapshotAdapter";
import { RecordedFixtureAdapter } from "./recordedFixtureAdapter";
import type { AdapterMode, ExperienceAdapter } from "./contract";

export type {
  AdapterMode,
  ApprovalDecisionInput,
  ApprovalDecisionResult,
  CopilotMissionStart,
  ExperienceAdapter,
  MapState,
  NormalizedAgentEvent,
  NormalizedEventType,
  NormalizedProposal,
  NormalizedRun,
  NormalizedRunStatus,
  RecordedScenarioSummary,
  RunEventHandlers,
  RunSubscription,
  RuntimeStatusInfo,
  StopResult,
} from "./contract";

export { LiveCityNexusAdapter, AdapterHttpError } from "./liveCityNexusAdapter";
export type {
  EventSourceFactory,
  EventSourceLike,
  LiveCityNexusOptions,
  LiveDiagnostic,
  LiveMessageEvent,
} from "./liveCityNexusAdapter";
export { OfflineSnapshotAdapter } from "./offlineSnapshotAdapter";
export { RecordedFixtureAdapter, buildFixtureMapState, normalizedFixtureEvents } from "./recordedFixtureAdapter";
export type { RecordedRunSubscription, RecordedScenarioKey } from "./recordedFixtureAdapter";
export type { OfflineRunSubscription } from "./offlineSnapshotAdapter";
export {
  AgentEventStore,
  EventStore,
  buildNormalizedRun,
  compareNormalizedEvents,
  deriveRunStatus,
} from "./eventStore";
export type { AppendOptions, BuildRunInput, EventStoreOptions } from "./eventStore";
export {
  NORMALIZED_EVENT_TYPES,
  eventNameFromRaw,
  isIgnoredRawEvent,
  normalizeAgentEvent,
  normalizeEventBatch,
  normalizeEventType,
  normalizeRawEvent,
  normalizeRawEvents,
  safeSummary,
  toolNameFromRaw,
} from "./normalize";
export type { NormalizeOptions, RawAgentEvent } from "./normalize";

function adapterModeFromLocation(): AdapterMode | null {
  if (typeof window === "undefined") return null;
  const value = new URLSearchParams(window.location.search).get("adapter");
  return value === "live" || value === "offline" || value === "recorded" ? value : null;
}

function isBrowserOffline(): boolean {
  return typeof navigator !== "undefined" && navigator.onLine === false;
}

/**
 * Choose an adapter implementation.
 *
 * - `?adapter=live` -> LiveCityNexusAdapter
 * - `?adapter=offline` or `navigator.onLine === false` -> OfflineSnapshotAdapter
 * - default -> RecordedFixtureAdapter
 */
export function createExperienceAdapter(mode?: AdapterMode): ExperienceAdapter {
  const requested = mode ?? adapterModeFromLocation();
  if (requested === "live") return new LiveCityNexusAdapter();
  if (requested === "offline") return new OfflineSnapshotAdapter();
  if (isBrowserOffline()) return new OfflineSnapshotAdapter();
  return new RecordedFixtureAdapter();
}
