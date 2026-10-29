"""Public pointwise coefficient checks, native persistence and explicit replay."""

OPERATIONS = ('check-real-bound-coefficient', 'check-real-bound-coefficient-proofir',
              'inspect-real-coefficient', 'replay-real-coefficient')


def coefficient_command(args, value):
    from ladon.real_bound_native_coefficient import check_coefficient_implication
    from ladon.real_bound_native_coefficient_bundle import (
        inspect_coefficient_bundle,
        produce_coefficient_bundle,
        replay_coefficient_bundle,
    )

    if args.operation == 'inspect-real-coefficient':
        return inspect_coefficient_bundle(value, args.root)
    operation = {'check-real-bound-coefficient': check_coefficient_implication,
                 'check-real-bound-coefficient-proofir': produce_coefficient_bundle,
                 'replay-real-coefficient': replay_coefficient_bundle}[args.operation]
    return operation(value, args.root, timeout_seconds=args.timeout_seconds)
