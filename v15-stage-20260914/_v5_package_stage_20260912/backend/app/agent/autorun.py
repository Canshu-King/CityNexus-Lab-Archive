from __future__ import annotations

import asyncio
import json
import threading
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy import select

from app.agent.guardian import scan_guardian
from app.agent.signal_pipeline import SignalPipelineResult, refresh_demo_signals
from app.core.audit import record_audit
from app.core.config import settings
from app.db.models import GuardianPulse, Journey, JourneyMission
from app.db.session import SessionLocal

_worker_lock = threading.Lock()
_worker_thread: threading.Thread | None = None
_worker_stop: threading.Event | None = None
_worker_interval_seconds = settings.guardian_interval_seconds
_last_pulse_at: str | None = None
_last_error: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _live_weather_refresh(session, journey: Journey) -> SignalPipelineResult:
    """Use the existing Open-Meteo ingestion when live mode is explicitly selected."""

    from app.integrations.context.open_meteo import OpenMeteoContextProvider
    from app.integrations.context.weather_runtime import refresh_weather_runtime

    async def capture():
        async with httpx.AsyncClient(timeout=settings.open_meteo_timeout_seconds) as client:
            provider = OpenMeteoContextProvider(client=client, base_url=settings.open_meteo_url)
            return await refresh_weather_runtime(
                session,
                journey,
                provider=provider,
                captured_at=_now(),
            )

    result = asyncio.run(capture())
    return SignalPipelineResult(
        provider_key=result.provider_key,
        state="DISRUPTED" if result.event_ids else "NORMAL",
        observation_ids=(),
        event_ids=result.event_ids,
        created_event_ids=result.created_event_ids,
        resolved_event_ids=(),
        degraded=result.degraded,
    )


def refresh_signals(session, journey: Journey) -> SignalPipelineResult:
    if settings.guardian_signal_provider in {"open-meteo", "live", "weather"}:
        return _live_weather_refresh(session, journey)
    return refresh_demo_signals(session, journey)


def pulse_journey(session, journey: Journey) -> dict[str, Any]:
    """Persist one sensing -> Guardian evaluation cycle."""

    started_at = _now()
    pulse = GuardianPulse(
        id=str(uuid4()),
        journey_id=journey.id,
        status="RUNNING",
        provider_key=(
            "open-meteo"
            if settings.guardian_signal_provider in {"open-meteo", "live", "weather"}
            else "city-signal-fixture"
        ),
        observation_ids_json="[]",
        result_json="{}",
        started_at=started_at,
    )
    session.add(pulse)
    record_audit(
        session,
        action="guardian.pulse.started",
        entity_type="GuardianPulse",
        entity_id=pulse.id,
        journey_id=journey.id,
        actor_type="SYSTEM",
        actor_id="guardian-worker",
        after={"pulse_id": pulse.id, "provider_key": pulse.provider_key},
    )
    session.flush()
    try:
        signals = refresh_signals(session, journey)
        pulse.observation_ids_json = json.dumps(list(signals.observation_ids))
        guardian_result = None
        # A provider outage is evidence, not permission to mutate a stale Plan.
        if not signals.degraded:
            guardian_result = scan_guardian(session, journey)
            pulse.guardian_run_id = guardian_result.get("id")
        result = {
            "signals": signals.to_dict(),
            "guardian": guardian_result,
        }
        pulse.status = "COMPLETED"
        pulse.result_json = json.dumps(result, ensure_ascii=False, default=str)
        pulse.completed_at = _now()
        record_audit(
            session,
            action="guardian.pulse.completed",
            entity_type="GuardianPulse",
            entity_id=pulse.id,
            journey_id=journey.id,
            actor_type="SYSTEM",
            actor_id="guardian-worker",
            after={
                "pulse_id": pulse.id,
                "guardian_run_id": pulse.guardian_run_id,
                "created_event_ids": list(signals.created_event_ids),
                "degraded": signals.degraded,
            },
        )
        session.commit()
        return {"pulse_id": pulse.id, **result}
    except Exception as exc:  # provider/agent boundary: preserve worker liveness
        session.rollback()
        pulse = session.get(GuardianPulse, pulse.id)
        if pulse is not None:
            pulse.status = "FAILED"
            pulse.result_json = json.dumps({"error": str(exc)}, ensure_ascii=False)
            pulse.completed_at = _now()
            session.commit()
        raise


def run_once() -> list[dict[str, Any]]:
    """Run one deterministic-clock-friendly worker cycle."""

    global _last_pulse_at, _last_error
    results: list[dict[str, Any]] = []
    with SessionLocal() as session:
        journeys = session.scalars(
            select(Journey).where(Journey.status == "ACTIVE").order_by(Journey.id)
        ).all()
        for journey in journeys:
            mission = session.scalar(
                select(JourneyMission).where(
                    JourneyMission.journey_id == journey.id,
                    JourneyMission.is_standing.is_(True),
                    JourneyMission.status == "ACTIVE",
                )
            )
            if mission is None:
                continue
            try:
                results.append(pulse_journey(session, journey))
                _last_error = None
            except Exception as exc:  # noqa: BLE001 - one journey cannot stop the worker
                _last_error = f"{type(exc).__name__}: {exc}"
        _last_pulse_at = _now()
    return results


def _loop(stop: threading.Event, interval_seconds: float) -> None:
    global _worker_thread
    while not stop.wait(max(0.05, interval_seconds)):
        try:
            run_once()
        except Exception as exc:  # noqa: BLE001 - database/provider boundary
            global _last_error
            _last_error = f"{type(exc).__name__}: {exc}"
    with _worker_lock:
        _worker_thread = None


def start_autorun(*, interval_seconds: float | None = None) -> dict[str, Any]:
    global _worker_thread, _worker_stop, _worker_interval_seconds
    with _worker_lock:
        if _worker_thread is not None and _worker_thread.is_alive():
            return autorun_status()
        _worker_interval_seconds = float(
            interval_seconds if interval_seconds is not None else settings.guardian_interval_seconds
        )
        _worker_stop = threading.Event()
        _worker_thread = threading.Thread(
            target=_loop,
            args=(_worker_stop, _worker_interval_seconds),
            name="citynexus-guardian-worker",
            daemon=True,
        )
        _worker_thread.start()
        return autorun_status()


def stop_autorun() -> dict[str, Any]:
    thread: threading.Thread | None
    with _worker_lock:
        if _worker_stop is not None:
            _worker_stop.set()
        thread = _worker_thread
    if thread is not None and thread is not threading.current_thread():
        thread.join(timeout=max(1.0, _worker_interval_seconds + 1.0))
    return autorun_status()


def autorun_status() -> dict[str, Any]:
    thread = _worker_thread
    return {
        "enabled": bool(thread is not None and thread.is_alive()),
        "interval_seconds": _worker_interval_seconds,
        "signal_provider": settings.guardian_signal_provider,
        "last_pulse_at": _last_pulse_at,
        "last_error": _last_error,
    }


if settings.guardian_autorun:
    start_autorun()
