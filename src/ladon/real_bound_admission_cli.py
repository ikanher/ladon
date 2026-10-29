"""Public source-bound prefix planning and fresh law checking."""

from pathlib import Path

from ladon.proof_contract_io import load_bounded_plans
from ladon.real_bound_admission import plan_prefix_admission
from ladon.real_bound_admission_check import check_prefix_admission, verify_plan_source


def add_prefix_admission_parsers(sub):
    for name in ("plan-prefix-admission", "check-prefix-laws"):
        parser = sub.add_parser(name, help="Plan or freshly check generic prefix laws; no contract admission")
        parser.add_argument("--input", type=Path, required=True)
        parser.add_argument("--root", type=Path, required=True)
        parser.add_argument("--output", type=Path)
        if name == "check-prefix-laws":
            parser.add_argument("--terms", type=Path, required=True)
            parser.add_argument("--timeout-seconds", type=float, default=900)


def prefix_admission_command(args):
    if args.operation == "plan-prefix-admission":
        request, = load_bounded_plans([args.input], max_bytes=1024**2)
        result = plan_prefix_admission(request)
        verify_plan_source(args.root, result)
        return result
    plan, terms = load_bounded_plans([args.input, args.terms], max_bytes=1024**2)
    result = check_prefix_admission(args.root, plan, terms, timeout_seconds=args.timeout_seconds)
    checked = result.get("result") or {}
    return {"schema": "ladon-prefix-law-run-v1", "admission": "unresolved", "contract": None,
            "status": "checked-laws" if checked.get("status") == "checked-laws" else "unresolved",
            "supervision": result}


def prefix_admission_exit_status(result):
    if result.get("schema") == "ladon-prefix-law-run-v1":
        return 0 if result.get("status") == "checked-laws" else 2
    if result.get("schema") == "ladon-prefix-admission-plan-v1":
        return 2
    return None
