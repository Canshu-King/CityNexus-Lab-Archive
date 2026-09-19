from pathlib import Path
p = Path("D:/moodle/CityNexus/frontend/src/features/execution/LiveRecovery.tsx")
s = p.read_text(encoding="utf-8")

old = '''type Disruption = {
  id: string;
  type: string;
  severity: string;
  affected_activity_id: string | null;
  occurred_at: string;
  payload?: Record<string, unknown>;
};'''
new = '''type Disruption = {
  id: string;
  type: string;
  severity: string;
  /** DETECTED | ACKNOWLEDGED | RESOLVED | IGNORED. Absent means DETECTED. */
  status?: string;
  affected_activity_id: string | null;
  occurred_at: string;
  resolved_at?: string | null;
  payload?: Record<string, unknown>;
};'''
assert s.count(old) == 1, "Disruption type"
s = s.replace(old, new)

# split merged list into still-open vs already-handled
old2 = '''  // Canonicalise each proposal's semantic diff so two proposals that describe'''
new2 = '''  // An event the traveller already acted on must not keep shouting "what
  // happened" as an open problem.  Acknowledgement is deliberately NOT
  // resolution in this product, so the event stays in the payload; the surface
  // has to separate "still needs you" from "already handled".
  const isOpen = (d: Disruption) => {
    const status = String(d.status ?? "DETECTED").toUpperCase();
    return status !== "ACKNOWLEDGED" && status !== "RESOLVED" && status !== "IGNORED" && !d.resolved_at;
  };
  const openDisruptions = disruptions.filter(isOpen);
  const handledDisruptions = disruptions.filter((d) => !isOpen(d));

  // Canonicalise each proposal's semantic diff so two proposals that describe'''
assert s.count(old2) == 1, "merge anchor"
s = s.replace(old2, new2)

# banner: only open events
old3 = '''      {disruptions.length > 0 && (
        <div className="live-disruption" data-testid="live-disruption" role="status">
          <b>{zh ? "发生了什么" : "What happened"}</b>
          <ul>
            {disruptions.slice(0, 3).map((d) => {'''
new3 = '''      {openDisruptions.length > 0 && (
        <div className="live-disruption" data-testid="live-disruption" role="status">
          <b>{zh ? "发生了什么" : "What happened"}</b>
          <ul>
            {openDisruptions.slice(0, 3).map((d) => {'''
assert s.count(old3) == 1, "banner"
s = s.replace(old3, new3)

# handled notice: an accepted proposal OR an already-acknowledged event counts
old4 = '''      {handled.length > 0 && disruptions.length === 0 && (
        <p className="live-handled" data-testid="live-handled">
          {zh
            ? "刚才的行程变化已经处理好，已确认的预订保持不变。"
            : "The earlier disruption has been handled; your confirmed bookings are unchanged."}
        </p>
      )}'''
new4 = '''      {(handled.length > 0 || handledDisruptions.length > 0) && openDisruptions.length === 0 && (
        <p className="live-handled" data-testid="live-handled">
          {zh
            ? "刚才的行程变化已经处理好，已确认的预订保持不变。"
            : "The earlier disruption has been handled; your confirmed bookings are unchanged."}
        </p>
      )}'''
assert s.count(old4) == 1, "handled notice"
s = s.replace(old4, new4)

p.write_text(s, encoding="utf-8")
print("LiveRecovery patched")
