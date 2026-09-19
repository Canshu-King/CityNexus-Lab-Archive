from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Traveler(Base):
    __tablename__ = "travelers"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    locale: Mapped[str] = mapped_column(String)
    timezone: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class Preference(Base):
    __tablename__ = "preferences"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    traveler_id: Mapped[str] = mapped_column(ForeignKey("travelers.id", ondelete="CASCADE"))
    category: Mapped[str] = mapped_column(String)
    preference_key: Mapped[str] = mapped_column(String)
    value_json: Mapped[str] = mapped_column(Text)
    weight: Mapped[float] = mapped_column()
    source: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("traveler_id", "category", "preference_key"),)


class TravelerAgentPolicy(Base):
    __tablename__ = "traveler_agent_policies"
    traveler_id: Mapped[str] = mapped_column(
        ForeignKey("travelers.id", ondelete="CASCADE"), primary_key=True
    )
    mode: Mapped[str] = mapped_column(String, default="ADVISORY", server_default="ADVISORY")
    auto_accept_replan: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    max_auto_replan_cost_delta_minor: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    max_auto_loss_minor: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    max_auto_schedule_drift_min: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    allowed_activity_types_json: Mapped[str] = mapped_column(
        Text, default="[]", server_default="[]"
    )
    protected_commitment_levels_json: Mapped[str] = mapped_column(
        Text,
        default='["C3_Guaranteed", "C4_Anchored"]',
        server_default='["C3_Guaranteed", "C4_Anchored"]',
    )
    allow_auto_commitment_management: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )
    allow_auto_when_provider_degraded: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )
    allow_auto_on_critical_event: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class Journey(Base):
    __tablename__ = "journeys"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    traveler_id: Mapped[str] = mapped_column(ForeignKey("travelers.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String)
    city_code: Mapped[str] = mapped_column(String)
    timezone: Mapped[str] = mapped_column(String)
    start_at: Mapped[str] = mapped_column(String)
    end_at: Mapped[str] = mapped_column(String)
    budget_currency: Mapped[str] = mapped_column(String)
    budget_amount_minor: Mapped[int] = mapped_column(Integer)
    planning_mode: Mapped[str] = mapped_column(
        String, default="balanced", server_default="balanced"
    )
    status: Mapped[str] = mapped_column(String)
    active_plan_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("plan_versions.id", ondelete="SET NULL"), nullable=True
    )
    current_activity_id: Mapped[str | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class JourneyMission(Base):
    """One-run natural-language intent bounded by the global Agent policy."""

    __tablename__ = "journey_missions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    traveler_id: Mapped[str] = mapped_column(ForeignKey("travelers.id", ondelete="CASCADE"))
    trigger_event_id: Mapped[str | None] = mapped_column(String, nullable=True)
    user_text: Mapped[str] = mapped_column(Text)
    objective_codes_json: Mapped[str] = mapped_column(Text, default="[]")
    protected_activity_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    mutable_activity_ids_json: Mapped[str] = mapped_column(Text, default="[]", server_default="[]")
    intent_json: Mapped[str] = mapped_column(Text, default="{}", server_default="{}")
    resolved_intent_json: Mapped[str] = mapped_column(Text, default="{}", server_default="{}")
    allowed_action_classes_json: Mapped[str] = mapped_column(
        Text, default="[]", server_default="[]"
    )
    unresolved_references_json: Mapped[str] = mapped_column(Text, default="[]", server_default="[]")
    compiler_provider_key: Mapped[str] = mapped_column(
        String, default="deterministic", server_default="deterministic"
    )
    compiler_model_key: Mapped[str] = mapped_column(
        String,
        default="mission-compiler-v2-fallback",
        server_default="mission-compiler-v2-fallback",
    )
    compiler_confidence: Mapped[float] = mapped_column(default=1.0, server_default="1.0")
    reasoning_summary: Mapped[str] = mapped_column(Text, default="", server_default="")
    is_standing: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    parent_mission_id: Mapped[str | None] = mapped_column(String, nullable=True)
    max_cost_delta_minor: Mapped[int] = mapped_column(Integer, default=0)
    max_loss_minor: Mapped[int] = mapped_column(Integer, default=0)
    max_schedule_drift_min: Mapped[int] = mapped_column(Integer, default=0)
    preferences_json: Mapped[str] = mapped_column(Text, default="{}")
    requested_autonomy: Mapped[str] = mapped_column(String, default="PLAN_ONLY")
    status: Mapped[str] = mapped_column(String, default="CREATED")
    created_at: Mapped[str] = mapped_column(String)
    started_at: Mapped[str | None] = mapped_column(String, nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class AgentRun(Base):
    """Persisted execution envelope for a model-backed Journey Agent run."""

    __tablename__ = "agent_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    mission_id: Mapped[str] = mapped_column(ForeignKey("journey_missions.id", ondelete="CASCADE"))
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    provider_key: Mapped[str] = mapped_column(String)
    model_key: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="RUNNING")
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
    started_at: Mapped[str] = mapped_column(String)
    completed_at: Mapped[str | None] = mapped_column(String, nullable=True)


class AgentRunStep(Base):
    """A compact, actionable trace of one model-selected tool call."""

    __tablename__ = "agent_run_steps"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id", ondelete="CASCADE"))
    sequence_no: Mapped[int] = mapped_column(Integer)
    tool_name: Mapped[str] = mapped_column(String)
    arguments_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    decision: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="COMPLETED")
    created_at: Mapped[str] = mapped_column(String)
    completed_at: Mapped[str | None] = mapped_column(String, nullable=True)


class AutopilotEnrollment(Base):
    """Per-Journey standing subscription for the process-global worker."""

    __tablename__ = "autopilot_enrollments"
    journey_id: Mapped[str] = mapped_column(
        ForeignKey("journeys.id", ondelete="CASCADE"), primary_key=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    interval_seconds: Mapped[float] = mapped_column(default=60.0, server_default="60")
    provider_mesh_json: Mapped[str] = mapped_column(Text, default="{}", server_default="{}")
    last_pulse_at: Mapped[str | None] = mapped_column(String, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class GuardianRun(Base):
    """Durable proactive scan and its idempotent recovery outcome."""

    __tablename__ = "guardian_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    standing_mission_id: Mapped[str | None] = mapped_column(
        ForeignKey("journey_missions.id", ondelete="SET NULL"), nullable=True
    )
    trigger_event_id: Mapped[str | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    agent_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True
    )
    proposal_id: Mapped[str | None] = mapped_column(
        ForeignKey("replan_proposals.id", ondelete="SET NULL"), nullable=True
    )
    decision: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="COMPLETED")
    action_status: Mapped[str] = mapped_column(String, default="NO_ACTION")
    evidence_fingerprint: Mapped[str] = mapped_column(String)
    evidence_json: Mapped[str] = mapped_column(Text, default="{}")
    reasoning_summary: Mapped[str] = mapped_column(Text, default="")
    active_plan_before_id: Mapped[str | None] = mapped_column(String, nullable=True)
    active_plan_after_id: Mapped[str | None] = mapped_column(String, nullable=True)
    trigger_kind: Mapped[str] = mapped_column(String, default="REACTIVE", server_default="REACTIVE")
    resilience_snapshot_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
    completed_at: Mapped[str | None] = mapped_column(String, nullable=True)
    cooldown_until: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (UniqueConstraint("journey_id", "evidence_fingerprint"),)


class ProviderObservation(Base):
    """Frozen provider evidence captured by the server-owned signal pipeline."""

    __tablename__ = "provider_observations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    provider_key: Mapped[str] = mapped_column(String)
    observation_type: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    incident_fingerprint: Mapped[str | None] = mapped_column(String, nullable=True)
    provenance: Mapped[str] = mapped_column(String, default="REPLAY", server_default="REPLAY")
    captured_at: Mapped[str] = mapped_column(String)
    expires_at: Mapped[str | None] = mapped_column(String, nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String)


class CitySignalFixture(Base):
    """Server-owned deterministic provider fixture used by offline demos/tests."""

    __tablename__ = "city_signal_fixtures"
    journey_id: Mapped[str] = mapped_column(
        ForeignKey("journeys.id", ondelete="CASCADE"), primary_key=True
    )
    provider_key: Mapped[str] = mapped_column(String, default="city-signal-fixture")
    state: Mapped[str] = mapped_column(String, default="NORMAL")
    revision: Mapped[int] = mapped_column(Integer, default=0)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[str] = mapped_column(String)


class GuardianPulse(Base):
    """One server-owned sensing/evaluation cycle."""

    __tablename__ = "guardian_pulses"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String, default="RUNNING")
    provider_key: Mapped[str] = mapped_column(String)
    observation_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    guardian_run_id: Mapped[str | None] = mapped_column(String, nullable=True)
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    started_at: Mapped[str] = mapped_column(String)
    completed_at: Mapped[str | None] = mapped_column(String, nullable=True)


