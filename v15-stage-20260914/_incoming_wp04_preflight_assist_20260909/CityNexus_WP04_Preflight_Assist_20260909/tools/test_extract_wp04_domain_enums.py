from __future__ import annotations

import importlib.util
from pathlib import Path

P = Path(__file__).with_name('extract_wp04_domain_enums.py')
spec = importlib.util.spec_from_file_location('extract_wp04_domain_enums', P)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def test_reads_wp04_named_enums_without_guessing():
    doc = {
        'enums': {
            'commitment_strength': ['C0_Flexible', 'C1_A', 'C2_B', 'C3_C', 'C4_Anchored'],
            'commitment_source_type': ['booking', 'order', 'payment', 'appointment'],
        }
    }
    _, strengths = mod.require_unique_named_list(doc, 'commitment_strength')
    _, sources = mod.require_unique_named_list(doc, 'commitment_source_type')
    assert strengths[0] == 'C0_Flexible' and strengths[-1] == 'C4_Anchored'
    assert sources == ['booking', 'order', 'payment', 'appointment']


def test_refuses_ambiguous_named_enum_definitions():
    doc = {
        'a': {'commitment_source_type': ['booking']},
        'b': {'commitment_source_type': ['payment']},
    }
    try:
        mod.require_unique_named_list(doc, 'commitment_source_type')
    except ValueError as exc:
        assert 'Ambiguous' in str(exc)
    else:
        raise AssertionError('expected ambiguity rejection')
