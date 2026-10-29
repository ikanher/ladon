"""Explicit ordered-edge native chain commands."""

from ladon.proof_contract_io import load_bounded_plans
from ladon.real_bound_native_chain_bundle import (
    inspect_chain_bundle,
    produce_chain_bundle,
    replay_chain_bundle,
)

OPERATIONS = ('propagate-real-bounds-proofir', 'inspect-real-chain', 'replay-real-chain')


def chain_command(args):
    if args.operation == 'propagate-real-bounds-proofir':
        productions = load_bounded_plans(args.production, max_bytes=32 * 1024**2)
        return produce_chain_bundle(productions, args.rule, args.root, timeout_seconds=args.timeout_seconds)
    bundle, = load_bounded_plans([args.input], max_bytes=32 * 1024**2)
    if args.operation == 'replay-real-chain':
        return replay_chain_bundle(bundle, args.root, timeout_seconds=args.timeout_seconds)
    return inspect_chain_bundle(bundle, args.root)
