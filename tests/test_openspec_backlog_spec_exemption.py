"""Respect OpenSpec's explicit pure-refactor exemption without inventing deltas."""
import json

import pytest
from test_openspec_backlog import write_change

from ladon.analysis.openspec_backlog import summarize_openspec_backlog


@pytest.mark.parametrize('setting,exempt', [
    ('skip_specs: true\n', True),
    ('skip_specs: true # pure refactor\n', True),
    ('skip_specs: true#not-a-comment\n', False),
    ('skip_specs:true\n', False),
    ('skip_specs: truefalse\n', False),
    ('skip_specs: false\n', False),
    ('', False),
    ('  skip_specs: true\n', False),
    ('skip_specs: "false"\n', False),
    ('skip_specs: true\nskip_specs: false\n', False),
    ('skip_specs: true\nskip_specs : false\n', False),
    ('skip_specs: true\n"skip_specs": false\n', False),
    ('skip_specs: true\n"skip_spec\\u0073": false\n', False),
    ('skip_specs: true\n? skip_specs\n: false\n', False),
])
def test_completed_packet_respects_only_explicit_unambiguous_spec_exemption(tmp_path, setting, exempt):
    change = write_change(tmp_path, 'refactor', status='completed', tasks=['- [x] refactor'])
    metadata = change / '.openspec.yaml'
    metadata.write_text(metadata.read_text() + setting)
    (change / 'automation.json').write_text(json.dumps({
        'commands': ['openspec validate refactor --strict']}))
    summary = summarize_openspec_backlog(tmp_path / 'openspec')
    invalid = [row for row in summary['findings'] if row['kind'] == 'invalid_completed_packet']
    assert bool(invalid) is not exempt
    assert summary['packets'][0]['has_delta_spec'] is False
