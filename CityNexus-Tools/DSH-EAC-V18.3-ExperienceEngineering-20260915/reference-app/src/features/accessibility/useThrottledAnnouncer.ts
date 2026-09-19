import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Agent lifecycle transitions that must never be silently throttled away.
 * 中文说明：这些关键生命周期变化必须可靠播报。
 */
export type AgentLifecycleTransition =
  | "approval_required"
  | "failed"
  | "stopped"
  | "completed";

export const IMPORTANT_AGENT_TRANSITIONS: readonly AgentLifecycleTransition[] = [
  "approval_required",
  "failed",
  "stopped",
  "completed",
];

/** Maps raw agent event types to the important lifecycle vocabulary. */
export const AGENT_EVENT_TO_TRANSITION: Record<string, AgentLifecycleTransition> = {
  "approval.required": "approval_required",
  "run.failed": "failed",
  "run.stopped": "stopped",
  "run.completed": "completed",
};

const IMPORTANT_TRANSITION_SET = new Set<string>(IMPORTANT_AGENT_TRANSITIONS);

export function normalizeAgentTransition(
  transition: string | null | undefined,
): AgentLifecycleTransition | null {
  if (!transition) return null;
  if (IMPORTANT_TRANSITION_SET.has(transition)) {
    return transition as AgentLifecycleTransition;
  }
  return AGENT_EVENT_TO_TRANSITION[transition] ?? null;
}

export function isImportantAgentTransition(
  transition: string | null | undefined,
): boolean {
  return normalizeAgentTransition(transition) !== null;
}

export interface ThrottledAnnouncerOptions {
  /** Minimum interval between ordinary announcements. Default: 1500 ms. */
  minIntervalMs?: number;
  /** Alias for `minIntervalMs`. */
  minInterval?: number;
  /** Optional initial live-region text. */
  initialMessage?: string;
}

export interface AnnounceOptions {
  /** Lifecycle transition, e.g. `approval_required` or `run.completed`. */
  transition?: string | null;
  /** Force the important path when the caller already classified the event. */
  important?: boolean;
}

/** `announce(message)` or `announce(message, transition)` or `announce(message, options)`. */
export type AnnounceArg = string | AnnounceOptions;

export const DEFAULT_ANNOUNCEMENT_INTERVAL_MS = 1500;

/**
 * Throttles bursty agent events into a single live-region message while letting
 * important lifecycle transitions through immediately.
 *
 * Only announcement coalescing uses `setTimeout`; progress is never fabricated.
 */
export function useThrottledAnnouncer(options: ThrottledAnnouncerOptions = {}) {
  const minIntervalMs = Math.max(
    0,
    options.minIntervalMs ?? options.minInterval ?? DEFAULT_ANNOUNCEMENT_INTERVAL_MS,
  );
  const [message, setMessage] = useState(options.initialMessage ?? "");
  const lastAnnouncedAt = useRef(0);
  const hasAnnounced = useRef(false);
  const trailing = useRef<string | null>(null);
  const timer = useRef<number | null>(null);
  const mounted = useRef(true);

  const clearTimer = useCallback(() => {
    if (timer.current != null) {
      window.clearTimeout(timer.current);
      timer.current = null;
    }
  }, []);

  const flushTrailing = useCallback(() => {
    timer.current = null;
    const pending = trailing.current;
    trailing.current = null;
    if (!mounted.current || !pending) return;
    setMessage(pending);
    hasAnnounced.current = true;
    lastAnnouncedAt.current = Date.now();
  }, []);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      clearTimer();
    };
  }, [clearTimer]);

  const announce = useCallback(
    (text: string, arg?: AnnounceArg) => {
      const trimmed = text.trim();
      if (!trimmed) return;
      const announceOptions: AnnounceOptions =
        typeof arg === "string" ? { transition: arg } : arg ?? {};
      const important =
        announceOptions.important === true ||
        isImportantAgentTransition(announceOptions.transition);

      if (important) {
        // Important lifecycle changes bypass the throttle. Calls in the same
        // React batch collapse to the final lifecycle message.
        trailing.current = null;
        clearTimer();
        if (!mounted.current) return;
        setMessage(trimmed);
        hasAnnounced.current = true;
        lastAnnouncedAt.current = Date.now();
        return;
      }

      const now = Date.now();
      const elapsed = hasAnnounced.current
        ? now - lastAnnouncedAt.current
        : Number.POSITIVE_INFINITY;

      if (timer.current == null && elapsed >= minIntervalMs) {
        if (!mounted.current) return;
        setMessage(trimmed);
        hasAnnounced.current = true;
        lastAnnouncedAt.current = now;
        return;
      }

      // Burst coalescing: keep only the latest ordinary message.
      trailing.current = trimmed;
      if (timer.current == null) {
        const wait = Math.max(0, minIntervalMs - elapsed);
        timer.current = window.setTimeout(flushTrailing, wait);
      }
    },
    [clearTimer, flushTrailing, minIntervalMs],
  );

  return { announce, message };
}
