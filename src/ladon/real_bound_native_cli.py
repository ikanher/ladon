"""Public native Real planning, fresh production, inspection, reporting and replay."""

from pathlib import Path

from ladon.proof_contract_io import load_bounded_plans
from ladon.real_bound_binding_check import verify_binding_source
from ladon.real_bound_native_chain_cli import OPERATIONS as CHAIN_OPERATIONS
from ladon.real_bound_native_chain_cli import chain_command
from ladon.real_bound_native_coefficient_cli import OPERATIONS as COEFFICIENT_OPERATIONS
from ladon.real_bound_native_coefficient_cli import coefficient_command
from ladon.real_bound_native_plan import plan_real_bound
from ladon.real_bound_native_production import (
    inspect_real_bound,
    produce_real_bound,
    replay_real_bound,
)
from ladon.real_bound_native_transfer_cli import OPERATIONS as TRANSFER_OPERATIONS
from ladon.real_bound_native_transfer_cli import transfer_command

OPERATIONS = (
    "plan-real-bound", "admit-real-bound", "inspect-real-bound", "report-real-bound",
    "replay-real-bound", "compare-real-bounds", "propagate-real-bound-identity",
    "compare-real-bounds-proofir", "inspect-real-comparison", "replay-real-comparison",
    "check-real-bound-prefix", "check-real-bound-prefix-proofir", "inspect-real-prefix", "replay-real-prefix",
    *COEFFICIENT_OPERATIONS,
    *TRANSFER_OPERATIONS,
    *CHAIN_OPERATIONS,
)


def add_real_bound_parsers(sub):
    for name in OPERATIONS:
        parser = sub.add_parser(name, help="Source-bound Real contracts; saved evidence remains historical")
        if name in {"compare-real-bounds", "compare-real-bounds-proofir", "compose-real-bounds", "compose-real-bounds-proofir"}:
            parser.add_argument("--left", type=Path, required=True)
            parser.add_argument("--right", type=Path, required=True)
        elif name in {"check-real-bound-prefix", "check-real-bound-prefix-proofir"}:
            parser.add_argument("--stronger", type=Path, required=True)
            parser.add_argument("--weaker", type=Path, required=True)
        elif name in {"propagate-real-bound-identity", "propagate-real-bounds-proofir"}:
            parser.add_argument("--production", type=Path, action="append", required=True)
        else:
            parser.add_argument("--input", type=Path, required=True)
        if name == "propagate-real-bounds-proofir":
            parser.add_argument("--rule", action="append", required=True,
                                choices=("identity-v1", "order-prefix-v1"))
        parser.add_argument("--root", type=Path, required=name not in {"inspect-real-bound", "report-real-bound", "inspect-real-comparison", "inspect-real-prefix", "inspect-real-chain", "inspect-real-coefficient", "inspect-real-transfer"})
        parser.add_argument("--output", type=Path)
        if name == "admit-real-bound":
            parser.add_argument("--proofs", type=Path, required=True)
        if name in {"admit-real-bound", "replay-real-bound", "compare-real-bounds",
                    "propagate-real-bound-identity", "compare-real-bounds-proofir",
                    "replay-real-comparison", "check-real-bound-prefix", "check-real-bound-prefix-proofir",
                    "replay-real-prefix", "propagate-real-bounds-proofir", "replay-real-chain",
                    "check-real-bound-coefficient", "check-real-bound-coefficient-proofir", "replay-real-coefficient",
                    "compose-real-bounds", "compose-real-bounds-proofir", "replay-real-transfer"}:
            parser.add_argument("--timeout-seconds", type=float, default=600)


