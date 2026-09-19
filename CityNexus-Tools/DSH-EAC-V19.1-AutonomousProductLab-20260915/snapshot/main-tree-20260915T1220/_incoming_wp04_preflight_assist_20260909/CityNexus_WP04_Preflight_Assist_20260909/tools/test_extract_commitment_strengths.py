from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name('extract_commitment_strengths.py')
spec = importlib.util.spec_from_file_location('extract_commitment_strengths', MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def test_resolves_commitment_strength_list_and_orders_by_rank():
    doc = {
        'enums': {
            'commitment_strength': [
                'C3_SourceValue', 'C0_Flexible', 'C2_SourceValue', 'C4_Anchored', 'C1_SourceValue'
            ]
        }
    }
    path, codes = mod.resolve(doc)
    assert path == ('enums', 'commitment_strength')
    assert codes == (
        'C0_Flexible', 'C1_SourceValue', 'C2_SourceValue', 'C3_SourceValue', 'C4_Anchored'
    )


def test_ignores_unrelated_non_five_value_lists():
    doc = {
        'enums': {
            'planning_mode': ['balanced', 'budget', 'explore', 'strict_schedule'],
            'commitment_strength': ['C0_Flexible', 'C1_A', 'C2_B', 'C3_C', 'C4_Anchored'],
        }
    }
    _, codes = mod.resolve(doc)
    assert len(codes) == 5


def test_refuses_to_guess_if_no_clear_commitment_path():
    doc = {'something': ['C0_A', 'C1_B', 'C2_C', 'C3_D', 'C4_E']}
    try:
        mod.resolve(doc)
    except ValueError as exc:
        assert 'commitment-related' in str(exc)
    else:
        raise AssertionError('expected refusal to guess')
