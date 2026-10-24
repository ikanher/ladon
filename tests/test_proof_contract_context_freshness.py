"""Term-stage input custody, with real local files and bounded hash checks."""
import hashlib

import pytest

from ladon import proof_contract_context_worker as worker


def test_term_stage_rejects_changed_original_source_and_quote(tmp_path, monkeypatch):
    original = tmp_path / 'Original.lean'
    quote = tmp_path / 'claim.txt'
    original.write_text('import Lean\n')
    quote.write_text('Original quoted reading.\n')
    environment = 'sha256:' + 'a' * 64
    binding = {'originalSource': {'path': original.name,
        'sha256': hashlib.sha256(original.read_bytes()).hexdigest()},
        'selection': {'module': 'Original'}, 'environment': environment,
        'originalInterpretation': {'source': {'path': quote.name,
            'sha256': hashlib.sha256(quote.read_bytes()).hexdigest()}}}
    monkeypatch.setattr(worker, '_environment', lambda _root: environment, raising=False)
    worker._verify_original_inputs(tmp_path, binding)
    original.write_text('import Lean\n-- drift\n')
    with pytest.raises(ValueError, match='changed'):
        worker._verify_original_inputs(tmp_path, binding)
    original.write_text('import Lean\n')
    quote.write_text('Strengthened quoted reading.\n')
    with pytest.raises(ValueError, match='changed'):
        worker._verify_original_inputs(tmp_path, binding)


def test_term_stage_rejects_environment_drift_even_with_unchanged_files(tmp_path, monkeypatch):
    original = tmp_path / 'Original.lean'
    quote = tmp_path / 'claim.txt'
    original.write_text('import Lean\n')
    quote.write_text('Original.\n')
    binding = {'originalSource': {'path': original.name,
        'sha256': hashlib.sha256(original.read_bytes()).hexdigest()},
        'selection': {'module': 'Original'}, 'environment': 'sha256:' + 'a' * 64,
        'originalInterpretation': {'source': {'path': quote.name,
            'sha256': hashlib.sha256(quote.read_bytes()).hexdigest()}}}
    monkeypatch.setattr(worker, '_environment', lambda _root: 'sha256:' + 'b' * 64, raising=False)
    with pytest.raises(ValueError, match='environment'):
        worker._verify_original_inputs(tmp_path, binding)
