"""Add recovery / stale fields to the V8Data contract type."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/frontend/src/app/v8Types.ts")
s = P.read_text(encoding="utf-8")

old = """  traveler_twin?: { explicit_dimensions: string[]; learned_soft_dimensions: string[]; authority: string; explicit_capabilities?: TravelerCapability[]; capability_summary?: Record<string, unknown> };
  provider_mesh?: Record<string, any>;
};"""

new = """  traveler_twin?: { explicit_dimensions: string[]; learned_soft_dimensions: string[]; authority: string; explicit_capabilities?: TravelerCapability[]; capability_summary?: Record<string, unknown> };
  provider_mesh?: Record<string, any>;
  recovery?: RecoveryState | null;
  experience_flags?: {
    needs_review: boolean;
    recovery_required: boolean;
    staleness: boolean;
    feasibility_failures: string[];
  };
};

/**
 * Durable, governed recovery state returned by `/experience` and by the
 * capability confirm endpoints.  Present only when a confirmed HARD capability
 * (or an evidence regression) invalidated the active plan.  The active plan is
 * never silently mutated.
 */
export type RecoveryState = {
  state: "RECOVERY_REQUIRED" | "RECOVERY_REQUIRED_NO_ALTERNATIVE" | "RESOLVED";
  kind: string;
  event_id: string;
  event_status: "DETECTED" | "ACKNOWLEDGED" | "RESOLVED";
  capability_code: string | null;
  active_plan_version_id: string | null;
  failures: string[];
  candidate_plan_count: number;
  candidate_plan_ids: string[];
  requires_user_decision: boolean;
  silent_plan_mutation: false;
  actions: Array<"REPLAN" | "ACKNOWLEDGE_NO_ALTERNATIVE">;
  detected_at: string;
  journey_status?: string;
};"""
assert old in s, "v8Types tail not found"
s = s.replace(old, new, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("v8Types patched")
