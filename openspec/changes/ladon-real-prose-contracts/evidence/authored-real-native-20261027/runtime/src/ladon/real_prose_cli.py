"""Public typed-prose observation commands, independent of admitted profiles."""

from pathlib import Path

from ladon.proof_contract_io import load_bounded_plans
from ladon.real_prose_inputs import MAX_BYTES, SCHEMA
from ladon.real_prose_native_cli import OPERATIONS as NATIVE_OPERATIONS
from ladon.real_prose_observation import (
    inspect_prose_observation,
    observe_prose_bound,
    replay_prose_observation,
)
from ladon.resource_limits import DEFAULT_MAX_RSS_MIB

OBSERVATION_OPERATIONS = ('observe-prose-bound', 'replay-prose-bound', 'recognize-prose-bound')
OPERATIONS = (*OBSERVATION_OPERATIONS, *NATIVE_OPERATIONS)


def add_parsers(sub):
    from ladon.real_prose_native_cli import add_parsers as add_native_parsers

    add_native_parsers(sub)
    for name in OBSERVATION_OPERATIONS:
        parser = sub.add_parser(name, help='Observe an authored proposition with no proof authority')
        parser.add_argument('--root', type=Path, required=True)
        if name != 'replay-prose-bound':
            parser.add_argument('--interpretation', type=Path, required=True)
            parser.add_argument('--context', type=Path, required=True)
        else:
            parser.add_argument('--input', type=Path, required=True)
        parser.add_argument('--timeout-seconds', type=float, default=600)
        parser.add_argument('--max-rss-mib', type=int, default=DEFAULT_MAX_RSS_MIB)
        parser.add_argument('--output', type=Path)


def command(args):
    if args.operation in NATIVE_OPERATIONS:
        from ladon.real_prose_native_cli import command as native_command

        return native_command(args)
    limits = {'timeout_seconds': args.timeout_seconds, 'max_rss_bytes': args.max_rss_mib * 1024**2}
    if args.operation == 'replay-prose-bound':
        snapshot, = load_bounded_plans([args.input], max_bytes=MAX_BYTES)
        return replay_prose_observation(snapshot, args.root, **limits)
    reading, context = load_bounded_plans([args.interpretation, args.context], max_bytes=MAX_BYTES)
    if args.operation == 'recognize-prose-bound':
        from ladon.real_prose_recognition import recognize_prose_bound

        return recognize_prose_bound(args.root, reading, context, **limits)
    return observe_prose_bound(args.root, reading, context, **limits)


def inspect_snapshot(snapshot, context, root):
    if snapshot.get('schema') == 'ladon-real-prose-production-v1':
        from ladon.real_prose_native_production import inspect_real_prose_bound

        if context is not None:
            raise ValueError('authored Real inspection does not accept alternate context')
        return inspect_real_prose_bound(snapshot, root)
    if snapshot.get('schema') == 'ladon-real-prose-recognition-v1':
        from ladon.real_prose_recognition import inspect_recognition

        if context is not None:
            raise ValueError('recognition inspection does not accept alternate context')
        return inspect_recognition(snapshot, root)
    if snapshot.get('schema') != SCHEMA:
        return None
    if context is not None:
        raise ValueError('prose observation inspection does not accept an alternate --context')
    return inspect_prose_observation(snapshot, root)


def exit_status(result):
    if result.get('schema') == 'ladon-real-prose-production-v1':
        return 0 if result['status'] == 'authored' else 2
    if result.get('schema') == 'ladon-real-prose-recognition-v1':
        return 0 if result['status'] == 'recognized' else 2
    if result.get('schema') == SCHEMA:
        return 0 if result['status'] == 'observed' else 2
    return None
