/**
 * Runtime Adapter Layer contract test.
 *
 * Run with:
 *   node --experimental-strip-types scripts/adapter-contract-test.ts
 *
 * No external dependencies. Uses `node:assert/strict`.
 *
 * The adapter sources use the same extensionless relative imports as the rest
 * of the Vite app, while Node ESM requires explicit extensions. A tiny resolve
 * hook adds `.ts` for extensionless relative specifiers so the reference
 * implementation can be exercised unchanged.
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { registerHooks } from "node:module";

// ---------------------------------------------------------------------------
// Node resolution bridge: allow the adapters' extensionless relative imports.
// ---------------------------------------------------------------------------
registerHooks({
  resolve(
    specifier: string,
    context: unknown,
    nextResolve: (specifier: string, context: unknown) => unknown,
  ) {
    if (specifier.startsWith(".") && !/\.[a-zA-Z]+$/.test(specifier)) {
      try {
        return nextResolve(specifier, context);
      } catch {
        return nextResolve(`${specifier}.ts`, context);
      }
    }
    return nextResolve(specifier, context);
  },
});

// ---------------------------------------------------------------------------
// Browser-style requestAnimationFrame shim for Node. The recorded adapter
// prefers rAF; the shim drives frames from microtasks so no timer is needed.
// ---------------------------------------------------------------------------
let frameId = 0;
(globalThis as Record<string, unknown>).requestAnimationFrame = (callback: (time: number) => void) => {
  const id = (frameId += 1);
  queueMicrotask(() => callback(Date.now()));
  return id;
};
(globalThis as Record<string, unknown>).cancelAnimationFrame = () => undefined;

const normalizeModule = await import("../src/adapters/normalize.ts");
const eventStoreModule = await import("../src/adapters/eventStore.ts");
const recordedModule = await import("../src/adapters/recordedFixtureAdapter.ts");
const offlineModule = await import("../src/adapters/offlineSnapshotAdapter.ts");
const liveModule = await import("../src/adapters/liveCityNexusAdapter.ts");

const { normalizeRawEvent } = normalizeModule;
const { EventStore } = eventStoreModule;
const { RecordedFixtureAdapter } = recordedModule;
const { OfflineSnapshotAdapter } = offlineModule;
const { LiveCityNexusAdapter } = liveModule;

const RECORDED_RUN_ID = "run-fixture-hermes-20260915-01";

function section(name: string): void {
  console.log(`- ${name}`);
}

async function testNormalization(): Promise<void> {
  section("normalization boundary");

  // Unknown event names normalize to `unknown` and are preserved.
  const unknown = normalizeRawEvent({ event_type: "totally.weird.event" });
  assert.ok(unknown, "unknown event should normalize, not throw");
  assert.equal(unknown.event_type, "unknown");
  assert.equal(unknown.unknown, true);
  assert.equal(unknown.raw_event_type, "totally.weird.event");

  // Known noise is ignored.
  for (const name of ["message.delta", "reasoning.delta", "content.delta", "heartbeat"]) {
    assert.equal(normalizeRawEvent({ event_type: name, delta: "x" }), null, `${name} must be ignored`);
  }
  assert.equal(normalizeRawEvent({ event: "reasoning_available" }), null);

  // Missing optional fields receive safe defaults.
  const missing = normalizeRawEvent({ event_type: "tool.started" });
  assert.ok(missing);
  assert.equal(missing.sequence_no, 0);
  assert.equal(missing.tool_name, null);
  assert.equal(missing.duration_ms, null);
  assert.equal(missing.result_summary, null);
  assert.equal(missing.policy_decision, null);
  assert.equal(missing.approval_id, undefined);
  assert.equal(missing.proposal_id, undefined);
  assert.equal(missing.mission_id, undefined);
  assert.equal(missing.status, "started");
  assert.equal(typeof missing.timestamp, "string");
  assert.equal(missing.source, "RECORDED_FIXTURE");
  assert.equal(missing.unknown, false);

  // Semantic aliases and namespaced tool names.
  assert.equal(normalizeRawEvent({ event_type: "run_started" })?.event_type, "run.started");
  assert.equal(normalizeRawEvent({ event_type: "approval_requested" })?.event_type, "approval.required");
  const namespaced = normalizeRawEvent({
    event_type: "tool.completed",
    tool_name: "citynexus__search_city_services",
    duration: 0.62,
    status: "completed",
  });
  assert.ok(namespaced);
  assert.equal(namespaced.tool_name, "search_city_services");
  assert.equal(namespaced.duration_ms, 620);
  assert.equal(namespaced.event_type, "tool.completed");

  // Missing event names degrade to run.started, mirroring the server contract.
  assert.equal(normalizeRawEvent({})?.event_type, "run.started");

  // Hostile input never throws.
  assert.equal(normalizeRawEvent(null), null);
  assert.equal(normalizeRawEvent("nope"), null);
  const hostile = normalizeRawEvent({ event_type: {}, timestamp: {} });
  assert.ok(hostile, "hostile payload should still produce an event");
  assert.equal(hostile.event_type, "unknown");

  // Source is stamped by the caller.
  assert.equal(normalizeRawEvent({ event_type: "run.started" }, { source: "LIVE" })?.source, "LIVE");
  assert.equal(normalizeRawEvent({ event_type: "run.started" }, { source: "OFFLINE" })?.source, "OFFLINE");
}

async function testEventStore(): Promise<void> {
  section("event store dedupe and ordering");

  const store = new EventStore({ source: "RECORDED_FIXTURE" });
  const first = store.append({
    id: "evt-a",
    event_type: "run.started",
    run_id: "run-1",
    sequence_no: 1,
    timestamp: "2026-01-01T00:00:00.000Z",
  });
  assert.equal(first.length, 1);
  const duplicate = store.append({
    id: "evt-a",
    event_type: "run.started",
    run_id: "run-1",
    sequence_no: 1,
    timestamp: "2026-01-01T00:00:00.000Z",
  });
  assert.equal(duplicate.length, 0, "duplicate id must not be inserted");
  assert.equal(store.snapshot().length, 1);

  // Out-of-order arrival is returned in stable sequence order.
  const store2 = new EventStore({ source: "LIVE" });
  const inserted = store2.append([
    { id: "evt-c", event_type: "tool.completed", run_id: "r", sequence_no: 3, timestamp: "2026-01-01T00:00:03.000Z" },
    { id: "evt-a", event_type: "run.started", run_id: "r", sequence_no: 1, timestamp: "2026-01-01T00:00:01.000Z" },
    { id: "evt-b", event_type: "tool.started", run_id: "r", sequence_no: 2, timestamp: "2026-01-01T00:00:02.000Z" },
  ]);
  assert.deepEqual(
    inserted.map((event) => event.sequence_no),
    [1, 2, 3],
    "newly inserted events must be emitted in stable order",
  );
  assert.deepEqual(
    store2.snapshot().map((event) => event.sequence_no),
    [1, 2, 3],
  );
  assert.equal(store2.getLastSequence(), 3);

  // Same sequence number -> timestamp order.
  const store3 = new EventStore({ source: "LIVE" });
  store3.append([
    { id: "z", event_type: "tool.started", run_id: "r", sequence_no: 0, timestamp: "2026-01-01T00:00:03.000Z" },
    { id: "x", event_type: "tool.started", run_id: "r", sequence_no: 0, timestamp: "2026-01-01T00:00:01.000Z" },
    { id: "y", event_type: "tool.started", run_id: "r", sequence_no: 0, timestamp: "2026-01-01T00:00:02.000Z" },
  ]);
  assert.deepEqual(
    store3.snapshot().map((event) => event.id),
    ["x", "y", "z"],
  );

  // Emission callback only sees newly inserted events.
  const emitted: number[] = [];
  const store4 = new EventStore({
    source: "LIVE",
    onInsert: (events) => emitted.push(...events.map((event) => event.sequence_no)),
  });
  store4.append([
    { id: "p1", event_type: "tool.started", run_id: "p", sequence_no: 1, timestamp: "2026-01-01T00:00:01.000Z" },
    { id: "p2", event_type: "tool.started", run_id: "p", sequence_no: 2, timestamp: "2026-01-01T00:00:02.000Z" },
  ]);
  store4.append({ id: "p2", event_type: "tool.started", run_id: "p", sequence_no: 2, timestamp: "2026-01-01T00:00:02.000Z" });
  assert.deepEqual(emitted, [1, 2]);

  // Status derivation and clear().
  const statusStore = new EventStore({ source: "LIVE" });
  statusStore.append([
    { id: "s1", event_type: "run.started", run_id: "s", sequence_no: 1, timestamp: "2026-01-01T00:00:01.000Z" },
    { id: "s2", event_type: "run.completed", run_id: "s", sequence_no: 2, timestamp: "2026-01-01T00:00:02.000Z" },
  ]);
  assert.equal(statusStore.getStatus(), "success");
  statusStore.clear();
  assert.equal(statusStore.snapshot().length, 0);
  assert.equal(statusStore.getLastSequence(), 0);
  assert.equal(statusStore.getStatus(), "idle");

  // 1000-event performance smoke.
  const perf = new EventStore({ source: "LIVE" });
  const startedAt = Date.now();
  for (let index = 1; index <= 1000; index += 1) {
    perf.append({
      id: `perf-${index}`,
      event_type: "tool.started",
      run_id: "perf-run",
      sequence_no: index,
      timestamp: new Date(1_700_000_000_000 + index).toISOString(),
      tool_name: `tool-${index % 10}`,
    });
  }
  const elapsed = Date.now() - startedAt;
  assert.equal(perf.snapshot().length, 1000);
  assert.ok(elapsed < 2000, `1000-event append took ${elapsed}ms`);
}

async function testRecordedAdapter(): Promise<void> {
  section("recorded fixture adapter");

  const adapter = new RecordedFixtureAdapter();
  assert.equal(adapter.mode, "recorded");
  assert.equal(adapter.source, "RECORDED_FIXTURE");

  const scenarios = adapter.listRecordedScenarios();
  const byKey = new Map(scenarios.map((scenario) => [scenario.key, scenario]));
  assert.equal(byKey.get("completed")?.event_count, 14);
  assert.equal(byKey.get("completed")?.run_status, "approval_required");
  assert.equal(byKey.get("approved")?.event_count, 15);
  assert.equal(byKey.get("approved")?.run_status, "success");
  assert.equal(byKey.get("failed")?.event_count, 6);
  assert.equal(byKey.get("failed")?.run_status, "failed");
  assert.equal(byKey.get("stopped")?.event_count, 5);
  assert.equal(byKey.get("stopped")?.run_status, "stopped");

  // Code scan: recorded replay must not generate progress with timer APIs.
  const recordedSource = readFileSync(
    new URL("../src/adapters/recordedFixtureAdapter.ts", import.meta.url),
    "utf8",
  );
  assert.equal(
    /setTimeout|setInterval/.test(recordedSource),
    false,
    "recorded replay must not reference timer APIs",
  );
  assert.ok(
    recordedSource.includes("requestAnimationFrame"),
    "recorded replay must be driven by requestAnimationFrame",
  );

  adapter.selectRecordedScenario("completed");
  const run = await adapter.getRun(RECORDED_RUN_ID);
  assert.ok(run, "completed fixture run must resolve");
  assert.equal(run?.source, "RECORDED_FIXTURE");
  assert.equal(run?.status, "approval_required");
  assert.equal(run?.tool_count, 4);

  // Replay emits every recorded event once, in order, as RECORDED_FIXTURE.
  const received: number[] = [];
  const sources = new Set<string>();
  let lastStatus = "";
  const subscription = adapter.subscribeRunEvents(run!.run_id, {
    onEvent: (event) => {
      received.push(event.sequence_no);
      sources.add(event.source);
    },
    onStatusChange: (next) => {
      lastStatus = next.status;
    },
  });
  assert.equal(subscription.isLive(), false);
  await subscription.whenComplete();
  assert.deepEqual(
    received,
    Array.from({ length: 14 }, (_, index) => index + 1),
  );
  assert.deepEqual([...sources], ["RECORDED_FIXTURE"]);
  assert.equal(lastStatus, "approval_required");

  // since_sequence resumes after the cursor.
  const resumed: number[] = [];
  const resumedSub = adapter.subscribeRunEvents(
    run!.run_id,
    { onEvent: (event) => resumed.push(event.sequence_no) },
    { since_sequence: 10 },
  );
  await resumedSub.whenComplete();
  assert.deepEqual(resumed, [11, 12, 13, 14]);

  // Approval lifecycle + double-click safety.
  const approvalInput = {
    proposal_id: "proposal-fixture-002",
    approval_id: "approval-fixture-002",
    decision: "approve" as const,
    idempotency_key: "idem-approve-1",
    online: true,
  };
  const approved = await adapter.submitApprovalDecision(approvalInput);
  assert.equal(approved.state, "approved");
  assert.equal(approved.server_truth, false);
  const approvedAgain = await adapter.submitApprovalDecision(approvalInput);
  assert.deepEqual(approvedAgain, approved, "same idempotency key must return the settled result");
  assert.equal(approvedAgain.server_truth, false);

  const rejected = await adapter.submitApprovalDecision({
    proposal_id: "proposal-fixture-002",
    decision: "reject",
    idempotency_key: "idem-reject-1",
    online: true,
  });
  assert.equal(rejected.state, "rejected");

  const reviewed = await adapter.submitApprovalDecision({
    proposal_id: "proposal-fixture-002",
    decision: "review_requested",
    idempotency_key: "idem-review-1",
    online: true,
  });
  assert.equal(reviewed.state, "review_requested");

  const offlineDecision = await adapter.submitApprovalDecision({
    proposal_id: "proposal-fixture-002",
    decision: "approve",
    idempotency_key: "idem-offline-1",
    online: false,
  });
  assert.equal(offlineDecision.reason, "offline");
  assert.equal(offlineDecision.retryable, true);

  const expired = await adapter.submitApprovalDecision({
    proposal_id: "expired-proposal-1",
    decision: "approve",
    idempotency_key: "idem-expired-1",
    online: true,
  });
  assert.equal(expired.reason, "expired");
  assert.equal(expired.retryable, false);

  const superseded = await adapter.submitApprovalDecision({
    proposal_id: "superseded-proposal-1",
    decision: "approve",
    idempotency_key: "idem-superseded-1",
    online: true,
  });
  assert.equal(superseded.reason, "superseded");
  assert.equal(superseded.retryable, false);

  const consumed = await adapter.submitApprovalDecision({
    proposal_id: "already-consumed-proposal-1",
    decision: "approve",
    idempotency_key: "idem-consumed-1",
    online: true,
  });
  assert.equal(consumed.reason, "already_consumed");
  assert.equal(consumed.state, "approved");

  // Scenario-key override.
  adapter.selectRecordedScenario("approval:expired");
  const viaScenario = await adapter.submitApprovalDecision({
    proposal_id: "proposal-fixture-002",
    decision: "approve",
    idempotency_key: "idem-scenario-expired-1",
    online: true,
  });
  assert.equal(viaScenario.reason, "expired");
  adapter.selectRecordedScenario("completed");
}

async function testOfflineAdapter(): Promise<void> {
  section("offline snapshot adapter");

  const adapter = new OfflineSnapshotAdapter();
  assert.equal(adapter.mode, "offline");
  assert.equal(adapter.source, "OFFLINE");
  assert.equal(typeof adapter.getLastUpdated(), "string");
  assert.equal(Number.isNaN(Date.parse(adapter.getLastUpdated())), false);
  assert.equal(adapter.getLastUpdated(), "2026-09-15T08:12:08+08:00");

  const decision = await adapter.submitApprovalDecision({
    proposal_id: "proposal-fixture-002",
    approval_id: "approval-fixture-002",
    decision: "approve",
    idempotency_key: "offline-key",
    online: true,
  });
  assert.equal(decision.reason, "offline");
  assert.equal(decision.retryable, true);
  assert.equal(decision.server_truth, false);

  const pulse = await adapter.getJourneyPulse();
  assert.equal(pulse.risk.source, "OFFLINE");

  const received: string[] = [];
  const subscription = adapter.subscribeRunEvents(RECORDED_RUN_ID, {
    onEvent: (event) => received.push(event.source),
  });
  assert.equal(subscription.isLive(), false);
  await subscription.whenComplete();
  assert.equal(received.length, 14);
  assert.ok(received.every((source) => source === "OFFLINE"));
}

async function testLiveHonesty(): Promise<void> {
  section("live adapter source honesty on failure");

  const adapter = new LiveCityNexusAdapter({
    journeyId: "journey-reference-tianjin-20260915",
    fetchImpl: async () => {
      throw new Error("network down");
    },
    eventSourceFactory: () => {
      throw new Error("EventSource unavailable");
    },
  });

  const status = await adapter.getRuntimeStatus();
  assert.equal(status.source, "OFFLINE");

  const decision = await adapter.submitApprovalDecision({
    proposal_id: "proposal-fixture-002",
    approval_id: "approval-fixture-002",
    decision: "approve",
    idempotency_key: "live-offline-key",
    online: false,
  });
  assert.equal(decision.reason, "offline");
  assert.equal(decision.retryable, true);
  assert.equal(decision.server_truth, false);
}

async function main(): Promise<void> {
  await testNormalization();
  await testEventStore();
  await testRecordedAdapter();
  await testOfflineAdapter();
  await testLiveHonesty();
  console.log("ADAPTER CONTRACT TESTS: PASS");
}

main().catch((error: unknown) => {
  console.error("ADAPTER CONTRACT TESTS: FAIL");
  console.error(error);
  process.exitCode = 1;
});
