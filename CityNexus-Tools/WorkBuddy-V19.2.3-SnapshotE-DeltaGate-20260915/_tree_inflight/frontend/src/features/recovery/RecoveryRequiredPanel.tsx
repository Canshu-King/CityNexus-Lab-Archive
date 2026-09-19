/**
 * Mid-trip HARD recovery + stale-evidence panel.
 *
 * Surfaces the durable recovery state the backend writes when a newly
 * confirmed HARD capability (or an evidence regression) invalidates the
 * ACTIVE plan.  The active plan is never silently rewritten, so the traveller
 * is given an explicit, governed choice.
 */

import { useState } from "react";
import type { RecoveryState } from "../../app/v8Types";

type Props = {
  journeyId: string;
  recovery?: RecoveryState | null;
  flags?: {
    needs_review: boolean;
    recovery_required: boolean;
    staleness: boolean;
    feasibility_failures: string[];
  } | null;
  onRefresh: () => void;
};

async function post(path: string, body?: unknown): Promise<Response> {
  return fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export function RecoveryRequiredPanel({ journeyId, recovery, flags, onRefresh }: Props) {
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState(false);

  const stale = Boolean(flags?.staleness);
  const active = Boolean(recovery && recovery.state !== "RESOLVED");

  if (!stale && !active) return null;
  if (dismissed) return null;

  const failures = recovery?.failures ?? flags?.feasibility_failures ?? [];
  const title = stale
    ? "Trip evidence needs re-syncing"
    : "Your trip needs a decision";
  const detail = stale
    ? "The mobility evidence for this plan has expired. Generate fresh options before you continue."
    : `A new hard requirement (${recovery?.capability_code ?? "accessibility need"}) means the current plan can no longer be confirmed as safe. Your existing plan has not been changed.`;

  async function replan() {
    setBusy("REPLAN");
    setMessage(null);
    try {
      const response = await post(`/api/v1/journeys/${journeyId}/plans/generate`, {});
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        setMessage(
          body?.error?.message ??
            body?.detail ??
            "No alternative plan could be generated for the new requirement.",
        );
        return;
      }
      setMessage("Fresh options generated. Review and select one to continue.");
      onRefresh();
    } catch {
      setMessage("Could not reach the planner. Check your connection and try again.");
    } finally {
      setBusy(null);
    }
  }

  function acknowledge() {
    setDismissed(true);
    setMessage(null);
  }

  return (
    <section
      className="v8-feasibility v8-recovery-required"
      data-testid="recovery-required-panel"
      data-recovery-state={recovery?.state ?? (stale ? "STALE_EVIDENCE" : "NONE")}
      role="alert"
      aria-live="polite"
      style={{
        border: "1px solid #b45309",
        background: "rgba(180, 83, 9, 0.08)",
        borderRadius: 8,
        padding: "12px 14px",
        marginTop: 12,
      }}
    >
      <span className="status-dot" aria-hidden="true" />
      <div style={{ flex: 1 }}>
        <b data-testid="recovery-required-title">{title}</b>
        <small style={{ display: "block", marginTop: 4 }}>{detail}</small>
        {failures.length > 0 && (
          <ul style={{ margin: "8px 0 0 0", paddingLeft: 18, fontSize: 12 }}>
            {failures.slice(0, 4).map((item) => (
              <li key={item} data-testid="recovery-failure">
                {item}
              </li>
            ))}
          </ul>
        )}
        <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
          <button
            type="button"
            data-testid="recovery-replan"
            onClick={replan}
            disabled={busy !== null}
          >
            {busy === "REPLAN" ? "Generating…" : "Generate new options"}
          </button>
          <button
            type="button"
            data-testid="recovery-acknowledge"
            onClick={acknowledge}
            disabled={busy !== null}
          >
            Continue without changes
          </button>
        </div>
        {message && (
          <small
            data-testid="recovery-message"
            role="status"
            style={{ display: "block", marginTop: 8 }}
          >
            {message}
          </small>
        )}
      </div>
    </section>
  );
}
