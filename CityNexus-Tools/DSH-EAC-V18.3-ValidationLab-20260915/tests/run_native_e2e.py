"""Trigger one Copilot -> native Hermes run and capture the real SSE sequence."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx

BASE = "http://127.0.0.1:8022"
WORKSPACE = Path(__file__).resolve().parents[1]
SCENARIO = json.loads((WORKSPACE / "lab-data" / "scenario.json").read_text(encoding="utf-8"))
EVIDENCE = WORKSPACE / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)
TOOL_SEQUENCE = EVIDENCE / "hermes_tool_sequences.jsonl"
RESULT = EVIDENCE / "native_e2e_run.json"
TERMINAL = {"run.completed", "run.failed", "run.stopped"}


def parse_sse_line(line: str, event_name: str | None) -> tuple[dict[str, Any] | None, str | None]:
    if line.startswith("event:"):
        return None, line[6:].strip() or None
    if line.startswith("data:"):
        raw = line[5:].strip()
        if not raw:
            return None, event_name
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return None, event_name
        if isinstance(value, dict):
            if event_name:
                value.setdefault("event_type", event_name)
            return value, None
    return None, None


def main() -> int:
    journey_id = SCENARIO["journey_id"]
    message = sys.argv[1] if len(sys.argv) > 1 else (
        "地铁延误了，我赶不上下一个活动，帮我检查行程并给出重规划建议。"
    )
    result: dict[str, Any] = {
        "journey_id": journey_id,
        "message": message,
        "started_at": time.time(),
    }
    try:
        with httpx.Client(base_url=BASE, timeout=httpx.Timeout(20.0, read=900.0)) as client:
            response = client.post(
                f"/api/v1/journeys/{journey_id}/copilot/messages",
                json={"message": message, "locale": "zh"},
            )
            response.raise_for_status()
            payload = response.json()
            result["copilot_response"] = payload
            agent_run = payload.get("agent_run") or {}
            run_id = agent_run.get("run_id")
            result["run_id"] = run_id
            result["runtime_identity"] = agent_run.get("runtime_identity")
            if not run_id:
                result["status"] = "NO_NATIVE_RUN"
                RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 2

            events: list[dict[str, Any]] = []
            url = f"/api/v1/journeys/{journey_id}/agent/hermes/runs/{run_id}/events"
            try:
                with client.stream("GET", url) as stream:
                    stream.raise_for_status()
                    event_name: str | None = None
                    for line in stream.iter_lines():
                        if not line:
                            event_name = None
                            continue
                        value, next_event = parse_sse_line(line, event_name)
                        if next_event is not None:
                            event_name = next_event
                        if value is not None:
                            events.append(value)
                            with TOOL_SEQUENCE.open("a", encoding="utf-8") as handle:
                                handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
                            if value.get("event_type") in TERMINAL:
                                break
            except httpx.HTTPError as exc:
                result["sse_error"] = f"{type(exc).__name__}: {exc}"

            result["events"] = events
            result["event_count"] = len(events)
            result["tool_events"] = [
                {
                    "event_type": item.get("event_type"),
                    "tool_name": item.get("tool_name"),
                    "status": item.get("status"),
                    "timestamp": item.get("timestamp"),
                    "duration_ms": item.get("duration_ms"),
                }
                for item in events
                if item.get("event_type") in {"tool.started", "tool.completed", "tool.failed"}
            ]
            try:
                timeline = client.get(
                    f"/api/v1/journeys/{journey_id}/agent/hermes/runs/{run_id}/timeline"
                )
                timeline.raise_for_status()
                result["timeline"] = timeline.json()
            except httpx.HTTPError as exc:
                result["timeline_error"] = f"{type(exc).__name__}: {exc}"
            try:
                run_status = client.get(
                    f"/api/v1/journeys/{journey_id}/agent/hermes/runs/{run_id}"
                )
                run_status.raise_for_status()
                result["run_status"] = run_status.json()
            except httpx.HTTPError as exc:
                result["run_status_error"] = f"{type(exc).__name__}: {exc}"
            terminal = next(
                (item["event_type"] for item in reversed(events) if item.get("event_type") in TERMINAL),
                None,
            )
            result["terminal_event"] = terminal
            result["status"] = "COMPLETED" if terminal == "run.completed" else (terminal or "NO_TERMINAL")
    except Exception as exc:  # noqa: BLE001
        result["status"] = "EXCEPTION"
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["finished_at"] = time.time()
    result["duration_seconds"] = round(result["finished_at"] - result["started_at"], 3)
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: result.get(key) for key in (
        "status", "run_id", "runtime_identity", "event_count", "tool_events", "terminal_event", "duration_seconds"
    )}, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
