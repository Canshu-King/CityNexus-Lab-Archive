"""Deterministic capability-impact explanation over actual gate failures."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from app.capabilities import canonicalize_capabilities


def _failure_text(failures: Iterable[str]) -> list[str]:
    return [str(item) for item in failures if item]


def _evidence(state: str, summary: str, failure: str | None = None) -> dict[str, Any]:
    return {
        "state": state,
        "summary": summary,
        "failure": failure,
        "provenance": {"source": "capability_plan_impact", "truth": "DERIVED_FROM_LIVE_GATE"},
    }


def _impact_state(
    code: str,
    severity: str,
    failures: list[str],
) -> tuple[str, str, str | None]:
    """Return UI impact status, explanation and the matching failure."""

    if code in {"STEP_FREE_REQUIRED", "AVOID_STAIRS"}:
        conflict = next((item for item in failures if item.startswith("ACCESSIBILITY_CONFLICT")), None)
        if conflict:
            return "VIOLATED", "Provider evidence records an accessibility conflict.", conflict
        unknown = next(
            (item for item in failures if item.startswith("ACCESSIBILITY_UNVERIFIED") or item.startswith("NEEDS_LIVE_EVIDENCE")),
            None,
        )
        if unknown:
            return "UNKNOWN", "Step-free evidence is missing or unverified; unknown is not accessible.", unknown
        return "PRESERVED", "No accessibility conflict or evidence gap was reported by the live gate.", None

    if code.startswith("MAX_"):
        exceeded = next((item for item in failures if f"{code}_EXCEEDED" in item or f"{code.split('_')[1]}_EXCEEDED" in item), None)
        if not exceeded:
            exceeded = next((item for item in failures if "MAX_" in item and "EXCEEDED" in item), None)
        if exceeded:
            return "VIOLATED", "Live feasibility gate reports the numeric limit was exceeded.", exceeded
        unknown = next((item for item in failures if "NEEDS_LIVE_EVIDENCE" in item and "MAX_" in item), None)
        invalid = next((item for item in failures if item.startswith("CAPABILITY_PARAMS_INVALID")), None)
        if unknown or invalid:
            return "UNKNOWN", "Live route/walking evidence is unavailable or the capability params are invalid.", unknown or invalid
        return "PRESERVED", "Live feasibility gate reports the numeric limit is satisfied.", None

    if code in {"MIDDAY_REST_WINDOW", "INFANT_NAP_WINDOW", "REST_EVERY_MIN", "TOILET_BREAK_EVERY_MIN"}:
        unsatisfied = next((item for item in failures if item.startswith("REST_WINDOW_UNSATISFIED")), None)
        invalid = next((item for item in failures if item.startswith("CAPABILITY_PARAMS_INVALID")), None)
        if unsatisfied:
            return "VIOLATED", "Live schedule gate reports the required rest/pace window is not preserved.", unsatisfied
        if invalid:
            return "UNKNOWN", "Rest/nap capability parameters are invalid.", invalid
        return "PRESERVED", "Live schedule gate reports the rest/care window is preserved.", None

    if code in {"STROLLER", "LARGE_LUGGAGE"}:
        unavailable = next((item for item in failures if "UNAVAILABLE" in item), None)
        if unavailable:
            return "VIOLATED", "Live provider gate reports the stroller/luggage facility is unavailable.", unavailable
        return "UNKNOWN", "No explicit provider conflict was reported, but facility evidence is not verified.", None

    if severity == "HARD":
        return "UNKNOWN", "Hard capability has no dedicated live impact rule yet.", None
    return "PRESERVED", "Soft/strong capability remains ranking/explanation context; it is not a hard gate.", None


def build_capability_impacts(
    capabilities: Iterable[Mapping[str, Any]] | None,
    gate_failures: Iterable[str] | None,
    *,
    candidate_id: str = "live-plan",
) -> dict[str, Any]:
    canonical = canonicalize_capabilities(capabilities or ())
    failures = _failure_text(gate_failures or ())
    why: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []
    for item in canonical:
        code = str(item["code"])
        severity = str(item["severity"])
        status, explanation, failure = _impact_state(code, severity, failures)
        impact = {
            "id": f"impact-{code}",
            "capability_id": code,
            "capability_label": code.replace("_", " ").title(),
            "kind": str(item.get("class") or "SOFT_PREFERENCE"),
            "status": status,
            "explanation": explanation,
            "candidate_id": candidate_id,
            "failure": failure,
            "evidence": _evidence(
                "VERIFIED" if status == "PRESERVED" and code in {"STEP_FREE_REQUIRED", "AVOID_STAIRS"} and not failure else (
                    "CONFLICT" if status == "VIOLATED" else (
                        "NEEDS_LIVE_EVIDENCE" if status == "UNKNOWN" else "UNVERIFIED"
                    )
                ),
                explanation,
                failure,
            ),
        }
        if status == "PRESERVED":
            why.append(impact)
        elif status in {"VIOLATED", "AT_RISK"}:
            rejected.append(impact)
        else:
            unknown.append(impact)
    return {
        "candidate_id": candidate_id,
        "authority": "BACKEND_DERIVED_FROM_LIVE_GATE",
        "gate_failures": failures,
        "why": why,
        "rejected": rejected,
        "unknown": unknown,
        "capabilities": [dict(item) for item in canonical],
        "unknown_accessibility_is_not_accessible": True,
    }
