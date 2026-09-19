"""Wire the recovery panel into V8Experience."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/frontend/src/app/V8Experience.tsx")
s = P.read_text(encoding="utf-8")

s = s.replace(
    'import { V14RecoveryTruthPanel } from "../features/recovery/V14RecoveryTruthPanel";',
    'import { V14RecoveryTruthPanel } from "../features/recovery/V14RecoveryTruthPanel";\n'
    'import { RecoveryRequiredPanel } from "../features/recovery/RecoveryRequiredPanel";',
    1,
)

old = """      {loading && <p className="v8-muted">{t("auth.loading")}</p>}
      {!loading && !plan && (
        <div className="v8-feasibility">
          <span className="status-dot" />
          <div>
            <b>{t("auth.noPlan")}</b>
            <small>{t("auth.noPlanSub")}</small>
          </div>
        </div>
      )}"""
new = """      {loading && <p className="v8-muted">{t("auth.loading")}</p>}
      {/* Durable mid-trip HARD recovery / stale-evidence condition.  Rendered
          before the plan so an invalidated plan can never look healthy. */}
      <RecoveryRequiredPanel
        journeyId={journeyId}
        recovery={recovery}
        flags={flags}
        onRefresh={onRefresh}
      />
      {!loading && !plan && (
        <div className="v8-feasibility">
          <span className="status-dot" />
          <div>
            <b>{t("auth.noPlan")}</b>
            <small>{t("auth.noPlanSub")}</small>
          </div>
        </div>
      )}"""
assert old in s, "no-plan block not found"
s = s.replace(old, new, 1)

old2 = """function AuthoritativeExecution({
  journeyId,
  plan,
  twin,
  policy,
  loading,
  onRefresh,
}: {
  journeyId: string;
  plan: PlanVersion | null;
  twin: JourneyTwin | null;
  policy: Policy | null;
  loading: boolean;
  onRefresh: () => void;
}) {"""
new2 = """function AuthoritativeExecution({
  journeyId,
  plan,
  twin,
  policy,
  loading,
  recovery,
  flags,
  onRefresh,
}: {
  journeyId: string;
  plan: PlanVersion | null;
  twin: JourneyTwin | null;
  policy: Policy | null;
  loading: boolean;
  recovery?: RecoveryState | null;
  flags?: V8Data["experience_flags"];
  onRefresh: () => void;
}) {"""
assert old2 in s, "AuthoritativeExecution signature not found"
s = s.replace(old2, new2, 1)

s = s.replace(
    'import { v8Modes, type V8Data, type V8Mode } from "./v8Types";',
    'import { v8Modes, type RecoveryState, type V8Data, type V8Mode } from "./v8Types";',
    1,
)
P.write_text(s, encoding="utf-8", newline="\n")
print("V8Experience patched")
