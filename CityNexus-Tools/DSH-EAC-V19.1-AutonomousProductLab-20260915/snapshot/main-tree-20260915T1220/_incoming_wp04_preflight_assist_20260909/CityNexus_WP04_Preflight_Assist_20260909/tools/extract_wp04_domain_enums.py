from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def walk_dicts(value: Any, path: tuple[str, ...] = ()):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk_dicts(child, (*path, str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_dicts(child, (*path, str(index)))


def find_named_lists(document: Any, target_key: str) -> list[tuple[tuple[str, ...], list[str]]]:
    found: list[tuple[tuple[str, ...], list[str]]] = []
    needle = target_key.lower()
    for path, mapping in walk_dicts(document):
        for key, value in mapping.items():
            if str(key).lower() != needle:
                continue
            if isinstance(value, list) and value and all(isinstance(x, str) for x in value):
                found.append(((*path, str(key)), list(value)))
            elif isinstance(value, dict):
                for child_key in ('values', 'allowed', 'enum', 'items'):
                    child = value.get(child_key)
                    if isinstance(child, list) and child and all(isinstance(x, str) for x in child):
                        found.append(((*path, str(key), child_key), list(child)))
    return found


def require_unique_named_list(document: Any, key: str) -> tuple[tuple[str, ...], list[str]]:
    found = find_named_lists(document, key)
    if not found:
        raise ValueError(f'No string-list definition found for {key!r}')
    unique = {tuple(values) for _, values in found}
    if len(unique) != 1:
        raise ValueError(
            f'Ambiguous definitions for {key!r}: '
            + repr([('.'.join(path), values) for path, values in found])
        )
    return found[0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Read only WP04-relevant enum lists from the frozen CityNexus domain YAML.'
    )
    parser.add_argument('yaml_path', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    doc = yaml.safe_load(args.yaml_path.read_text(encoding='utf-8'))

    # commitment_strength is required to contain exactly the source C0..C4 codes.
    strength_path, strengths = require_unique_named_list(doc, 'commitment_strength')
    if len(strengths) != 5:
        raise ValueError(f'commitment_strength must have exactly five values; found {strengths}')

    # This enum is required by FR-029 traceability. We read it now to avoid another lossy mapping.
    source_type_path, source_types = require_unique_named_list(doc, 'commitment_source_type')

    payload = {
        'commitment_strength': {
            'yaml_path': '.'.join(strength_path),
            'values': strengths,
        },
        'commitment_source_type': {
            'yaml_path': '.'.join(source_type_path),
            'values': source_types,
        },
    }
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
    print(encoded, end='')
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
