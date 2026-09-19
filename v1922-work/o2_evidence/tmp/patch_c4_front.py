from pathlib import Path

# ---------- v8Types: disruptions carry status/resolved_at ----------
p = Path("D:/moodle/CityNexus/frontend/src/app/v8Types.ts")
s = p.read_text(encoding="utf-8")
old = "disruptions: Array<{ id: string; type: string; severity: string; affected_activity_id: string | null; occurred_at: string }>"
new = ("disruptions: Array<{ id: string; type: string; severity: string; "
       "status?: string; affected_activity_id: string | null; occurred_at: string; "
       "resolved_at?: string | null }>")
assert s.count(old) == 1, "v8Types disruptions"
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("v8Types patched")

# ---------- V8Experience: only OPEN disruptions need attention ----------
p = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = p.read_text(encoding="utf-8")

old = '''  const disruptions = useMemo(
    () => data?.active_plan?.disruptions ?? [],
    [data],
  );'''
new = '''  // "Needs attention" means an event the traveller has NOT already handled.
  // An accepted replan leaves its trigger Event in ACKNOWLEDGED, which this
  // product deliberately treats as "seen", not "resolved" — so the plan still
  // lists it.  Counting that as an open problem made Today and the notification
  // badge keep saying "1 项变化" forever while Live showed nothing to decide.
  // Anything explicitly RESOLVED/IGNORED is likewise no longer attention.
  const allDisruptions = useMemo(
    () => data?.active_plan?.disruptions ?? [],
    [data],
  );
  const disruptions = useMemo(
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
assert s.count(old) == 1, "shell disruptions"
s = s.replace(old, new)

# Hub: separate open from handled
old2 = '''  const chosenStay = data.options.find((option) => option.status === "SELECTED") ?? null;
  const disruptions = data.active_plan?.disruptions ?? [];
  const nextClock = nextStop ? clockInZone(nextStop.start_at, journeyTz) : null;'''
new2 = '''  const chosenStay = data.options.find((option) => option.status === "SELECTED") ?? null;
  const planDisruptions = data.active_plan?.disruptions ?? [];
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
  });
  const nextClock = nextStop ? clockInZone(nextStop.start_at, journeyTz) : null;'''
assert s.count(old2) == 1, "hub disruptions"
s = s.replace(old2, new2)

# Hub: the Attention cell must tell the truth in all three states
old3 = '''              <strong
                className={disruptions.length ? "warn" : "green"}
                data-testid="today-attention"
              >
                {disruptions.length
                  ? zh
                    ? `${disruptions.length} 项变化`
                    : `${disruptions.length} change(s)`
                  : zh
                    ? "一切正常"
                    : "All clear"}
              </strong>
              <small>
                {disruptions.length
                  ? zh
                    ? "打开「实时行程」查看"
                    : "Open Live to review"
                  : zh
                    ? "没有影响行程的变化"
                    : "Nothing affecting your trip"}
              </small>'''
new3 = '''              <strong
                className={disruptions.length ? "warn" : "green"}
                data-testid="today-attention"
              >
                {disruptions.length
                  ? zh
                    ? `${disruptions.length} 项变化`
                    : `${disruptions.length} change(s)`
                  : handledDisruptions.length
                    ? zh
                      ? "已处理"
                      : "Handled"
                    : zh
                      ? "一切正常"
                      : "All clear"}
              </strong>
              <small>
                {disruptions.length
                  ? zh
                    ? "打开「实时行程」查看"
                    : "Open Live to review"
                  : handledDisruptions.length
                    ? zh
                      ? "刚才的变化已经处理好"
                      : "The earlier change has been handled"
                    : zh
                      ? "没有影响行程的变化"
                      : "Nothing affecting your trip"}
              </small>'''
assert s.count(old3) == 1, "hub attention"
s = s.replace(old3, new3)

# Live's guardian line must read the same truth
old4 = '''                {data.active_plan?.disruptions.length
                  ? t("live.guardianMonitoring", { severity: data.active_plan.disruptions[0].severity })
                  : t("live.routeCurrent")}'''
new4 = '''                {disruptions.length
                  ? t("live.guardianMonitoring", { severity: disruptions[0].severity })
                  : t("live.routeCurrent")}'''
assert s.count(old4) == 1, "live guardian"
s = s.replace(old4, new4)

p.write_text(s, encoding="utf-8")
print("V8Experience patched")
