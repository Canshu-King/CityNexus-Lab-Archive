from pathlib import Path

# ---------- V8Experience: cross-reference accepted replans so the count is right
# even against a backend that does not yet project event status ----------
p = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = p.read_text(encoding="utf-8")

old = '''  const [offline, setOffline] = useState<OfflineJourney | null>(null);'''
new = '''  const [offline, setOffline] = useState<OfflineJourney | null>(null);
  // Event ids whose disruption the traveller has already resolved by accepting
  // a replan.  Read from /replans (which is authoritative for proposal status)
  // as well as from the event status, so the two can never disagree.
  const [handledEventIds, setHandledEventIds] = useState<string[]>([]);'''
assert s.count(old) == 1, "offline state anchor"
s = s.replace(old, new)

old2 = '''    const [nextPolicy, nextWallet, nextOffline, nextRuntimeStatus] = await Promise.all(['''
new2 = '''    // Which disruptions already have an accepted proposal behind them?
    try {
      const replans = await v8Request<Array<{ trigger_event_id?: string | null; status?: string }>>(
        `/api/v1/journeys/${journeyId}/replans`,
      );
      setHandledEventIds(
        (Array.isArray(replans) ? replans : [])
          .filter((item) => String(item?.status ?? "").toUpperCase() === "ACCEPTED")
          .map((item) => String(item?.trigger_event_id ?? ""))
          .filter(Boolean),
      );
    } catch {
      setHandledEventIds([]);
    }
    const [nextPolicy, nextWallet, nextOffline, nextRuntimeStatus] = await Promise.all(['''
assert s.count(old2) == 1, "load anchor"
s = s.replace(old2, new2)

# shell-level split uses both signals
old3 = '''  const disruptions = useMemo(
    () =>
      allDisruptions.filter((item) => {
        const status = String(item.status ?? "DETECTED").toUpperCase();
        return status !== "RESOLVED" && status !== "IGNORED" && !item.resolved_at;
      }),
    [allDisruptions],
  );
  /** Disruptions the traveller has already acted on; explained, not escalated. */
  const handledDisruptions = useMemo(
    () =>
      allDisruptions.filter((item) => {
        const status = String(item.status ?? "").toUpperCase();
        return status === "ACKNOWLEDGED" || status === "RESOLVED";
      }),
    [allDisruptions],
  );'''
new3 = '''  const isHandledDisruption = useCallback(
    (item: V8Data["active_plan"] extends null
      ? never
      : NonNullable<V8Data["active_plan"]>["disruptions"][number]) => {
      const status = String(item.status ?? "").toUpperCase();
      if (status === "ACKNOWLEDGED" || status === "RESOLVED" || status === "IGNORED") return true;
      if (item.resolved_at) return true;
      return handledEventIds.includes(item.id);
    },
    [handledEventIds],
  );
  const disruptions = useMemo(
    () => allDisruptions.filter((item) => !isHandledDisruption(item)),
    [allDisruptions, isHandledDisruption],
  );
  /** Disruptions the traveller has already acted on; explained, not escalated. */
  const handledDisruptions = useMemo(
    () => allDisruptions.filter((item) => isHandledDisruption(item)),
    [allDisruptions, isHandledDisruption],
  );'''
assert s.count(old3) == 1, "shell split"
s = s.replace(old3, new3)

# Hub gets the same predicate passed in
old4 = '''  const planDisruptions = data.active_plan?.disruptions ?? [];
  // A handled event is history, not an open problem.  An ACKNOWLEDGED trigger
  // stays in the plan payload (acknowledgement is not resolution), so it must
  // not keep Today in a permanent "needs attention" state.
  const disruptions = planDisruptions.filter((item) => {
    const status = String(item.status ?? "DETECTED").toUpperCase();
    return status !== "ACKNOWLEDGED" && status !== "RESOLVED" && status !== "IGNORED" && !item.resolved_at;
  });
  const handledDisruptions = planDisruptions.filter((item) => {
    const status = String(item.status ?? "").toUpperCase();
    return status === "ACKNOWLEDGED" || status === "RESOLVED";
  });'''
new4 = '''  const planDisruptions = data.active_plan?.disruptions ?? [];
  // A handled event is history, not an open problem.  An ACKNOWLEDGED trigger
  // stays in the plan payload (acknowledgement is not resolution), so it must
  // not keep Today in a permanent "needs attention" state.
  const disruptions = planDisruptions.filter((item) => !isHandledDisruption(item));
  const handledDisruptions = planDisruptions.filter((item) => isHandledDisruption(item));'''
assert s.count(old4) == 1, "hub split"
s = s.replace(old4, new4)

# Hub signature
old5 = '''function Hub({
  data,
  selected,
  hasChosenPlan,
  onNavigate,
  onNewJourney,
  onPlanWithAi,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  /** True only when the traveller actually adopted a plan. */
  hasChosenPlan: boolean;'''
new5 = '''function Hub({
  data,
  selected,
  hasChosenPlan,
  isHandledDisruption,
  onNavigate,
  onNewJourney,
  onPlanWithAi,
}: {
  data: V8Data;
  selected: V8Data["options"][number] | null;
  /** True only when the traveller actually adopted a plan. */
  hasChosenPlan: boolean;
  /** Whether a disruption has already been dealt with (accepted replan). */
  isHandledDisruption: (item: NonNullable<V8Data["active_plan"]>["disruptions"][number]) => boolean;'''
assert s.count(old5) == 1, "hub signature"
s = s.replace(old5, new5)

old6 = '''                hasChosenPlan={hasChosenPlan}
                onNavigate={navigate}'''
new6 = '''                hasChosenPlan={hasChosenPlan}
                isHandledDisruption={isHandledDisruption}
                onNavigate={navigate}'''
assert s.count(old6) == 1, "hub call"
s = s.replace(old6, new6)

# import useCallback
old7 = 'import { useEffect, useMemo, useState } from "react";'
new7 = 'import { useCallback, useEffect, useMemo, useState } from "react";'
assert s.count(old7) == 1, "react import"
s = s.replace(old7, new7)

p.write_text(s, encoding="utf-8")
print("V8Experience cross-reference patched")