class JourneyResilienceSnapshot(Base):
    """Deterministic risk projection; AI may explain it but cannot rewrite it."""

    __tablename__ = "journey_resilience_snapshots"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    score: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String)
    captured_at: Mapped[str] = mapped_column(String)
    expires_at: Mapped[str | None] = mapped_column(String, nullable=True)
    components_json: Mapped[str] = mapped_column(Text, default="{}")
    activity_risks_json: Mapped[str] = mapped_column(Text, default="[]")
    commitment_buffers_json: Mapped[str] = mapped_column(Text, default="[]")
    failure_modes_json: Mapped[str] = mapped_column(Text, default="[]")
    recommendation_json: Mapped[str] = mapped_column(Text, default="{}")
    provenance_json: Mapped[str] = mapped_column(Text, default="[]")
    fingerprint: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("journey_id", "fingerprint"),)


class CounterfactualSimulation(Base):
    """Bounded what-if result that never mutates domain truth."""

    __tablename__ = "counterfactual_simulations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    snapshot_id: Mapped[str | None] = mapped_column(
        ForeignKey("journey_resilience_snapshots.id", ondelete="SET NULL"), nullable=True
    )
    scenario_key: Mapped[str] = mapped_column(String)
    scenario_type: Mapped[str] = mapped_column(String)
    parameters_json: Mapped[str] = mapped_column(Text, default="{}")
    feasible: Mapped[bool] = mapped_column(Boolean)
    c4_preserved: Mapped[bool] = mapped_column(Boolean)
    cost_delta_minor: Mapped[int] = mapped_column(Integer, default=0)
    schedule_drift_min: Mapped[int] = mapped_column(Integer, default=0)
    plan_changes_json: Mapped[str] = mapped_column(Text, default="[]")
    evidence_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("journey_id", "scenario_key"),)


