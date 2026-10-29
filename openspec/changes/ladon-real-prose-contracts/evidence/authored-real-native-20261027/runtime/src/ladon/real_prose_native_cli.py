"""Explicit native Real authoring, history reporting and fresh replay commands."""

from pathlib import Path

from ladon.proof_contract_io import load_bounded_plans
from ladon.real_prose_inputs import MAX_BYTES
from ladon.resource_limits import DEFAULT_MAX_RSS_MIB

OPERATIONS = ('produce-real-prose-bound', 'replay-real-prose-bound', 'report-real-prose-bound')


def add_parsers(sub):
    for name in OPERATIONS:
        parser = sub.add_parser(name, help='Attribute a native Real reading without semantic admission')
        parser.add_argument('--root', type=Path, required=name != 'report-real-prose-bound')
        parser.add_argument('--output', type=Path)
        if name == 'produce-real-prose-bound':
            parser.add_argument('--interpretation', type=Path, required=True)
            parser.add_argument('--context', type=Path, required=True)
            parser.add_argument('--alternative-id', required=True)
            parser.add_argument('--author', default='caller')
        else:
            parser.add_argument('--input', type=Path, required=True)
        if name != 'report-real-prose-bound':
            parser.add_argument('--timeout-seconds', type=float, default=600)
            parser.add_argument('--max-rss-mib', type=int, default=DEFAULT_MAX_RSS_MIB)


def command(args):
    from ladon.real_prose_native_production import (
        inspect_real_prose_bound,
        produce_real_prose_bound,
        replay_real_prose_bound,
    )

    if args.operation == 'report-real-prose-bound':
        snapshot, = load_bounded_plans([args.input], max_bytes=MAX_BYTES)
        return inspect_real_prose_bound(snapshot, args.root)
    limits = {'timeout_seconds': args.timeout_seconds, 'max_rss_bytes': args.max_rss_mib * 1024**2}
    if args.operation == 'replay-real-prose-bound':
        snapshot, = load_bounded_plans([args.input], max_bytes=MAX_BYTES)
        return replay_real_prose_bound(snapshot, args.root, **limits)
    reading, context = load_bounded_plans([args.interpretation, args.context], max_bytes=MAX_BYTES)
    return produce_real_prose_bound(args.root, reading, context, alternative_id=args.alternative_id,
                                    author=args.author, **limits)
