"""A verified generation must agree with the transaction used for result rows."""
import sqlite3

from ladon.cli import main
from ladon.proof_search_index import build_proof_search_index


def test_generation_change_after_verification_is_rejected(tmp_path, monkeypatch, capsys):
    from ladon import proof_search_type_cli as cli

    (tmp_path / 'Main.lean').write_text('theorem first : Nat := 1\n')
    path = build_proof_search_index(tmp_path).index_path
    original = cli.type_text_freshness

    def replace_generation(*args):
        evidence = original(*args)
        with sqlite3.connect(path) as connection:
            connection.execute("UPDATE metadata SET value = 'changed' WHERE key = 'generationIdentity'")
        return evidence

    monkeypatch.setattr(cli, 'type_text_freshness', replace_generation)
    assert main(['proof-search', 'search', 'type-text', '--repo-root', str(tmp_path),
                 '--pattern', 'Nat', '--freshness', 'verify', '--format', 'json']) != 0
    captured = capsys.readouterr()
    assert 'generation changed' in captured.err
    assert not captured.out
