"""Generation equality is distinct from merely having a fresh index."""
import json

from ladon.cli import main
from ladon.proof_search_index import build_proof_search_index


def test_expected_generation_controls(tmp_path, capsys):
    (tmp_path / 'Main.lean').write_text('def first : Nat := 1\n')
    generation = build_proof_search_index(tmp_path).payload['generationIdentity']
    args = ['proof-search', 'index', 'freshness', '--repo-root', str(tmp_path), '--format', 'json']
    for expected, unchanged in [(generation, True), ('different-generation', False)]:
        assert main(args + ['--expected-generation', expected]) == 0
        result = json.loads(capsys.readouterr().out)
        assert result['freshness'] == 'fresh'
        assert result['unchangedSinceExpectedGeneration'] is unchanged


def test_missing_index_does_not_create_one(tmp_path, capsys):
    assert main(['proof-search', 'index', 'freshness', '--repo-root', str(tmp_path),
                 '--format', 'json']) != 0
    assert not (tmp_path / '.ladon').exists()
    assert capsys.readouterr().err
