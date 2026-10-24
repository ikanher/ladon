"""Public native source-context planning and checkpointed term checking."""
from pathlib import Path

from .proof_contract_io import load_bounded_plans


def add_context_bridge_parsers(subparsers):
    for command in ('context-obligations', 'check-context-bridge'):
        parser = subparsers.add_parser(command, help='Regenerate exact original-context obligations')
        parser.add_argument('--input', type=Path, required=True)
        parser.add_argument('--output', type=Path)
        if command == 'check-context-bridge':
            parser.add_argument('--plan-id', required=True)
            parser.add_argument('--terms', type=Path, required=True)


def context_bridge(args):
    from .proof_contract_context_bridge import check_context_bridge, plan_context_bridge

    # The request owns its absolute clock. Reading files never refreshes it.
    paths = [args.input] + ([args.terms] if args.operation == 'check-context-bridge' else [])
    values = load_bounded_plans(paths, max_bytes=8 * 1024**2)
    request = values[0]
    return (plan_context_bridge(request) if len(values) == 1 else
            check_context_bridge(request, args.plan_id, values[1]))
