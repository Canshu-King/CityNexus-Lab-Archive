from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSIST_ROOT = HERE.parent
REFERENCE = ASSIST_ROOT / 'reference_patch' / 'backend'


def _load_extractor():
    path = HERE / 'extract_commitment_strengths.py'
    spec = importlib.util.spec_from_file_location('extract_commitment_strengths', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _source_codes(yaml_path: Path) -> tuple[str, ...]:
    import yaml

    extractor = _load_extractor()
    document = yaml.safe_load(yaml_path.read_text(encoding='utf-8'))
    _, codes = extractor.resolve(document)
    return codes


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _append_once(path: Path, marker: str, block: str) -> None:
    text = path.read_text(encoding='utf-8')
    if marker in text:
        return
    path.write_text(text.rstrip() + '\n\n' + marker + '\n' + block.rstrip() + '\n', encoding='utf-8')


def _model_block() -> str:
    text = (REFERENCE / 'app/commerce/models_reference.py').read_text(encoding='utf-8')
    start = text.index('class Commitment(')
    return text[start:]


def _schema_block() -> str:
    text = (REFERENCE / 'app/commerce/schemas_reference.py').read_text(encoding='utf-8')
    start = text.index('class BookingSlot(')
    return text[start:]


def _replace_sql_strengths(schema_path: Path, codes: tuple[str, ...]) -> None:
    text = schema_path.read_text(encoding='utf-8')
    pattern = re.compile(r"(CREATE TABLE IF NOT EXISTS commitments \(.*?\n\s*level TEXT NOT NULL CHECK \(level IN \()([^\)]*)(\)\),)", re.S)
    match = pattern.search(text)
    if not match:
        raise RuntimeError('Could not locate commitments.level CHECK in backend/db/schema.sql')
    enum_sql = ','.join(repr(code) for code in codes)
    replacement = match.group(1) + enum_sql + match.group(3)
    schema_path.write_text(text[:match.start()] + replacement + text[match.end():], encoding='utf-8')


def _replace_openapi_strengths(openapi_path: Path, codes: tuple[str, ...]) -> None:
    text = openapi_path.read_text(encoding='utf-8')
    old_pattern = re.compile(r"(\n\s*level:\s*\{type: string, enum: \[)([^\]]+)(\]\})")
    matches = list(old_pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f'Expected exactly one Commitment level enum in OpenAPI; found {len(matches)}')
    match = matches[0]
    enum_yaml = ', '.join(codes)
    text = text[:match.start()] + match.group(1) + enum_yaml + match.group(3) + text[match.end():]
    openapi_path.write_text(text, encoding='utf-8')


def _write_generated_strengths(repo: Path, codes: tuple[str, ...], source: Path) -> None:
    extractor = _load_extractor()
    target = repo / 'backend/app/commerce/strengths_generated.py'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(extractor.render_python(codes, str(source)), encoding='utf-8')


def apply(repo: Path, yaml_path: Path) -> tuple[str, ...]:
    required = [
        repo / 'backend/app/db/models.py',
        repo / 'backend/app/schemas.py',
        repo / 'backend/db/schema.sql',
        repo / 'contracts/openapi.yaml',
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f'Not a CityNexus MVP repo layout; missing: {missing}')

    codes = _source_codes(yaml_path)
    if len(codes) != 5:
        raise RuntimeError('exactly five source commitment strengths required')

    # Add isolated commerce/policy code. These files are intentionally new to minimise merge conflicts.
    for rel in [
        'app/commerce/__init__.py',
        'app/commerce/commitment_policy.py',
        'app/commerce/idempotency.py',
        'app/commerce/validators.py',
        'app/commerce/service_reference.py',
        'app/commerce/order_pricing.py',
        'app/integrations/commerce_ports.py',
        'app/integrations/mock/commerce_providers.py',
    ]:
        _copy(REFERENCE / rel, repo / 'backend' / rel)


    for rel in [
        'data/mock/wp04_commerce_catalog.json',
        'data/mock/wp04_city_services_overlay.json',
    ]:
        _copy(REFERENCE / rel, repo / 'backend' / rel)

    _write_generated_strengths(repo, codes, yaml_path)

    _append_once(
        repo / 'backend/app/db/models.py',
        '# === WP04 COMMERCE ORM SCAFFOLD (generated) ===',
        _model_block(),
    )
    _append_once(
        repo / 'backend/app/schemas.py',
        '# === WP04 COMMERCE API SCHEMAS (generated) ===',
        _schema_block(),
    )

    _replace_sql_strengths(repo / 'backend/db/schema.sql', codes)
    _replace_openapi_strengths(repo / 'contracts/openapi.yaml', codes)

    # Pure reference/contract tests are safe to add before endpoint implementation.
    _copy(
        REFERENCE / 'tests/test_wp04_reference_contract.py',
        repo / 'backend/tests/test_wp04_reference_contract.py',
    )
    _copy(
        REFERENCE / 'tests/test_wp04_validators.py',
        repo / 'backend/tests/test_wp04_validators.py',
    )
    _copy(
        REFERENCE / 'tests/test_wp04_order_pricing.py',
        repo / 'backend/tests/test_wp04_order_pricing.py',
    )
    return codes


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Apply only the low-conflict WP04A/B scaffold after the pre-WP04 WP03 gate is green.'
    )
    parser.add_argument('repo', type=Path)
    parser.add_argument('frozen_domain_yaml', type=Path)
    args = parser.parse_args()
    codes = apply(args.repo.resolve(), args.frozen_domain_yaml.resolve())
    print('WP04 scaffold applied. Exact source strength codes by rank:')
    for rank, code in enumerate(codes):
        print(f'  C{rank}: {code}')
    print('No booking/payment endpoints were added. Continue with CODEX_WP04_START_INSTRUCTION.md.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
