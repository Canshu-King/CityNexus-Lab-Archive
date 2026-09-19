from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit('PyYAML is required: pip install PyYAML') from exc

RANK_RE = re.compile(r'^C([0-4])[_-].+')


def walk(value: Any, path: tuple[str, ...] = ()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, (*path, str(key)))
    elif isinstance(value, list):
        yield path, value
        for index, child in enumerate(value):
            yield from walk(child, (*path, str(index)))


def candidate_codes(value: list[Any]) -> tuple[str, ...] | None:
    if len(value) != 5 or not all(isinstance(item, str) for item in value):
        return None
    ranked: dict[int, str] = {}
    for item in value:
        match = RANK_RE.match(item)
        if not match:
            return None
        rank = int(match.group(1))
        if rank in ranked:
            return None
        ranked[rank] = item
    if set(ranked) != set(range(5)):
        return None
    return tuple(ranked[i] for i in range(5))


def find_candidates(document: Any) -> list[tuple[tuple[str, ...], tuple[str, ...]]]:
    candidates: list[tuple[tuple[str, ...], tuple[str, ...]]] = []
    for path, value in walk(document):
        codes = candidate_codes(value) if isinstance(value, list) else None
        if codes:
            candidates.append((path, codes))
    return candidates


def score_path(path: tuple[str, ...]) -> int:
    text = '.'.join(path).lower()
    score = 0
    if 'commitment' in text:
        score += 10
    if 'strength' in text:
        score += 10
    if 'enum' in text:
        score += 3
    return score


def resolve(document: Any) -> tuple[tuple[str, ...], tuple[str, ...]]:
    candidates = find_candidates(document)
    if not candidates:
        raise ValueError('No exact C0..C4 five-value enum list found')
    ranked = sorted(candidates, key=lambda item: score_path(item[0]), reverse=True)
    best_score = score_path(ranked[0][0])
    best = [item for item in ranked if score_path(item[0]) == best_score]
    if best_score < 10:
        details = [('.'.join(path), list(codes)) for path, codes in ranked]
        raise ValueError(f'Found C0..C4 lists but none is clearly commitment-related: {details}')
    unique_code_sets = {codes for _, codes in best}
    if len(unique_code_sets) != 1:
        details = [('.'.join(path), list(codes)) for path, codes in best]
        raise ValueError(f'Ambiguous commitment-strength enum candidates: {details}')
    return best[0]


def render_python(codes: tuple[str, ...], source_path: str) -> str:
    encoded = ',\n    '.join(repr(code) for code in codes)
    return (
        '# Generated from the frozen CityNexus domain YAML by '
        'tools/extract_commitment_strengths.py.\n'
        '# Do not hand-invent or rename these source-domain values.\n'
        f'# Source file: {source_path}\n\n'
        'SOURCE_COMMITMENT_STRENGTHS: tuple[str, str, str, str, str] = (\n'
        f'    {encoded},\n'
        ')\n\n'
        'SOURCE_COMMITMENT_STRENGTH_BY_RANK = dict(enumerate(SOURCE_COMMITMENT_STRENGTHS))\n'
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Read only the exact five C0..C4 commitment-strength codes from frozen YAML.'
    )
    parser.add_argument('yaml_path', type=Path)
    parser.add_argument('--json-out', type=Path)
    parser.add_argument('--python-out', type=Path)
    args = parser.parse_args()

    document = yaml.safe_load(args.yaml_path.read_text(encoding='utf-8'))
    path, codes = resolve(document)
    payload = {
        'source_file': str(args.yaml_path),
        'yaml_path': '.'.join(path),
        'codes_by_rank': list(codes),
        'count': 5,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.python_out:
        args.python_out.parent.mkdir(parents=True, exist_ok=True)
        args.python_out.write_text(render_python(codes, str(args.yaml_path)), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