class RealPlaceCandidate(Base):
    """Provider-backed discovery evidence before/after Place materialization."""

    __tablename__ = "real_place_candidates"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str | None] = mapped_column(
        ForeignKey("journeys.id", ondelete="CASCADE"), nullable=True
    )
    provider_key: Mapped[str] = mapped_column(String)
    external_id: Mapped[str] = mapped_column(String)
    city_code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    latitude: Mapped[float] = mapped_column()
    longitude: Mapped[float] = mapped_column()
    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    opening_hours_json: Mapped[str] = mapped_column(Text, default="{}")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    captured_at: Mapped[str] = mapped_column(String)
    expires_at: Mapped[str | None] = mapped_column(String, nullable=True)
    distance_m: Mapped[float | None] = mapped_column(nullable=True)
    evidence_json: Mapped[str] = mapped_column(Text, default="{}")
    materialized_place_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="DISCOVERED")

    __table_args__ = (UniqueConstraint("provider_key", "external_id"),)


class JourneyConstraint(Base):
    __tablename__ = "constraints"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    rule_code: Mapped[str] = mapped_column(String)
    params_json: Mapped[str] = mapped_column(Text)
    weight: Mapped[float] = mapped_column()
    active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class Place(Base):
    __tablename__ = "places"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_key: Mapped[str] = mapped_column(String)
    external_id: Mapped[str] = mapped_column(String)
    city_code: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    latitude: Mapped[float] = mapped_column()
    longitude: Mapped[float] = mapped_column()
    opening_hours_json: Mapped[str] = mapped_column(Text)
    tags_json: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("provider_key", "external_id"),)


