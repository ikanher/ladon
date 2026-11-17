"""Exposed root qualification; public CLI and bounded real Lean, no discovery score."""

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from time import monotonic

from ladon.process_supervisor import run_bounded_target_process

BASE = Path(__file__).resolve().parent
PROJECT = BASE / 'project'
REPO = Path.cwd()
STARTED = monotonic()
CLI = [sys.executable, '-c', 'import sys; from ladon.entrypoint import main; sys.exit(main(sys.argv[1:]))']


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def execute(name, command, cwd=REPO):
    remaining = 900 - (monotonic() - STARTED)
    if remaining <= 0:
        raise RuntimeError('whole-exercise 900-second bound exhausted')
    print(name, flush=True)
    receipt = run_bounded_target_process(command, cwd=cwd, timeout_seconds=min(300, remaining),
                                         max_output_bytes=8 * 1024**2,
                                         max_rss_bytes=12 * 1024**3)
    write(BASE / (name + '.process.json'), asdict(receipt))
    if not receipt.succeeded:
        raise RuntimeError(name + ' failed; retained process receipt')


def invoke(name, *args):
    execute(name, [*CLI, *map(str, args)])


def bind_record(identity, line, formula, symbols):
    raw = (PROJECT / 'source.txt').read_bytes()
    return {'id': identity, 'source': {'path': 'source.txt', 'startLine': line, 'endLine': line,
            'quote': raw.decode().splitlines()[line-1], 'sha256': hashlib.sha256(raw).hexdigest()},
            'formula': formula, 'symbols': symbols}


def prepare_case(name, record, object_map, slice_name, terms):
    directory = BASE / name
    directory.mkdir(exist_ok=False)
    for file, value in [('interpretation.json', record), ('map.json', object_map), ('terms.json', terms)]:
        write(directory / file, value)
    invoke(name + '-interpret', 'investigation', 'interpret', '--record', directory / 'interpretation.json',
           '--root', PROJECT, '--slice', BASE / slice_name, '--output', directory / 'interpreted.json')
    invoke(name + '-align', 'investigation', 'align', '--interpretation', directory / 'interpreted.json',
           '--slice', BASE / slice_name, '--map', directory / 'map.json', '--root', PROJECT,
           '--output', directory / 'aligned.json')
    return directory


def check_case(name, directory):
    invoke(name + '-check', 'investigation', 'check', '--plan', directory / 'aligned.json',
           '--terms', directory / 'terms.json', '--repo', PROJECT, '--root', PROJECT,
           '--output', directory / 'checked.json')
    invoke(name + '-inspect', 'investigation', 'inspect', '--plan', directory / 'checked.json',
           '--context-max-bytes', 8388608, '--output', directory / 'inspection.json')


def main():
    first = {
        'exposure': 'Root authored from existing representation/quantifier controls; not source-blind.',
        'faithful': 'Fin.val maps the same Fin 5 index to its natural value; derive the bound from i.isLt.',
        'wrong-map': 'The source remains true; mapping to i.val+5 refutes this premise-supply route only.',
        'uniform': 'The pointwise theorem does not imply one common bound. The source reading is false.',
        'bounds': {'wholeSeconds': 900, 'perCommandSeconds': 300, 'rssBytes': 12 * 1024**3,
                   'outputBytes': 8 * 1024**2},
    }
    write(BASE / 'FIRST-INTERPRETATION.json', first)
    execute('source-control', ['elan', 'run', (PROJECT / 'lean-toolchain').read_text().strip(),
                             'lean', 'Context.lean'], PROJECT)
    for label, decl, application in [('representation', 'selected', 'bridge'),
                                      ('quantifier', 'selectedPointwise', 'pointwise')]:
        invoke(label + '-slice', 'proof-search', 'proof', 'slice', '--repo', PROJECT,
               '--source', 'Context.lean', '--module', 'Context', '--declaration', 'ContextFixture.'+decl,
               '--application', 'ContextFixture.'+application, '--output', BASE / (label + '-slice.json'))
    symbols = {'val': {'leanName': 'Fin.val', 'leanType': 'Fin 5 → Nat'},
               'shifted': {'leanName': 'ContextFixture.shifted', 'leanType': 'Fin 5 → Nat'}}
    formula = {'tag': 'forall', 'binder': {'id': 'i', 'name': 'index', 'domain': 'Fin 5'},
               'body': {'tag': 'lt', 'left': {'tag': 'app', 'symbol': 'val',
                        'args': [{'tag': 'var', 'id': 'i'}]}, 'right': {'tag': 'const', 'name': '5'}}}
    record = bind_record('fin-bound', 1, formula, symbols)
    terms = [{'obligation': name, 'mode': 'prove', 'term': term} for name, term in [
        ('interpretation', 'by intro h; exact h'), ('object-map', 'by intro i; trivial'),
        ('premise-1', 'by intro i; dsimp; intro h; exact i.isLt'),
        ('conclusion', 'by intro i; dsimp; intro h formal; exact formal')]]
    faithful = prepare_case('faithful', record, {'n': {'symbol': 'val', 'args': ['i']}},
                            'representation-slice.json', terms)
    wrong = prepare_case('wrong-map', record, {'n': {'symbol': 'shifted', 'args': ['i']}},
                         'representation-slice.json', [{'obligation': 'premise-1', 'mode': 'refute',
                         'term': 'by intro h; have bad := h ⟨0, by decide⟩ trivial; change 5 < 5 at bad; exact Nat.lt_irrefl 5 bad'}])
    body = {'tag': 'lt', 'left': {'tag': 'var', 'id': 'n'}, 'right': {'tag': 'var', 'id': 'k'}}
    for tag, identity in [('forall', 'n'), ('exists', 'k'), ('forall', 'd')]:
        body = {'tag': tag, 'binder': {'id': identity, 'name': identity, 'domain': 'Nat'}, 'body': body}
    uniform = prepare_case('uniform', bind_record('uniform-bound', 2, body, {}), {'d': 'd'},
                           'quantifier-slice.json', [{'obligation': 'conclusion', 'mode': 'refute',
                           'term': 'by intro h; have u := h 0 trivial (ContextFixture.pointwise 0); obtain ⟨k, hk⟩ := u; exact Nat.lt_irrefl k (hk k)'}])
    for name, directory in [('faithful', faithful), ('wrong-map', wrong), ('uniform', uniform)]:
        check_case(name, directory)
    write(BASE / 'EXECUTION.json', {'elapsedSeconds': monotonic()-STARTED, 'status': 'commands-completed'})


if __name__ == '__main__':
    main()
