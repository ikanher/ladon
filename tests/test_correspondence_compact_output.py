"""Public complete native bundles stay consumable under the unchanged 32 MiB cap."""
import hashlib
import json

import pytest


def test_public_attach_compacts_three_complete_near_cap_native_bundles(tmp_path, capsys):
    """Three valid public bundles must fit compactly and remain complete on reload."""
    from ladon.entrypoint import main
    from ladon.investigation_correspondence_cli import load_investigation

    root = tmp_path
    source = root / 'source.txt'
    source.write_text('Three complete interpretations are attached.\n', encoding='utf-8')
    # The admitted maximum symbol count and a long, lexically valid identifier
    # create ordinary public interpretations whose duplicated native payloads
    # fit under 32 MiB compactly but cross it after pretty-print expansion.
    symbol_name = 'a' * 1310
    symbols = {f's{i:04d}': {'leanName': symbol_name, 'leanType': 'Nat'}
               for i in range(4096)}

    plan = tmp_path / 'plan.json'
    assert main(['investigation', 'init', '--text', str(source), '--root', str(root),
                 '--output', str(plan), '--minutes', '90', '--correspondence']) == 0
    for index in range(3):
        plan = _attach_one(root, source, symbols, index, plan, capsys, main)

    cap = 32 * 1024**2
    assert plan.stat().st_size <= cap
    loaded = load_investigation(plan)
    assert len(loaded['correspondenceBundles']) == 3
    for index, entry in enumerate(loaded['correspondenceBundles']):
        assert entry['bundle']['record']['id'] == f'large-native-{index}'
        assert entry['bundle']['record']['symbols'] == symbols


def test_true_over_cap_is_explicit_and_does_not_publish_partial_output(tmp_path):
    from ladon.correspondence_cli import publish
    output = tmp_path / "too-large.json"
    with pytest.raises(ValueError, match="32 MiB"):
        publish({"evidence": "x" * (32 * 1024**2)}, output)
    assert not output.exists()


def _attach_one(root, source, symbols, index, plan, capsys, main):
    tmp_path = root
    record = {
        'id': f'large-native-{index}',
        'source': {'path': source.name, 'startLine': 1, 'endLine': 1,
                   'quote': 'Three complete interpretations are attached.',
                   'sha256': hashlib.sha256(source.read_bytes()).hexdigest()},
        'formula': {'tag': 'const', 'name': 'True'},
        'symbols': symbols,
    }
    record_path = tmp_path / f'record-{index}.json'
    bundle_path = tmp_path / f'bundle-{index}.json'
    record_path.write_text(json.dumps(record, separators=(',', ':')), encoding='utf-8')
    assert main(['investigation', 'interpret', '--record', str(record_path),
                 '--root', str(root), '--output', str(bundle_path)]) == 0
    output = tmp_path / f'attached-{index}.json'
    code = main(['investigation', 'attach', '--plan', str(plan), '--bundle', str(bundle_path),
                 '--root', str(root), '--output', str(output)])
    assert code == 0, capsys.readouterr().out
    return output

