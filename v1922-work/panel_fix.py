from pathlib import Path

p = Path("D:/moodle/CityNexus/frontend/src/features/recovery/RecoveryRequiredPanel.tsx")
s = p.read_text(encoding="utf-8")

old = '''  function acknowledge() {
    setDismissed(true);
    setMessage(null);
  }'''
new = '''  async function acknowledge() {
    // Governed acknowledgement: this records that the traveller saw the
    // warning on the backend.  It never resolves recovery, never marks an
    // infeasible plan safe, and never hides the truth - the banner stays until
    // a revalidated feasible plan is actually selected.
    setBusy("ACK");
    setMessage(null);
    try {
      const response = await post(
        `/api/v1/journeys/${journeyId}/recovery/acknowledge`,
      );
      if (!response.ok) {
        setMessage("Could not record the acknowledgement. Please try again.");
        return;
      }
      setAcknowledged(true);
      setMessage(
        "Warning acknowledged. This plan is still unverified - generate and select new options to clear it.",
      );
      onRefresh();
    } catch {
      setMessage("Could not reach the server. The warning remains active.");
    } finally {
      setBusy(null);
    }
  }'''
assert old in s, "acknowledge not found"
s = s.replace(old, new, 1)

old2 = '''  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState(false);

  const stale = Boolean(flags?.staleness);
  const active = Boolean(recovery && recovery.state !== "RESOLVED");

  if (!stale && !active) return null;
  if (dismissed) return null;'''
new2 = '''  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [acknowledged, setAcknowledged] = useState(false);

  const stale = Boolean(flags?.staleness);
  const active = Boolean(recovery && recovery.state !== "RESOLVED");

  // The panel is never hidden by a local dismissal.  It only disappears when
  // the backend says the journey truth is actually healthy again.
  if (!stale && !active) return null;

  const noAlternative = Boolean(recovery?.no_alternative);
  const isAcknowledged = acknowledged || Boolean(recovery?.acknowledged);'''
assert old2 in s, "state block not found"
s = s.replace(old2, new2, 1)

old3 = '''  const title = stale
    ? "Trip evidence needs re-syncing"
    : "Your trip needs a decision";
  const detail = stale
    ? "The mobility evidence for this plan has expired. Generate fresh options before you continue."
    : `A new hard requirement (${recovery?.capability_code ?? "accessibility need"}) means the current plan can no longer be confirmed as safe. Your existing plan has not been changed.`;'''
new3 = '''  const title = stale
    ? "Trip evidence needs re-syncing"
    : noAlternative
      ? "No safe alternative is available"
      : "Your trip needs a decision";
  const detail = stale
    ? "The mobility evidence for this plan has expired. Generate fresh options before you continue."
    : noAlternative
      ? `A replan was attempted for ${recovery?.capability_code ?? "the new requirement"} and produced no feasible alternative. The current plan stays unverified.`
      : `A new hard requirement (${recovery?.capability_code ?? "accessibility need"}) means the current plan can no longer be confirmed as safe. Your existing plan has not been changed.`;'''
assert old3 in s, "title block not found"
s = s.replace(old3, new3, 1)

old4 = '''          <button
            type="button"
            data-testid="recovery-acknowledge"
            onClick={acknowledge}
            disabled={busy !== null}
          >
            Continue without changes
          </button>'''
new4 = '''          <button
            type="button"
            data-testid="recovery-acknowledge"
            onClick={() => void acknowledge()}
            disabled={busy !== null || isAcknowledged}
          >
            {isAcknowledged ? "Warning acknowledged" : "Acknowledge warning"}
          </button>'''
assert old4 in s, "acknowledge button not found"
s = s.replace(old4, new4, 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("面板已改造")