class CityService(Base):
    __tablename__ = "city_services"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_key: Mapped[str] = mapped_column(String)
    external_id: Mapped[str] = mapped_column(String)
    place_id: Mapped[str | None] = mapped_column(
        ForeignKey("places.id", ondelete="SET NULL"), nullable=True
    )
    city_code: Mapped[str] = mapped_column(String)
    service_type: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    availability_json: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("provider_key", "external_id"),)


class PlanVersion(Base):
    __tablename__ = "plan_versions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    version_no: Mapped[int] = mapped_column(Integer)
    planning_mode: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    parent_plan_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("plan_versions.id", ondelete="SET NULL"), nullable=True
    )
    total_cost_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String)
    estimated_duration_min: Mapped[int] = mapped_column(Integer)
    utility_score: Mapped[float | None] = mapped_column(nullable=True)
    score_breakdown_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("journey_id", "version_no"),)


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    plan_version_id: Mapped[str] = mapped_column(ForeignKey("plan_versions.id", ondelete="CASCADE"))
    sequence_no: Mapped[int] = mapped_column(Integer)
    activity_type: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    place_id: Mapped[str | None] = mapped_column(
        ForeignKey("places.id", ondelete="SET NULL"), nullable=True
    )
    city_service_id: Mapped[str | None] = mapped_column(
        ForeignKey("city_services.id", ondelete="SET NULL"), nullable=True
    )
    start_at: Mapped[str] = mapped_column(String)
    end_at: Mapped[str] = mapped_column(String)
    travel_from_prev_min: Mapped[int] = mapped_column(Integer)
    estimated_cost_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    locked: Mapped[bool] = mapped_column(Boolean)
    metadata_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("plan_version_id", "sequence_no"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    actor_type: Mapped[str] = mapped_column(String)
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    journey_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String)
    entity_type: Mapped[str | None] = mapped_column(String, nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    before_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)


# === WP04 COMMERCE ORM SCAFFOLD (generated) ===
class Commitment(Base):
    __tablename__ = "commitments"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    activity_id: Mapped[str | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String)
    level: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    monetary_value_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    policy_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    activity_id: Mapped[str | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    commitment_id: Mapped[str | None] = mapped_column(
        ForeignKey("commitments.id", ondelete="SET NULL"), nullable=True
    )
    provider_key: Mapped[str] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String)
    cancellation_policy_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    activity_id: Mapped[str | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    commitment_id: Mapped[str | None] = mapped_column(
        ForeignKey("commitments.id", ondelete="SET NULL"), nullable=True
    )
    provider_key: Mapped[str] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String)
    items_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class PaymentTransaction(Base):
    __tablename__ = "transactions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    booking_id: Mapped[str | None] = mapped_column(
        ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True
    )
    order_id: Mapped[str | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    provider_key: Mapped[str] = mapped_column(String)
    idempotency_key: Mapped[str] = mapped_column(String)
    transaction_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    provider_payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)

    __table_args__ = (UniqueConstraint("provider_key", "idempotency_key"),)


class ProviderCall(Base):
    __tablename__ = "provider_calls"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider_key: Mapped[str] = mapped_column(String)
    operation: Mapped[str] = mapped_column(String)
    request_json: Mapped[str] = mapped_column(Text)
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    operation: Mapped[str] = mapped_column(String)
    request_hash: Mapped[str] = mapped_column(Text)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
    expires_at: Mapped[str] = mapped_column(String)


