"""Public planning and fresh checking of observed predicate applications."""

from pathlib import Path

from ladon.derivative_prefix import plan_derivative_prefix
from ladon.proof_contract_io import load_bounded_plans
from ladon.proof_contract_payloads import closed
from ladon.real_bound_binding import plan_bound_prefix
from ladon.real_bound_binding_check import check_bound_prefix, verify_binding_source


def add_bound_prefix_parsers(sub):
    for name in ("plan-bound-prefix", "check-bound-prefix", "plan-derivative-prefix", "check-derivative-prefix"):
        parser = sub.add_parser(name, help="Bind prefix laws to the exact observed predicate; no contract activation")
        parser.add_argument("--input", type=Path, required=True)
        parser.add_argument("--root", type=Path, required=True)
        parser.add_argument("--output", type=Path)
        if name == "plan-bound-prefix":
            parser.add_argument("--measure", type=Path, required=True)
        elif name != "plan-derivative-prefix":
            parser.add_argument("--proof", type=Path, required=True)
            parser.add_argument("--timeout-seconds", type=float, default=900)


def bound_prefix_command(args):
    if args.operation == "plan-derivative-prefix":
        observation, = load_bounded_plans([args.input], max_bytes=8 * 1024**2)
        plan = plan_derivative_prefix(observation)
        verify_binding_source(args.root, plan)
        return plan
    if args.operation == "plan-bound-prefix":
        observation, measure = load_bounded_plans([args.input, args.measure], max_bytes=8 * 1024**2)
        plan = plan_bound_prefix(observation, measure)
        verify_binding_source(args.root, plan)
        return plan
    plan, proof = load_bounded_plans([args.input, args.proof], max_bytes=8 * 1024**2)
    expected = ("ladon-derivative-prefix-plan-v1" if args.operation == "check-derivative-prefix"
                else "ladon-bound-prefix-plan-v1")
    if plan.get("schema") != expected:
        raise ValueError("check command requires its exact bound-prefix plan schema")
    closed(proof, {"term"}, "bound proof")
    result = check_bound_prefix(args.root, plan, proof["term"], timeout_seconds=args.timeout_seconds)
    checked = result.get("result") or {}
    run = {"schema": "ladon-bound-prefix-run-v1", "admission": "unresolved", "contract": None,
           "status": "checked-binding" if checked.get("status") == "checked-binding" else "unresolved",
           "supervision": result}
    if args.operation == "check-derivative-prefix":
        run.update(schema="ladon-derivative-prefix-run-v1", paperNormBridge="unresolved",
                   derivativeAdmission=checked.get("derivativeAdmission", "unresolved"))
    return run


def bound_prefix_exit_status(result):
    if result.get("schema") in {"ladon-bound-prefix-run-v1", "ladon-derivative-prefix-run-v1"}:
        return 0 if result.get("status") == "checked-binding" else 2
    if result.get("schema") in {"ladon-bound-prefix-plan-v1", "ladon-derivative-prefix-plan-v1"}:
        return 2
    return None
