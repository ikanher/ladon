"""Bounded public continuation demo; performs work without ending its audit clock."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path

from ladon.entrypoint import main


def run(output: Path):
    output.mkdir(parents=True, exist_ok=False)
    source = output / 'source.txt'
    source.write_text('An assertion still needing an interpretation.\nA second unexamined assertion.\n')
    plan, checkpoint, terminal = (output / name for name in ('plan.json', 'checkpoint.json', 'terminal.json'))
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        original, refused = _initialize_checkpoint(source, output, plan, checkpoint, terminal, log)
        next_work = next(row for row in refused['next'] if row['kind'] == 'inventory-source')
        quote = '\n'.join(source.read_text().splitlines()[next_work['startLine']-1:next_work['endLine']])
        record = {'id': 'continued-source-review', 'source': {'path': source.name,
                  'startLine': next_work['startLine'], 'endLine': next_work['endLine'],
                  'quote': quote, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()},
                  'formula': {'tag': 'opaque', 'text': quote,
                              'reason': 'Demo records an unresolved source interpretation.'}, 'symbols': {}}
        record_path, bundle, continued = (output / name for name in ('record.json', 'bundle.json', 'continued.json'))
        record_path.write_text(json.dumps(record))
        assert main(['investigation', 'interpret', '--record', str(record_path), '--root', str(output),
                     '--output', str(bundle)]) == 0
        assert main(['investigation', 'attach', '--plan', str(plan), '--bundle', str(bundle),
                     '--root', str(output), '--output', str(continued)]) == 0
        assert main(['investigation', 'finalize', '--plan', str(continued), '--root', str(output),
                     '--output', str(terminal)]) == 2
        initial, _later = _assert_clock(plan, original, continued, terminal)
    (output / 'CLI.log').write_text(log.getvalue())
    summary = {'status': 'continue', 'actionPerformed': 'source-bound opaque interpretation attached',
               'startedAt': initial['startedAt'], 'budgetSeconds': initial['budgetSeconds'],
               'terminalReceiptCreated': False,
               'nonclaim': 'Demonstrates workflow only; no mathematical comparison or Lean proof was performed.'}
    (output / 'RESULT.json').write_text(json.dumps(summary, indent=2)+'\n')
    return summary


def _initialize_checkpoint(source, output, plan, checkpoint, terminal, log):
    assert main(['investigation', 'init', '--text', str(source), '--root', str(output),
                 '--output', str(plan), '--correspondence', '--unit-lines', '1']) == 0
    original = plan.read_bytes()
    assert main(['investigation', 'checkpoint', '--plan', str(plan), '--root', str(output),
                 '--output', str(checkpoint)]) == 0
    assert main(['investigation', 'finalize', '--plan', str(plan), '--root', str(output),
                 '--output', str(terminal)]) == 2
    refused = json.loads(log.getvalue().splitlines()[-1])
    return original, refused


def _assert_clock(plan, original, continued, terminal):
    assert not terminal.exists() and plan.read_bytes() == original
    initial, later = json.loads(original), json.loads(continued.read_text())
    assert initial['startedAt'] == later['startedAt']
    assert initial['budgetSeconds'] == later['budgetSeconds']
    return initial, later


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(run(parser.parse_args().output.resolve())))
