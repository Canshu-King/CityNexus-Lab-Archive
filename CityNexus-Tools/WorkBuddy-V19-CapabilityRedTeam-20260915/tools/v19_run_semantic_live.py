"""Run the raw-language corpus through the REAL semantic compiler.

Records, per case:
  raw text -> model envelope -> server canonical capability -> final policy

If the DeepSeek credential is absent the script still runs the deterministic
pass and marks the live columns as NOT_RUN, so the report can never pretend
live semantics were verified.
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19-CapabilityRedTeam-20260915")
sys.path.insert(0, str(LAB / "repo_copy" / "backend"))

os.environ.setdefault("CITYNEXUS_DATABASE_URL", f"sqlite:///{LAB / 'v19_redteam.db'}")
os.environ.setdefault("CITYNEXUS_ENV", "test")

from app.integrations.ai.copilot_contract import classify_copilot_message  # noqa: E402
from app.integrations.ai.semantic_compiler import (  # noqa: E402
    SemanticEnvelope,
    apply_semantic_policy,
    compile_semantic_envelope,
)

CORPUS = LAB / "evidence" / "semantic_cases.jsonl"
OUT = LAB / "evidence" / "semantic_live_results.jsonl"
SUMMARY = LAB / "evidence" / "semantic_live_summary.json"

# Capability-relevant vocabulary that a correct capability layer must derive.
CAPABILITY_TERMS = (
    "step_free", "wheelchair", "walking", "max_walk", "rest", "nap", "quiet",
    "sensory", "luggage", "stroller", "toilet", "shade", "accessible",
    "mobility", "capability", "hardness", "HARD", "SOFT", "durability",
)
ENVELOPE_KEYS = (
    "intent", "assertion_status", "effective_time", "event_type",
    "requested_action", "confidence", "reasoning_summary", "entities", "constraints",
)

VERIFIED_CONTEXT: dict[str, Any] = {
    "journey_id": "22222222-2222-4222-8222-222222222222",
    "city_code": "CNX-DEMO",
    "timezone": "Asia/Shanghai",
    "status": "DRAFT",
    "protected_commitments": [],
    "preferences": [],
    "known_venue_accessibility_evidence": [],
}


def deterministic_view(text: str) -> dict[str, Any]:
    try:
        result = classify_copilot_message(text)
        return {
            "intent": getattr(result, "intent", None),
            "confidence": getattr(result, "confidence", None),
            "reason": getattr(result, "reason", None),
        }
    except Exception as exc:  # noqa: BLE001 - evidence collection must not crash
        return {"error": f"{type(exc).__name__}: {exc}"}


def capability_terms_in(payload: Any) -> list[str]:
    blob = json.dumps(payload, ensure_ascii=False, default=str).lower()
    return sorted({term for term in CAPABILITY_TERMS if term.lower() in blob})


def run_case(case: dict[str, Any], client: Any, live: bool) -> dict[str, Any]:
    text = case["text"]
    row: dict[str, Any] = {
        "id": case["id"],
        "bucket": case["bucket"],
        "pair_id": case.get("pair_id"),
        "role": case["role"],
        "topic": case.get("topic"),
        "lang": case["lang"],
        "persona": case.get("persona"),
        "raw_text": text,
        "expected": case.get("expected"),
        "why": case.get("why"),
        "deterministic": deterministic_view(text),
    }

    if not live:
        row.update(
            {
                "live_status": "NOT_RUN",
                "model_envelope": None,
                "envelope_valid": None,
                "server_canonical_capability": None,
                "final_policy": None,
                "capability_terms_in_envelope": [],
                "capability_terms_in_decision": [],
                "error": None,
            }
        )
        return row

    last_error: str | None = None
    envelope: SemanticEnvelope | None = None
    raw_envelope: dict[str, Any] | None = None
    for attempt in range(3):  # policy: retry provider failures twice at most
        try:
            envelope = compile_semantic_envelope(client, text, VERIFIED_CONTEXT)
            break
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {str(exc)[:220]}"
            time.sleep(0.6 * (attempt + 1))
    if envelope is None and last_error is None:
        last_error = "ENVELOPE_REJECTED_BY_SCHEMA_VALIDATOR"

    if envelope is not None:
        raw_envelope = envelope.as_dict()

    decision = apply_semantic_policy(envelope) if envelope is not None else None
    row.update(
        {
            "live_status": "OK" if envelope is not None else "FAILED",
            "model_envelope": raw_envelope,
            "envelope_valid": envelope is not None,
            "server_canonical_capability": None,
            "capability_path_exists": False,
            "final_policy": (
                {
                    "route_intent": decision.route_intent,
                    "action": decision.action,
                    "event_type": decision.event_type,
                    "create_event": decision.create_event,
                    "verify_evidence": decision.verify_evidence,
                    "reason": decision.reason,
                }
                if decision is not None
                else None
            ),
            "capability_terms_in_envelope": capability_terms_in(raw_envelope or {}),
            "capability_terms_in_decision": capability_terms_in(
                {
                    "route_intent": decision.route_intent if decision else None,
                    "action": decision.action if decision else None,
                    "reason": decision.reason if decision else None,
                }
            ),
            "error": last_error,
        }
    )
    return row


def _credential() -> str | None:
    """Reuse the existing credential inside this child process only.

    The value is never printed, logged, or written to disk.
    """

    for name in ("DEEPSEEK_API_KEY", "CITYNEXUS_AI_API_KEY"):
        value = os.getenv(name)
        if value:
            return value
    try:
        import winreg  # noqa: PLC0415

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as handle:
            value, _ = winreg.QueryValueEx(handle, "DEEPSEEK_API_KEY")
            return str(value) or None
    except OSError:
        return None


def main() -> int:
    cases = [json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines() if line.strip()]
    api_key = _credential()
    limit = int(os.getenv("V19_CASE_LIMIT", "0") or 0)
    if limit:
        cases = cases[:limit]
    live = bool(api_key)
    client = None
    if live:
        from app.integrations.ai.responses import DeepSeekResponsesClient  # noqa: E402

        client = DeepSeekResponsesClient(
            api_key=api_key,
            model=os.getenv("CITYNEXUS_AI_MODEL", "deepseek-v4-flash"),
            base_url=os.getenv("CITYNEXUS_DEEPSEEK_API_URL", "https://api.deepseek.com/responses"),
            reasoning_effort="none",
            timeout_seconds=45.0,
        )

    print(f"cases={len(cases)} live={live}")
    started = time.time()
    rows: list[dict[str, Any]] = []
    if live:
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(run_case, case, client, True): case for case in cases}
            for done, future in enumerate(as_completed(futures), start=1):
                rows.append(future.result())
                if done % 25 == 0:
                    print(f"  {done}/{len(cases)} elapsed={time.time() - started:.0f}s", flush=True)
    else:
        rows = [run_case(case, None, False) for case in cases]

    order = {case["id"]: index for index, case in enumerate(cases)}
    rows.sort(key=lambda item: order.get(item["id"], 10**6))
    with OUT.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    # ---------------- scoring ----------------
    by_id = {row["id"]: row for row in rows}
    pair_stats: list[dict[str, Any]] = []
    pair_ids = sorted({row["pair_id"] for row in rows if row["pair_id"]})
    for pair_id in pair_ids:
        members = [by_id[key] for key in by_id if key.startswith(pair_id + "-")]
        if len(members) != 2:
            continue
        first, second = members
        def signature(row: dict[str, Any]) -> Any:
            envelope = row.get("model_envelope") or {}
            return (
                envelope.get("intent"),
                envelope.get("assertion_status"),
                envelope.get("effective_time"),
                envelope.get("event_type"),
                envelope.get("requested_action"),
                json.dumps(envelope.get("constraints"), ensure_ascii=False, sort_keys=True),
                (row.get("final_policy") or {}).get("route_intent"),
            )
        pair_stats.append(
            {
                "pair_id": pair_id,
                "bucket": first["bucket"],
                "a_id": first["id"],
                "a_role": first["role"],
                "b_id": second["id"],
                "b_role": second["role"],
                "identical_outcome": signature(first) == signature(second),
                "a_signature": signature(first),
                "b_signature": signature(second),
            }
        )

    total = len(rows)
    live_rows = [row for row in rows if row.get("live_status") == "OK"]
    envelope_ok = len(live_rows)
    any_capability_term = sum(1 for row in live_rows if row.get("capability_terms_in_envelope"))
    decision_capability_term = sum(
        1 for row in live_rows if row.get("capability_terms_in_decision")
    )
    constraints_non_empty = sum(
        1 for row in live_rows if (row.get("model_envelope") or {}).get("constraints")
    )
    indistinct = [item for item in pair_stats if item["identical_outcome"]]

    summary = {
        "corpus_total": total,
        "live_enabled": live,
        "live_ok": envelope_ok,
        "live_failed": sum(1 for row in rows if row.get("live_status") == "FAILED"),
        "schema_rejected": sum(
            1 for row in rows if row.get("error") == "ENVELOPE_REJECTED_BY_SCHEMA_VALIDATOR"
        ),
        "envelopes_with_any_capability_term": any_capability_term,
        "policies_with_any_capability_term": decision_capability_term,
        "envelopes_with_non_empty_constraints": constraints_non_empty,
        "server_canonical_capability_present": False,
        "pairs_evaluated": len(pair_stats),
        "pairs_with_identical_outcome": len(indistinct),
        "pair_discrimination_rate": (
            round(1 - len(indistinct) / len(pair_stats), 4) if pair_stats else None
        ),
        "indistinct_pairs_by_bucket": _count_by(indistinct, "bucket"),
        "elapsed_seconds": round(time.time() - started, 1),
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    (LAB / "evidence" / "semantic_pair_stats.json").write_text(
        json.dumps(pair_stats, ensure_ascii=False, indent=1, default=str), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in items:
        out[item[key]] = out.get(item[key], 0) + 1
    return out


if __name__ == "__main__":
    raise SystemExit(main())
