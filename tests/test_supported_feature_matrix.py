from __future__ import annotations

import importlib.util
from pathlib import Path


def _generator():
    path = Path(__file__).parents[1] / "scripts/generate_supported_feature_matrix.py"
    spec = importlib.util.spec_from_file_location("supported_feature_matrix", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_matrix_profiles_and_semantic_requirements_have_collectable_nodes() -> None:
    generator = _generator()
    assert {feature['id']: feature['profile'] for feature in generator.FEATURES if feature['profile'] != 'extra'} == {
        'architecture-review': 'secondary', 'type-text-declaration-search': 'primary',
        'verified-proposition-discovery': 'primary', 'evidence-and-lineage-inspection': 'audit'}
    root = Path(__file__).parents[1]
    for feature in generator.FEATURES:
        assert feature["tests"]
        for node in feature["tests"]:
            relative, test_name = node.split("::", 1)
            source = root.joinpath(relative).read_text(encoding="utf-8")
            assert f"def {test_name}(" in source
    for nodes in generator.SEMANTIC_REQUIREMENTS.values():
        for node in nodes:
            relative, test_name = node.split('::', 1)
            assert f'def {test_name}(' in root.joinpath(relative).read_text()


def test_committed_matrix_matches_generator() -> None:
    generator = _generator()
    root = Path(__file__).parents[1]
    assert (root / "docs/SUPPORTED_FEATURE_MATRIX.json").read_text(
        encoding="utf-8"
    ) == generator.render_json()
    assert (root / "docs/SUPPORTED_FEATURE_MATRIX.md").read_text(
        encoding="utf-8"
    ) == generator.render_markdown()


def test_missing_execution_evidence_demotes_every_feature() -> None:
    payload = _generator().matrix_payload()
    assert all(feature['readiness'] == 'experimental' for feature in payload['features'])


def test_generator_uses_resolved_candidate_evidence_and_demotes_missing_nodes(tmp_path, monkeypatch):
    import json

    from test_readiness import qualified_case

    evidence, context = qualified_case.__wrapped__(tmp_path)
    generator = _generator()
    node = 'tests/test_alpha.py::test_case'
    monkeypatch.setattr(generator, 'SEMANTIC_REQUIREMENTS', {'synthetic': (node, node, node)})
    inventory = tmp_path / 'selected-inventory.json'
    inventory.write_text(json.dumps(context['inventories']['installedSmoke']))
    registry = {'inventoryPath': str(inventory), 'bundleRoot': str(tmp_path),
                'features': {'synthetic': evidence}}
    feature = {'id': 'synthetic', 'profile': 'primary', 'tests': (node,)}
    row = generator.feature_row(feature, registry)
    assert row['readiness'] == 'contract-supported'
    assert row['candidateCommit'] == '1' * 40
    generator.SEMANTIC_REQUIREMENTS['synthetic'] = (node, node, 'tests/test_alpha.py::test_omitted')
    assert generator.feature_row(feature, registry)['readiness'] == 'experimental'


def test_candidate_markdown_keeps_commands_timestamps_and_execution_limitations(tmp_path, monkeypatch):
    import json

    from test_readiness import qualified_case

    evidence, context = qualified_case.__wrapped__(tmp_path)
    evidence['installedSmoke']['limitations'] = ['Local integrity does not authenticate producers.']
    generator = _generator()
    node = 'tests/test_alpha.py::test_case'
    monkeypatch.setattr(generator, 'SEMANTIC_REQUIREMENTS', {'synthetic': (node, node, node)})
    monkeypatch.setattr(generator, 'FEATURES', ({'id': 'synthetic', 'profile': 'primary',
                                               'summary': 'Synthetic contract', 'tests': (node,)},))
    inventory = tmp_path / 'selected-inventory.json'
    inventory.write_text(json.dumps(context['inventories']['installedSmoke']))
    registry = {'inventoryPath': str(inventory), 'bundleRoot': str(tmp_path), 'features': {'synthetic': evidence}}
    markdown = generator.render_markdown(registry)
    for value in ('1' * 40, evidence['installedSmoke']['timestamp'],
                  evidence['installedSmoke']['command'], evidence['installedSmoke']['sourceTreeIdentity'],
                  evidence['installedSmoke']['environmentRef'], 'Local integrity does not authenticate producers.'):
        assert value in markdown
