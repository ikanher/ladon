"""Long lexical builds expose bounded operational stage events."""
from __future__ import annotations

import json

from ladon.proof_search_cli import proof_search_main


def test_build_progress_reports_internal_stages_and_keeps_stdout_clean(tmp_path, capsys):
    (tmp_path/'Owner.lean').write_text('theorem exampleTrue : True := True.intro\n')
    code = proof_search_main(['index', 'build', '--repo-root', str(tmp_path),
                              '--format', 'json', '--progress'])
    assert code == 0
    streams = capsys.readouterr()
    assert json.loads(streams.out)['status'] == 'complete'
    events = [json.loads(line) for line in streams.err.splitlines()]
    assert [row['phase'] for row in events] == [
        'dispatch', 'discovery', 'extraction', 'validation', 'publication', 'dispatch',
    ]
    assert events[2]['processedModules'] == events[2]['totalModules'] == 1
    assert all(len(json.dumps(row)) < 2048 for row in events)


def test_quiet_build_does_not_emit_stage_events(tmp_path, capsys):
    (tmp_path/'Owner.lean').write_text('theorem exampleTrue : True := True.intro\n')
    assert proof_search_main(['index', 'build', '--repo-root', str(tmp_path)]) == 0
    assert capsys.readouterr().err == ''
