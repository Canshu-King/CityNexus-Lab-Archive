import { useExperienceAdapter, useApprovalLifecycle, useRecoveryDiff } from "../adapters/ExperienceAdapterContext";
import { useOnlineStatus } from "../pwa/onlineStatus";
import { RecoveryDiff } from "../components/RecoveryDiff";

export default function RecoveryRoute() {
  const adapter = useExperienceAdapter();
  const { online } = useOnlineStatus();
  const recovery = useRecoveryDiff();
  const approval = useApprovalLifecycle(undefined);

  if (recovery.loading) return <section className="card">Loading recovery truth…</section>;
  if (recovery.error || !recovery.data) {
    return (
      <section className="card">
        <h2>Recovery unavailable</h2>
        <p className="muted">{recovery.error ?? "No recovery proposal is available."}</p>
      </section>
    );
  }

  return (
    <RecoveryDiff
      proposal={recovery.data}
      approvalState={approval.state}
      submitting={approval.submitting}
      offline={!online || adapter.source === "OFFLINE"}
      lastUpdated={adapter.getLastUpdated?.() ?? null}
      onDecision={(decision) => void approval.decide(decision)}
    />
  );
}