class ActionApproval(Base):
    """Server-issued, scoped user approval receipt for a gated agent action."""

    __tablename__ = "action_approvals"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    traveler_id: Mapped[str] = mapped_column(ForeignKey("travelers.id", ondelete="CASCADE"))
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    action: Mapped[str] = mapped_column(String)
    target_type: Mapped[str] = mapped_column(String)
    target_id: Mapped[str] = mapped_column(String)
    request_fingerprint: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String)
    required_decision: Mapped[str] = mapped_column(String, default="REQUIRE_CONFIRMATION")
    approval_method: Mapped[str | None] = mapped_column(String, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
    expires_at: Mapped[str] = mapped_column(String)
    approved_at: Mapped[str | None] = mapped_column(String, nullable=True)
    consumed_at: Mapped[str | None] = mapped_column(String, nullable=True)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    provider_key: Mapped[str] = mapped_column(String)
    provenance: Mapped[str] = mapped_column(String, default="SIMULATED")
    event_type: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    affected_activity_id: Mapped[str | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    occurred_at: Mapped[str] = mapped_column(String)
    detected_at: Mapped[str] = mapped_column(String)
    resolved_at: Mapped[str | None] = mapped_column(String, nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String)


class ImpactAssessment(Base):
    """AI/deterministic impact provenance kept separate from Event truth."""

    __tablename__ = "impact_assessments"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    provider_key: Mapped[str] = mapped_column(String)
    model_key: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    maturity_stage: Mapped[str] = mapped_column(String, default="AI_ONLY")
    selected_corroboration_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    independent_evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    uncertain: Mapped[bool] = mapped_column(Boolean, default=False)
    selected_activity_id: Mapped[str | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    primary_recovery_target_id: Mapped[str | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    secondary_risk_activity_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    candidates_json: Mapped[str] = mapped_column(Text, default="[]")
    validated_activity_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    rejected_activity_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    reason_codes_json: Mapped[str] = mapped_column(Text, default="[]")
    semantic_reason: Mapped[str] = mapped_column(Text, default="")
    failure_code: Mapped[str | None] = mapped_column(String, nullable=True)
    response_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String)


class JourneyTwin(Base):
    __tablename__ = "journey_twins"
    journey_id: Mapped[str] = mapped_column(
        ForeignKey("journeys.id", ondelete="CASCADE"), primary_key=True
    )
    active_plan_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("plan_versions.id", ondelete="SET NULL"), nullable=True
    )
    current_activity_id: Mapped[str | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    latest_event_id: Mapped[str | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    projection_status: Mapped[str] = mapped_column(String)
    snapshot_at: Mapped[str] = mapped_column(String)
    context_json: Mapped[str] = mapped_column(Text, default="{}")
    upcoming_commitments_json: Mapped[str] = mapped_column(Text, default="[]")
    updated_at: Mapped[str] = mapped_column(String)


class ReplanProposal(Base):
    __tablename__ = "replan_proposals"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    journey_id: Mapped[str] = mapped_column(ForeignKey("journeys.id", ondelete="CASCADE"))
    trigger_event_id: Mapped[str | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    base_plan_version_id: Mapped[str] = mapped_column(
        ForeignKey("plan_versions.id", ondelete="RESTRICT")
    )
    proposed_plan_version_id: Mapped[str] = mapped_column(
        ForeignKey("plan_versions.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(String)
    hard_constraints_passed: Mapped[bool] = mapped_column(Boolean)
    locked_commitments_preserved: Mapped[bool] = mapped_column(Boolean)
    utility_score: Mapped[float] = mapped_column()
    score_breakdown_json: Mapped[str] = mapped_column(Text)
    diff_json: Mapped[str] = mapped_column(Text)
    explanation_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String)
    decided_at: Mapped[str | None] = mapped_column(String, nullable=True)
