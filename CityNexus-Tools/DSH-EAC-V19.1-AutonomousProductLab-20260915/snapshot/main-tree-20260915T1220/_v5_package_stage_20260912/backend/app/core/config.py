from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("CITYNEXUS_ENV", "development")
    database_url: str = os.getenv("CITYNEXUS_DATABASE_URL", "sqlite:///./citynexus.db")
    ai_enabled: bool = os.getenv("CITYNEXUS_AI_ENABLED", "false").lower() == "true"
    ai_provider: str = os.getenv("CITYNEXUS_AI_PROVIDER", "deepseek")
    ai_model: str = os.getenv("CITYNEXUS_AI_MODEL", "deepseek/deepseek-chat")
    ai_api_key: str | None = (
        os.getenv("CITYNEXUS_AI_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or None
    )
    deepseek_api_url: str = os.getenv(
        "CITYNEXUS_DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions"
    )
    impact_provider: str = os.getenv("CITYNEXUS_IMPACT_PROVIDER", "disabled")
    impact_timeout_seconds: float = float(os.getenv("CITYNEXUS_IMPACT_TIMEOUT_SECONDS", "10"))
    # Agent identity is server-owned. A configured token is required outside
    # local development; the request body's agent_id is never authoritative.
    agent_token: str | None = os.getenv("CITYNEXUS_AGENT_TOKEN") or None
    agent_principal_id: str = os.getenv("CITYNEXUS_AGENT_PRINCIPAL_ID", "citynexus-local-agent")
    agent_allowed_traveler_ids: tuple[str, ...] = tuple(
        item.strip()
        for item in os.getenv("CITYNEXUS_AGENT_ALLOWED_TRAVELER_IDS", "").split(",")
        if item.strip()
    )
    live_valhalla_url: str | None = os.getenv("CITYNEXUS_LIVE_VALHALLA_URL") or None
    open_meteo_url: str = os.getenv("CITYNEXUS_OPEN_METEO_URL", "https://api.open-meteo.com")
    open_meteo_timeout_seconds: float = float(
        os.getenv("CITYNEXUS_OPEN_METEO_TIMEOUT_SECONDS", "10")
    )
    solver_mode: str = os.getenv("CITYNEXUS_SOLVER", "deterministic")
    hermes_api_url: str | None = os.getenv("CITYNEXUS_HERMES_API_URL")
    hermes_api_key: str | None = os.getenv("CITYNEXUS_HERMES_API_KEY")
    hermes_model: str = os.getenv("CITYNEXUS_HERMES_MODEL", "hermes")
    guardian_autorun: bool = os.getenv("CITYNEXUS_GUARDIAN_AUTORUN", "false").lower() == "true"
    guardian_interval_seconds: float = float(os.getenv("CITYNEXUS_GUARDIAN_INTERVAL_SECONDS", "60"))
    guardian_signal_provider: str = os.getenv("CITYNEXUS_GUARDIAN_SIGNAL_PROVIDER", "demo").lower()
    guardian_cooldown_seconds: int = int(os.getenv("CITYNEXUS_GUARDIAN_COOLDOWN_SECONDS", "900"))
    solver_random_seed: int = int(os.getenv("CITYNEXUS_SOLVER_RANDOM_SEED", "1"))
    solver_max_time_seconds: float = float(os.getenv("CITYNEXUS_SOLVER_MAX_TIME_SECONDS", "1.0"))


settings = Settings()
