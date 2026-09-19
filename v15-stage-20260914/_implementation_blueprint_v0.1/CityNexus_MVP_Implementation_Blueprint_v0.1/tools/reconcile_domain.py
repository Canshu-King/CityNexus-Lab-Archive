#!/usr/bin/env python3
"""Read-only helper to reconcile this blueprint with the actual local domain YAML.

Usage:
    python tools/reconcile_domain.py D:/moodle/CityNexus/domain-model/<current>.yaml

The script intentionally makes no modifications.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

BLUEPRINT_ENTITIES = {
    "Traveler", "Journey", "JourneyTwin", "PlanVersion", "Activity", "Place",
    "CityService", "Commitment", "Constraint", "Event", "ReplanProposal",
    "Booking", "Order", "Transaction", "Recommendation", "Preference",
}


def collect_named_entities(obj: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_l = str(key).lower().replace("-", "_")
            if key_l in {"entities", "core_entities", "domain_entities"}:
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            found.add(item)
                        elif isinstance(item, dict):
                            for candidate_key in ("name", "entity", "id"):
                                candidate = item.get(candidate_key)
                                if isinstance(candidate, str):
                                    found.add(candidate)
                                    break
                elif isinstance(value, dict):
                    found.update(str(k) for k in value.keys())
            found.update(collect_named_entities(value))
    elif isinstance(obj, list):
        for item in obj:
            found.update(collect_named_entities(item))
    return found


def find_planning_mode(obj: Any) -> list[str]:
    values: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).lower().replace("-", "_") == "planning_mode":
                if isinstance(value, list):
                    values.extend(str(x) for x in value)
                elif isinstance(value, dict):
                    for enum_key in ("enum", "values", "allowed"):
                        enum = value.get(enum_key)
                        if isinstance(enum, list):
                            values.extend(str(x) for x in enum)
            values.extend(find_planning_mode(value))
    elif isinstance(obj, list):
        for item in obj:
            values.extend(find_planning_mode(item))
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("domain_yaml", type=Path)
    args = parser.parse_args()
    data = yaml.safe_load(args.domain_yaml.read_text(encoding="utf-8"))
    entities = collect_named_entities(data)
    modes = sorted(set(find_planning_mode(data)))
    print(f"Detected entity-like names: {len(entities)}")
    for name in sorted(entities):
        marker = "known" if name in BLUEPRINT_ENTITIES else "not-in-blueprint"
        print(f"- {name} [{marker}]")
    print("\nBlueprint-known entities missing from detected set:")
    for name in sorted(BLUEPRINT_ENTITIES - entities):
        print(f"- {name}")
    print("\nDetected planning_mode values:")
    for mode in modes:
        print(f"- {mode}")
    print("\nExpected source-backed planning_mode values:")
    for mode in ["balanced", "budget", "explore", "strict_schedule"]:
        print(f"- {mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
