"""Key V9 frozen mobility evidence by the canonical semantic identity."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/operations/v9.py")
s = P.read_text(encoding="utf-8")

# 1. Build the canonical evidence bundle from canonical node identities.
old = '''    mobility_snapshot_id, mobility_evidence = _mobility_evidence_bundle(
        facts,
        journey_id=journey.id,
        operation_key=f"stay-option:{option.id}:{source}",
        stay_offer=offer,
    )'''
new = '''    # Freeze the mobility evidence under the *same* canonical semantic identity
    # the materialized Activities carry, so persistence, selection, booking,
    # start and replanning all reload one consistent graph.
    canonical_facts = [
        replace_fact_identity(fact, node_key=_canonical_node_semantic_key(journey, node))
        for fact, node in zip(facts, nodes)
    ]
    mobility_snapshot_id, mobility_evidence = _mobility_evidence_bundle(
        canonical_facts,
        journey_id=journey.id,
        operation_key=f"stay-option:{option.id}:{source}",
        stay_offer=offer,
    )'''
assert old in s, "evidence bundle not found"
s = s.replace(old, new, 1)

# 2. Persist JourneyLeg rows under canonical identity too.
old2 = '''                from_key=fact.from_key,
                to_key=fact.to_key,'''
new2 = '''                from_key=_canonical_node_semantic_key(journey, nodes[index - 1]),
                to_key=_canonical_node_semantic_key(journey, nodes[index]),'''
assert old2 in s, "journey leg keys not found"
s = s.replace(old2, new2, 1)

helpers = '''

def replace_fact_identity(fact: MobilityFact, *, node_key: str) -> MobilityFact:
    """Return a copy of a mobility fact under a canonical semantic identity."""

    return MobilityFact(
        id=fact.id,
        journey_id=fact.journey_id,
        option_id=fact.option_id,
        from_key=node_key,
        to_key=fact.to_key,
        mode=fact.mode,
        duration_min=fact.duration_min,
        distance_m=fact.distance_m,
        cost_amount_minor=fact.cost_amount_minor,
        currency=fact.currency,
        cost_status=fact.cost_status,
        walking_min=fact.walking_min,
        transfers=fact.transfers,
        reliability_score=fact.reliability_score,
        weather_exposure=fact.weather_exposure,
        geometry_json=fact.geometry_json,
        crs=fact.crs,
        provider_key=fact.provider_key,
        provenance=fact.provenance,
        provider_snapshot_id=fact.provider_snapshot_id,
        captured_at=fact.captured_at,
        expires_at=fact.expires_at,
    )
'''
s = s.replace('\n\n_STRUCTURAL_NODE_KEYS = {', helpers + '\n\n_STRUCTURAL_NODE_KEYS = {', 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("v9 evidence identity patched")
