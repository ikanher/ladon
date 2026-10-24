"""Ordinary CLI for native route context planning and checkpoint checking."""
from pathlib import Path

from .proof_contract_io import load_bounded_plans


def add_route_context_parsers(subparsers):
    for command in ('route-context-obligations', 'check-route-context-bridge'):
        parser = subparsers.add_parser(command, help='Check original readings against one native route requirement')
        parser.add_argument('--input', type=Path, required=True)
        parser.add_argument('--output', type=Path)
        if command == 'check-route-context-bridge':
            parser.add_argument('--plan-id', required=True)
            parser.add_argument('--terms', type=Path, required=True)


def route_context_bridge(args):
    from .proof_contract_route_context import check_route_context_bridge, plan_route_context_bridge

    paths = [args.input] + ([args.terms] if args.operation == 'check-route-context-bridge' else [])
    values = load_bounded_plans(paths, max_bytes=8 * 1024**2)
    return (plan_route_context_bridge(values[0]) if len(values) == 1 else
            check_route_context_bridge(values[0], args.plan_id, values[1]))
