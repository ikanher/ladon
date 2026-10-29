"""Source-bound conditional composition commands and native history routes."""

from ladon.proof_contract_io import load_bounded_plans

OPERATIONS = ('compose-real-bounds', 'compose-real-bounds-proofir',
              'inspect-real-transfer', 'replay-real-transfer')


def transfer_command(args):
    from ladon.real_bound_native_transfer import check_transfer_composition
    from ladon.real_bound_native_transfer_bundle import (
        inspect_transfer_bundle,
        produce_transfer_bundle,
        replay_transfer_bundle,
    )

    if args.operation in {'compose-real-bounds', 'compose-real-bounds-proofir'}:
        values = load_bounded_plans([args.left, args.right], max_bytes=32 * 1024**2)
        operation = produce_transfer_bundle if args.operation.endswith('-proofir') else check_transfer_composition
        return operation(*values, args.root, timeout_seconds=args.timeout_seconds)
    value, = load_bounded_plans([args.input], max_bytes=32 * 1024**2)
    if args.operation == 'inspect-real-transfer':
        return inspect_transfer_bundle(value, args.root)
    return replay_transfer_bundle(value, args.root, timeout_seconds=args.timeout_seconds)
