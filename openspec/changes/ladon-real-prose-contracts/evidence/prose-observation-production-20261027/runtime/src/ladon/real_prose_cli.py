"""Public typed-prose observation commands, independent of admitted profiles."""

from pathlib import Path

from ladon.proof_contract_io import load_bounded_plans
from ladon.real_prose_inputs import MAX_BYTES, SCHEMA
from ladon.real_prose_observation import (
    inspect_prose_observation,
    observe_prose_bound,
    replay_prose_observation,
)
from ladon.resource_limits import DEFAULT_MAX_RSS_MIB

OPERATIONS = ('observe-prose-bound', 'replay-prose-bound')


def add_parsers(sub):
    for name in OPERATIONS:
        parser = sub.add_parser(name, help='Observe an authored proposition with no proof authority')
        parser.add_argument('--root', type=Path, required=True)
        if name == 'observe-prose-bound':
            parser.add_argument('--interpretation', type=Path, required=True)
            parser.add_argument('--context', type=Path, required=True)
        else:
            parser.add_argument('--input', type=Path, required=True)
        parser.add_argument('--timeout-seconds', type=float, default=600)
        parser.add_argument('--max-rss-mib', type=int, default=DEFAULT_MAX_RSS_MIB)
        parser.add_argument('--output', type=Path)


def command(args):
    limits = {'timeout_seconds': args.timeout_seconds, 'max_rss_bytes': args.max_rss_mib * 1024**2}
    if args.operation == 'replay-prose-bound':
        snapshot, = load_bounded_plans([args.input], max_bytes=MAX_BYTES)
        return replay_prose_observation(snapshot, args.root, **limits)
    reading, context = load_bounded_plans([args.interpretation, args.context], max_bytes=MAX_BYTES)
    return observe_prose_bound(args.root, reading, context, **limits)


def inspect_snapshot(snapshot, context, root):
    if snapshot.get('schema') != SCHEMA:
        return None
    if context is not None:
        raise ValueError('prose observation inspection does not accept an alternate --context')
    return inspect_prose_observation(snapshot, root)


def exit_status(result):
    if result.get('schema') == SCHEMA:
        return 0 if result['status'] == 'observed' else 2
    return None
