from pathlib import Path

p = Path("D:/moodle/CityNexus/frontend/src/features/recovery/RecoveryRequiredPanel.tsx")
s = p.read_text(encoding="utf-8")

old = '''      const response = await post(`/api/v1/journeys/${journeyId}/plans/generate`, {});
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
      onRefresh();'''
new = '''      const response = await post(`/api/v1/journeys/${journeyId}/plans/generate`, {});
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        // The backend has persisted this as a real no-alternative outcome.
        setMessage(
          body?.error?.message ??
            body?.detail ??
            "No alternative plan could be generated for the new requirement.",
        );
        onRefresh();
        return;
      }
      setMessage(
        "Fresh options generated. Select one to clear this warning - it stays until then.",
      );
      onRefresh();'''
assert old in s, "replan body not found"
s = s.replace(old, new, 1)

old2 = '''          <button
            type="button"
            data-testid="recovery-replan"
            onClick={replan}
            disabled={busy !== null}
          >
            {busy === "REPLAN" ? "Generating…" : "Generate new options"}
          </button>'''
new2 = '''          <button
            type="button"
            data-testid="recovery-replan"
            onClick={() => void replan()}
            disabled={busy !== null}
          >
            {busy === "REPLAN" ? "Generating…" : "Generate new options"}
          </button>'''
assert old2 in s, "replan button not found"
s = s.replace(old2, new2, 1)

old3 = '''  async function replan() {'''
new3 = '''  async function replan(): Promise<void> {'''
assert old3 in s
s = s.replace(old3, new3, 1)
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
