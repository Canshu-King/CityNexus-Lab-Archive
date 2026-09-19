"""Key V9 frozen mobility evidence by canonical semantic identity (clean form)."""

from pathlib import Path

P = Path("D:/moodle/CityNexus/backend/app/operations/v9.py")
s = P.read_text(encoding="utf-8")

old = '''    # Freeze the mobility evidence under the *same* canonical semantic identity
    # the materialized Activities carry, so persistence, selection, booking,
    # start and replanning all reload one consistent graph.
    canonical_facts = [
        replace_fact_identity(fact, node_key=_canonical_node_semantic_key(journey, node))
        for fact, node in zip(facts, nodes)
    ]
    mobility_snapshot_id, mobility_evidence = _mobility_evidence_bundle(
        canonical_facts,'''
new = '''    # Freeze the mobility evidence under the *same* canonical semantic identity
    # the materialized Activities carry, so persistence, selection, booking,
    # start and replanning all reload one consistent graph.
    canonical_key_by_node_key = {
        str(node.key): _canonical_node_semantic_key(journey, node) for node in nodes
    }
    canonical_facts = [
        retarget_fact(
            fact,
            from_key=canonical_key_by_node_key.get(str(fact.from_key), fact.from_key),
            to_key=canonical_key_by_node_key.get(str(fact.to_key), fact.to_key),
        )
        for fact in facts
    ]
    mobility_snapshot_id, mobility_evidence = _mobility_evidence_bundle(
        canonical_facts,'''
assert old in s, "canonical facts block not found"
s = s.replace(old, new, 1)

old2 = '''def replace_fact_identity(fact: MobilityFact, *, node_key: str) -> MobilityFact:
    """Return a copy of a mobility fact under a canonical semantic identity."""

    return MobilityFact(
        id=fact.id,
        journey_id=fact.journey_id,
        option_id=fact.option_id,
        from_key=node_key,
        to_key=fact.to_key,'''
new2 = '''def retarget_fact(fact: MobilityFact, *, from_key: str, to_key: str) -> MobilityFact:
    """Return a copy of a mobility fact under canonical semantic identities."""

    return MobilityFact(
        id=fact.id,
        journey_id=fact.journey_id,
        option_id=fact.option_id,
        from_key=from_key,
        to_key=to_key,'''
assert old2 in s, "replace_fact_identity not found"
s = s.replace(old2, new2, 1)
P.write_text(s, encoding="utf-8", newline="\n")
print("ok")
