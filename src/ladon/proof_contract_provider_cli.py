"""Ordinary CLI for explicitly requested original-provider observation."""
from pathlib import Path

from .proof_contract_io import load_bounded_plans


def add_provider_expansion_parser(subparsers):
    parser = subparsers.add_parser('expand-provider',
        help='Observe a native demand provider application without discharging its goal')
    for name in ('input', 'context', 'request', 'root'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--application', required=True)
    parser.add_argument('--occurrence', type=int, default=0)
    parser.add_argument('--timeout-seconds', type=float, default=60)
    parser.add_argument('--max-rss-mib', type=int, default=12*1024)
    parser.add_argument('--output', type=Path)


def expand_provider(args):
    import time

    from .proof_contract_provider_expansion import expand_obligation_provider

    deadline = time.monotonic()+args.timeout_seconds
    analysis, context, selected = load_bounded_plans([args.input, args.context, args.request],
                                                    max_bytes=8*1024**2)
    return expand_obligation_provider({'repoRoot': args.root, 'analysisArtifact': analysis,
        'context': context, 'providerSliceRequest': selected, 'application': args.application,
        'occurrence': args.occurrence, 'deadlineMonotonic': deadline,
        'limits': {'timeout_seconds': min(30,args.timeout_seconds),
                   'max_rss_bytes': args.max_rss_mib*1024**2, 'max_output_bytes': 8*1024**2}})