def _pair_command(args):
    if args.operation in {"check-real-bound-prefix", "check-real-bound-prefix-proofir"}:
        from ladon.real_bound_native_prefix import check_prefix_implication
        from ladon.real_bound_native_prefix_bundle import produce_prefix_bundle

        stronger, weaker = load_bounded_plans([args.stronger, args.weaker], max_bytes=32 * 1024**2)
        operation = (produce_prefix_bundle if args.operation == "check-real-bound-prefix-proofir"
                     else check_prefix_implication)
        return operation(stronger, weaker, args.root, timeout_seconds=args.timeout_seconds)
    if args.operation in {"compare-real-bounds", "compare-real-bounds-proofir"}:
        left, right = load_bounded_plans([args.left, args.right], max_bytes=32 * 1024**2)
        from ladon.real_bound_native_analysis import compare_real_bounds

        if args.operation == "compare-real-bounds-proofir":
            from ladon.real_bound_native_analysis_bundle import produce_comparison_bundle

            return produce_comparison_bundle(left, right, args.root, timeout_seconds=args.timeout_seconds)
        return compare_real_bounds(left, right, args.root, timeout_seconds=args.timeout_seconds)
    raise ValueError("unsupported Real pair operation")


def real_bound_command(args):
    if args.operation in TRANSFER_OPERATIONS:
        return transfer_command(args)
    if args.operation in CHAIN_OPERATIONS:
        return chain_command(args)
    if args.operation in {"check-real-bound-prefix", "check-real-bound-prefix-proofir",
                          "compare-real-bounds", "compare-real-bounds-proofir"}:
        return _pair_command(args)
    if args.operation == "propagate-real-bound-identity":
        productions = load_bounded_plans(args.production, max_bytes=32 * 1024**2)
        from ladon.real_bound_native_analysis import propagate_real_bound_identity

        return propagate_real_bound_identity(productions, args.root,
                                             timeout_seconds=args.timeout_seconds)
    if args.operation == "admit-real-bound":
        plan, terms = load_bounded_plans([args.input, args.proofs], max_bytes=32 * 1024**2)
        return produce_real_bound(args.root, plan, terms, timeout_seconds=args.timeout_seconds)
    value, = load_bounded_plans([args.input], max_bytes=32 * 1024**2)
    return _single_command(args, value)


def _single_command(args, value):
    if args.operation in COEFFICIENT_OPERATIONS:
        return coefficient_command(args, value)
    if args.operation in {"inspect-real-prefix", "replay-real-prefix"}:
        from ladon.real_bound_native_prefix_bundle import (
            inspect_prefix_bundle,
            replay_prefix_bundle,
        )

        if args.operation == "replay-real-prefix":
            return replay_prefix_bundle(value, args.root, timeout_seconds=args.timeout_seconds)
        return inspect_prefix_bundle(value, args.root)
    if args.operation in {"inspect-real-comparison", "replay-real-comparison"}:
        from ladon.real_bound_native_analysis_bundle import (
            inspect_comparison_bundle,
            replay_comparison_bundle,
        )

        if args.operation == "replay-real-comparison":
            return replay_comparison_bundle(value, args.root, timeout_seconds=args.timeout_seconds)
        return inspect_comparison_bundle(value, args.root)
    if args.operation == "plan-real-bound":
        plan = plan_real_bound(value)
        verify_binding_source(args.root, value)
        return plan
    if args.operation == "replay-real-bound":
        return replay_real_bound(value, args.root, timeout_seconds=args.timeout_seconds)
    return inspect_real_bound(value, args.root)


def real_bound_exit_status(result):
    schema = result.get("schema")
    if schema in {"ladon-real-bound-analysis-v1", "ladon-real-bound-prefix-analysis-v1",
                  "ladon-real-bound-chain-analysis-v1", "ladon-real-bound-coefficient-analysis-v1",
                  "ladon-real-bound-transfer-analysis-v1"}:
        return 0 if result.get("status") == "resolved" else 2
    if schema == "ladon-real-bound-admission-plan-v1":
        return 2
    if schema == "ladon-real-bound-production-v1":
        return 0 if result.get("status") == "admitted" else 2
    if schema in {"ladon-real-bound-inspection-v1", "ladon-real-bound-comparison-bundle-v1",
                  "ladon-real-bound-coefficient-bundle-v1", "ladon-real-bound-coefficient-inspection-v1",
                  "ladon-real-bound-transfer-bundle-v1", "ladon-real-bound-transfer-inspection-v1",
                  "ladon-real-bound-prefix-bundle-v1", "ladon-real-bound-prefix-inspection-v1",
                  "ladon-real-bound-chain-bundle-v1", "ladon-real-bound-chain-inspection-v1",
                  "ladon-real-bound-comparison-inspection-v1"}:
        return 0
    return None
