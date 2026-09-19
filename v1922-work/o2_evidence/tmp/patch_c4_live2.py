from pathlib import Path
p = Path("D:/moodle/CityNexus/frontend/src/features/execution/LiveRecovery.tsx")
s = p.read_text(encoding="utf-8")

# accept a cross-referenced list of already-handled event ids
old = '''export function LiveRecovery({
  journeyId,
  onAccepted,
}: {
  journeyId: string;
  onAccepted?: () => void;
}) {'''
new = '''export function LiveRecovery({
  journeyId,
  handledEventIds = [],
  onAccepted,
}: {
  journeyId: string;
  /** Event ids the shell already knows are resolved by an accepted replan. */
  handledEventIds?: string[];
  onAccepted?: () => void;
}) {'''
assert s.count(old) == 1, "LiveRecovery signature"
s = s.replace(old, new)

old2 = '''  const isOpen = (d: Disruption) => {
    const status = String(d.status ?? "DETECTED").toUpperCase();
    return status !== "ACKNOWLEDGED" && status !== "RESOLVED" && status !== "IGNORED" && !d.resolved_at;
  };'''
new2 = '''  const isOpen = (d: Disruption) => {
    const status = String(d.status ?? "DETECTED").toUpperCase();
    if (status === "ACKNOWLEDGED" || status === "RESOLVED" || status === "IGNORED") return false;
    if (d.resolved_at) return false;
    return !handledEventIds.includes(d.id);
  };'''
assert s.count(old2) == 1, "isOpen"
s = s.replace(old2, new2)

# an ACCEPTED proposal is itself evidence the disruption was handled
old3 = '''  const handled = proposals.filter((p) => p.status === "ACCEPTED").slice(0, 1);'''
new3 = '''  const handled = proposals.filter((p) => p.status === "ACCEPTED").slice(0, 1);
  const acceptedTriggerIds = new Set(
    proposals
      .filter((p) => p.status === "ACCEPTED")
      .map((p) => String((p as { trigger_event_id?: string | null }).trigger_event_id ?? ""))
      .filter(Boolean),
  );'''
assert s.count(old3) == 1, "handled proposals"
s = s.replace(old3, new3)

old4 = '''  const openDisruptions = disruptions.filter(isOpen);'''
new4 = '''  const openDisruptions = disruptions.filter(
    (d) => isOpen(d) && !acceptedTriggerIds.has(d.id),
  );'''
assert s.count(old4) == 1, "openDisruptions"
s = s.replace(old4, new4)

p.write_text(s, encoding="utf-8")
print("LiveRecovery cross-reference patched")
