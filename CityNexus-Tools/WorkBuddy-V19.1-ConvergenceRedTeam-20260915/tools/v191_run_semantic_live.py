"""V19.1: run the raw-language hard-pair corpus through the REAL semantic path.

Per case it records four stages, so model error and server error can be told apart:

    raw text
      -> model_raw_capabilities      what DeepSeek actually emitted
      -> model_canonical             after canonicalize_capabilities(source=DEEPSEEK)
      -> local_capabilities          extract_capabilities_from_text (server deterministic)
      -> merged_capabilities         what the envelope finally carries
      -> gate_verdict                what the feasibility gate does with it

The credential is read inside this process from HKCU\\Environment.  It is never
printed, never written to disk, and never included in any deliverable.

Usage:
    python tools/v191_run_semantic_live.py            # all cases
    V191_LIMIT=10 python tools/v191_run_semantic_live.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

LAB = Path(r"D:\moodle\CityNexus-Tools\WorkBuddy-V19.1-ConvergenceRedTeam-20260915")
LABEL = (os.getenv("V191_SNAPSHOT") or "A").upper()
SNAP = LAB / f"snapshot_{LABEL.lower()}"

sys.path.insert(0, str(SNAP / "backend"))
sys.path.insert(0, str(SNAP / "backend" / "tests"))

os.environ.setdefault("CITYNEXUS_DATABASE_URL", f"sqlite:///{LAB / 'evidence' / '_db' / f'semantic_{LABEL.lower()}.db'}")
os.environ.setdefault("CITYNEXUS_ENV", "test")

from app.capabilities import (  # noqa: E402
    canonicalize_capabilities,
    extract_capabilities_from_text,
)
from app.integrations.ai.semantic_compiler import (  # noqa: E402
    SemanticEnvelope,
    apply_semantic_policy,
    compile_semantic_envelope,
)

CORPUS = LAB / "evidence" / "semantic_cases.jsonl"
# Per-snapshot file plus the contract-named file (which tracks the latest snapshot).
OUT = LAB / "evidence" / f"hardpairs_{LABEL.lower()}.jsonl"
OUT_CONTRACT = LAB / "evidence" / "hardpairs.jsonl"

VERIFIED_CONTEXT: dict[str, Any] = {
    "journey_id": "22222222-2222-4222-8222-222222222222",
    "city_code": "CNX-DEMO",
    "timezone": "Asia/Shanghai",
    "status": "DRAFT",
    "protected_commitments": [],
    "preferences": [],
    "known_venue_accessibility_evidence": [],
}

GATE_CODES = {
    "STEP_FREE_REQUIRED", "AVOID_STAIRS", "MAX_WALKING_PER_LEG_M",
    "MAX_CONTINUOUS_WALKING_MIN", "MAX_DAILY_WALKING_M", "MIDDAY_REST_WINDOW",
    "REST_EVERY_MIN", "INFANT_NAP_WINDOW", "TOILET_BREAK_EVERY_MIN",
    "STROLLER", "LARGE_LUGGAGE",
}


def _brief(items: Any) -> list[dict]:
    out = []
    for item in items or []:
        if isinstance(item, dict):
            out.append(
                {
                    "code": item.get("code"),
                    "severity": item.get("severity"),
                    "scope": item.get("scope"),
                    "params": item.get("params"),
                }
            )
    return out


def _credential() -> str | None:
    for name in ("DEEPSEEK_API_KEY", "CITYNEXUS_AI_API_KEY"):
        value = os.getenv(name)
        if value:
            return value
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as handle:
            value, _ = winreg.QueryValueEx(handle, "DEEPSEEK_API_KEY")
            return str(value) or None
    except OSError:
        return None


def _install_capture() -> dict:
    """Capture the raw model capabilities before canonicalization rewrites them."""
    from app.integrations.ai import semantic_compiler

    box: dict[str, Any] = {"raw": None, "calls": 0}
    original = semantic_compiler.canonicalize_capabilities

    def wrapper(items, **kwargs):
        box["calls"] += 1
        if box["raw"] is None:
            box["raw"] = [dict(i) for i in items if isinstance(i, dict)]
        return original(items, **kwargs)

    semantic_compiler.canonicalize_capabilities = wrapper
    return box


def run_case(case: dict, client: Any) -> dict:
    text = case["text"]
    row: dict[str, Any] = {
        "id": case["id"],
        "bucket": case["bucket"],
        "pair_id": case.get("pair_id"),
        "role": case["role"],
        "topic": case.get("topic"),
        "lang": case["lang"],
        "raw_text": text,
        "expected": case.get("expected"),
        "why": case.get("why"),
    }

    # stage 3: server deterministic extraction, independent of the model
    local = extract_capabilities_from_text(text, scope="JOURNEY")
    row["local_capabilities"] = _brief(local)

    box = _install_capture()
    envelope: SemanticEnvelope | None = None
    last_error: str | None = None
    for attempt in range(3):  # provider retries: at most two
        box["raw"] = None
        try:
            envelope = compile_semantic_envelope(client, text, VERIFIED_CONTEXT)
            break
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {str(exc)[:220]}"
            time.sleep(0.6 * (attempt + 1))

    row["live_status"] = "OK" if envelope is not None else "FAILED"
    row["error"] = last_error
    row["model_raw_capabilities"] = _brief(box["raw"])

    if envelope is None:
        row.update(
            {
                "model_canonical": None,
                "merged_capabilities": None,
                "final_policy": None,
                "gate_codes": [],
                "gate_would_block": None,
                "model_vs_server_diverged": None,
                "server_added": None,
                "server_dropped": None,
            }
        )
        return row

    merged = _brief(envelope.capabilities)
    model_canonical = _brief(
        canonicalize_capabilities(box["raw"] or [], source="DEEPSEEK", provenance="MODEL_INTERPRETED")
    )
    decision = apply_semantic_policy(envelope)

    model_codes = {c["code"] for c in model_canonical}
    merged_codes = {c["code"] for c in merged}
    local_codes = {c["code"] for c in _brief(local)}

    row.update(
        {
            "model_canonical": model_canonical,
            "merged_capabilities": merged,
            "final_policy": {
                "route_intent": decision.route_intent,
                "action": decision.action,
                "event_type": decision.event_type,
                "create_event": decision.create_event,
                "verify_evidence": decision.verify_evidence,
                "reason": decision.reason,
            }
            if decision is not None
            else None,
            "gate_codes": sorted(merged_codes & GATE_CODES),
            "gate_would_block": bool(merged_codes & GATE_CODES),
            "model_vs_server_diverged": model_codes != merged_codes,
            "server_added": sorted(merged_codes - model_codes),
            "server_dropped": sorted(model_codes - merged_codes),
            "server_local_codes": sorted(local_codes),
            "model_hard": sorted(c["code"] for c in model_canonical if c.get("severity") == "HARD"),
            "merged_hard": sorted(c["code"] for c in merged if c.get("severity") == "HARD"),
        }
    )
    return row


def main() -> int:
    cases = [
        json.loads(line)
        for line in CORPUS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    limit = int(os.getenv("V191_LIMIT", "0") or 0)
    if limit:
        cases = cases[:limit]

    api_key = _credential()
    if not api_key:
        print("credential_present=False -> cannot run live semantics")
        return 2

    from app.integrations.ai.responses import DeepSeekResponsesClient  # noqa: E402

    client = DeepSeekResponsesClient(
        api_key=api_key,
        model=os.getenv("CITYNEXUS_AI_MODEL", "deepseek-v4-flash"),
        base_url=os.getenv("CITYNEXUS_DEEPSEEK_API_URL", "https://api.deepseek.com/responses"),
        reasoning_effort="none",
        timeout_seconds=60.0,
    )

    print(f"snapshot={LABEL} cases={len(cases)} live=True")
    started = time.time()
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(run_case, case, client): case for case in cases}
        for done, future in enumerate(as_completed(futures), start=1):
            try:
                rows.append(future.result())
            except Exception as exc:  # noqa: BLE001
                case = futures[future]
                rows.append(
                    {
                        "id": case["id"],
                        "bucket": case["bucket"],
                        "raw_text": case["text"],
                        "live_status": "CRASHED",
                        "error": f"{type(exc).__name__}: {str(exc)[:220]}",
                    }
                )
            if done % 20 == 0:
                print(f"  {done}/{len(cases)} ({time.time() - started:.0f}s)")

    rows.sort(key=lambda r: r["id"])
    for target in (OUT, OUT_CONTRACT):
        with target.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    ok = [r for r in rows if r.get("live_status") == "OK"]
    diverged = [r for r in ok if r.get("model_vs_server_diverged")]
    summary = {
        "snapshot": LABEL,
        "cases": len(rows),
        "live_ok": len(ok),
        "live_failed": len(rows) - len(ok),
        "model_vs_server_diverged": len(diverged),
        "model_produced_capability": sum(1 for r in ok if r.get("model_canonical")),
        "server_produced_capability": sum(1 for r in ok if r.get("local_capabilities")),
        "merged_produced_capability": sum(1 for r in ok if r.get("merged_capabilities")),
        "cases_where_server_dropped_model_hard": sum(
            1
            for r in ok
            if set(r.get("model_hard") or []) - set(r.get("merged_hard") or [])
        ),
        "cases_where_server_added_hard": sum(
            1
            for r in ok
            if set(r.get("merged_hard") or []) - set(r.get("model_hard") or [])
        ),
        "elapsed_seconds": round(time.time() - started, 1),
    }
    (LAB / "evidence" / f"hardpairs_summary_{LABEL.lower()}.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print(f"written -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
