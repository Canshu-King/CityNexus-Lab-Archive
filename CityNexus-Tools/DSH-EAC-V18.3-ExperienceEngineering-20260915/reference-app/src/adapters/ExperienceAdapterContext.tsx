/**
 * React bindings for the Runtime Adapter Layer.
 *
 * Components consume the adapter exclusively through these hooks, so they
 * never import fixtures or runtime transports directly. `getJourneyPulse`,
 * `getRuntimeStatus`, `getRecoveryDiff`, and `getMapState` return
 * `{ data, loading, error, refresh }`; mutation hooks expose their own state.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { PulseState } from "../types";
import type {
  ApprovalDecisionInput,
  ApprovalDecisionResult,
  ApprovalState,
  CopilotMissionStart,
  ExperienceAdapter,
  MapState,
  NormalizedAgentEvent,
  NormalizedProposal,
  NormalizedRun,
  RunSubscription,
  StopResult,
} from "./contract";
import { compareNormalizedEvents } from "./eventStore";
import { createExperienceAdapter } from "./index";

const AdapterContext = createContext<ExperienceAdapter | null>(null);

export function ExperienceAdapterProvider({
  children,
  adapter,
}: {
  children: ReactNode;
  adapter?: ExperienceAdapter;
}) {
  const value = useMemo(() => adapter ?? createExperienceAdapter(), [adapter]);
  return <AdapterContext.Provider value={value}>{children}</AdapterContext.Provider>;
}

export function useExperienceAdapter(): ExperienceAdapter {
  const adapter = useContext(AdapterContext) as ExperienceAdapter | null;
  if (!adapter) {
    throw new Error("useExperienceAdapter must be used inside <ExperienceAdapterProvider>");
  }
  return adapter;
}

interface AsyncData<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  refresh: () => void;
}

function useAsyncData<T>(loader: () => Promise<T>, deps: readonly unknown[]): AsyncData<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    loader()
      .then((value) => {
        if (!cancelled) {
          setData(value);
          setError(null);
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Experience adapter failed");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // The loader closes over the adapter; deps describe when to reload.
  }, [...deps, tick]);

  const refresh = useCallback(() => setTick((value) => value + 1), []);
  return { data, error, loading, refresh };
}

export function useJourneyPulse(): AsyncData<PulseState> {
  const adapter = useExperienceAdapter();
  return useAsyncData(() => adapter.getJourneyPulse(), [adapter]);
}

export function useRuntimeStatus() {
  const adapter = useExperienceAdapter();
  return useAsyncData(() => adapter.getRuntimeStatus(), [adapter]);
}

export function useRecoveryDiff(proposalId?: string) {
  const adapter = useExperienceAdapter();
  return useAsyncData(() => adapter.getRecoveryDiff(proposalId), [adapter, proposalId]);
}

export function useMapState(): AsyncData<MapState> {
  const adapter = useExperienceAdapter();
  return useAsyncData(() => adapter.getMapState(), [adapter]);
}

export interface CopilotMissionHook {
  mission: CopilotMissionStart | null;
  start: (input: { message: string; locale: "en" | "zh-CN" }) => Promise<CopilotMissionStart | null>;
  loading: boolean;
  error: string | null;
  reset: () => void;
}

export function useCopilotMission(): CopilotMissionHook {
  const adapter = useExperienceAdapter();
  const [mission, setMission] = useState<CopilotMissionStart | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inFlight = useRef(false);

  const start = useCallback(
    async (input: { message: string; locale: "en" | "zh-CN" }) => {
      if (inFlight.current) return null;
      inFlight.current = true;
      setLoading(true);
      setError(null);
      try {
        const result = await adapter.startCopilotMission(input);
        setMission(result);
        return result;
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "Copilot mission failed");
        return null;
      } finally {
        inFlight.current = false;
        setLoading(false);
      }
    },
    [adapter],
  );

  return { mission, start, loading, error, reset: () => setMission(null) };
}

export function useRun(runId: string | null) {
  const adapter = useExperienceAdapter();
  return useAsyncData<NormalizedRun | null>(
    () => (runId ? adapter.getRun(runId) : Promise.resolve(null)),
    [adapter, runId],
  );
}

export interface RunEventsHook {
  events: NormalizedAgentEvent[];
  run: NormalizedRun | null;
  loading: boolean;
  error: string | null;
  isLive: boolean;
  reconnect: { attempt: number; since_sequence: number } | null;
  stop: () => Promise<StopResult | null>;
  subscription: { current: RunSubscription | null };
}

export function useRunEvents(runId: string | null): RunEventsHook {
  const adapter = useExperienceAdapter();
  const [events, setEvents] = useState<NormalizedAgentEvent[]>([]);
  const [run, setRun] = useState<NormalizedRun | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [reconnect, setReconnect] = useState<{ attempt: number; since_sequence: number } | null>(null);
  const subscriptionRef = useRef<RunSubscription | null>(null);

  useEffect(() => {
    if (!runId) {
      setEvents([]);
      setRun(null);
      setIsLive(false);
      setError(null);
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    setEvents([]);
    const subscription = adapter.subscribeRunEvents(
      runId,
      {
        onEvent: (event) => {
          if (cancelled) return;
          setEvents((current) => {
            if (current.some((item) => item.id === event.id)) return current;
            return [...current, event].sort(compareNormalizedEvents);
          });
          setIsLive(event.source === "LIVE");
        },
        onStatusChange: (next) => {
          if (!cancelled) setRun(next);
        },
        onError: (cause) => {
          if (!cancelled) {
            setError(cause.message);
            setIsLive(false);
          }
        },
        onReconnect: (info) => {
          if (!cancelled) setReconnect(info);
        },
      },
      { since_sequence: 0 },
    );
    subscriptionRef.current = subscription;
    setIsLive(subscription.isLive());
    setLoading(false);
    return () => {
      cancelled = true;
      subscription.unsubscribe();
      subscriptionRef.current = null;
    };
  }, [adapter, runId]);

  const stop = useCallback(async () => {
    if (!runId) return null;
    const result = await adapter.stopRun(runId);
    if (result.ok) {
      setRun((current) => (current ? { ...current, status: result.status } : current));
    }
    return result;
  }, [adapter, runId]);

  return { events, run, loading, error, isLive, reconnect, stop, subscription: subscriptionRef };
}

export interface ApprovalLifecycleHook {
  proposal: NormalizedProposal | null;
  state: ApprovalState;
  submitting: boolean;
  error: string | null;
  lastResult: ApprovalDecisionResult | null;
  decide: (decision: ApprovalDecisionInput["decision"]) => Promise<ApprovalDecisionResult | null>;
  reset: () => void;
}

function browserOnline(): boolean {
  return typeof navigator === "undefined" ? true : navigator.onLine !== false;
}

export function useApprovalLifecycle(proposalId?: string): ApprovalLifecycleHook {
  const adapter = useExperienceAdapter();
  const [proposal, setProposal] = useState<NormalizedProposal | null>(null);
  const [state, setState] = useState<ApprovalState>("proposal_only");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<ApprovalDecisionResult | null>(null);
  const idempotencyKeys = useRef<Map<string, string>>(new Map());
  const inFlight = useRef(false);

  useEffect(() => {
    let cancelled = false;
    adapter
      .getProposal(proposalId)
      .then((value) => {
        if (!cancelled && value) {
          setProposal(value);
          setState(value.state);
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : "Proposal load failed");
      });
    return () => {
      cancelled = true;
    };
  }, [adapter, proposalId]);

  const decide = useCallback(
    async (decision: ApprovalDecisionInput["decision"]) => {
      if (inFlight.current) return null;
      inFlight.current = true;
      setSubmitting(true);
      const composite = `${proposalId ?? proposal?.proposal_id ?? "proposal"}:${decision}`;
      let key = idempotencyKeys.current.get(composite);
      if (!key) {
        key = `idem-${composite}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        idempotencyKeys.current.set(composite, key);
      }
      try {
        const result = await adapter.submitApprovalDecision({
          proposal_id: proposalId ?? proposal?.proposal_id ?? "recorded-proposal",
          approval_id: proposal?.approval_id,
          decision,
          idempotency_key: key,
          online: browserOnline(),
        });
        setLastResult(result);
        setState(result.state);
        return result;
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "Approval decision failed");
        return null;
      } finally {
        inFlight.current = false;
        setSubmitting(false);
      }
    },
    [adapter, proposal, proposalId],
  );

  const reset = useCallback(() => {
    idempotencyKeys.current.clear();
    setLastResult(null);
    setState("proposal_only");
    setError(null);
  }, []);

  return { proposal, state, submitting, error, lastResult, decide, reset };
}
