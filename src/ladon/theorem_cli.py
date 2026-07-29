"""Ordinary installed CLI operations for theorem capsules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from ladon.cli_execution import EXIT_INVOCATION, EXIT_OPERATIONAL, EXIT_SUCCESS
from ladon.theorem_capsule_models import (
    CapsuleContentError,
    CapsuleInvocationError,
    CapsuleOperationalError,
    TheoremPlan,
)
from ladon.theorem_capsule_planning import plan_theorem_capsule


def build_theorem_parser() -> argparse.ArgumentParser:
    """Build the public theorem-capsule command tree."""

    parser = argparse.ArgumentParser(
        prog="ladon theorem",
        description="Plan, materialize, and independently replay Lean theorem capsules.",
    )
    commands = parser.add_subparsers(dest="theorem_command", required=True)
    plan = commands.add_parser(
        "plan",
        help="Resolve a theorem exactly and write a complete extraction plan.",
    )
    plan.add_argument("theorem", help="Fully qualified Lean theorem name.")
    _add_repository_options(plan)
    _add_result_options(plan, default_output="-")
    _add_timeout(plan)

    materialize = commands.add_parser(
        "materialize",
        help="Materialize a validated plan outside its target repository.",
    )
    materialize.add_argument("--plan", required=True, help="Canonical plan JSON.")
    materialize.add_argument("--output", required=True, help="Capsule directory or archive.")
    materialize.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Command-result representation written to stdout.",
    )

    replay = commands.add_parser(
        "replay",
        help="Verify a capsule with Lean in a fresh replay directory.",
    )
    replay.add_argument("capsule", help="Capsule directory or supported archive.")
    _add_result_options(replay, default_output="-")
    _add_timeout(replay)
    replay.add_argument(
        "--network",
        choices=("deny", "allow"),
        default="deny",
        help="Whether replay may acquire locked external packages.",
    )

    extract = commands.add_parser(
        "extract",
        help="Plan and materialize one theorem, optionally verifying it.",
    )
    extract.add_argument("theorem", help="Fully qualified Lean theorem name.")
    _add_repository_options(extract)
    extract.add_argument("--output", required=True, help="Capsule directory or archive.")
    extract.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Command-result representation written to stdout.",
    )
    extract.add_argument(
        "--verify",
        action="store_true",
        help="Replay the completed capsule before reporting success.",
    )
    extract.add_argument(
        "--network",
        choices=("deny", "allow"),
        default="deny",
        help="Whether verification may acquire locked external packages.",
    )
    _add_timeout(extract)
    return parser


def _add_repository_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Lean repository containing the theorem.",
    )


def _add_result_options(
    parser: argparse.ArgumentParser,
    *,
    default_output: str,
) -> None:
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="json",
        help="Result representation.",
    )
    parser.add_argument(
        "--output",
        default=default_output,
        help="Result path, or - for standard output.",
    )


def _add_timeout(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--timeout",
        type=_positive_timeout,
        default=120.0,
        help="Finite deadline for each target Lean/Lake process.",
    )
    parser.add_argument(
        "--max-rss-mib",
        type=_positive_integer,
        help="Optional supported process-tree resident-memory limit in MiB.",
    )


def theorem_main(argv: Sequence[str]) -> int:
    """Run one theorem-capsule operation with stable exit classifications."""

    parser = build_theorem_parser()
    try:
        args = parser.parse_args(list(argv))
        return _dispatch(args)
    except CapsuleInvocationError as exc:
        print(f"ladon theorem: invalid invocation: {exc}", file=sys.stderr)
        return EXIT_INVOCATION
    except (CapsuleContentError, CapsuleOperationalError) as exc:
        print(f"ladon theorem: operational failure: {exc}", file=sys.stderr)
        return EXIT_OPERATIONAL
    except OSError as exc:
        print(f"ladon theorem: filesystem failure: {exc}", file=sys.stderr)
        return EXIT_OPERATIONAL


def _dispatch(args: argparse.Namespace) -> int:
    if args.theorem_command == "plan":
        _validate_plan_output(Path(args.repo_root), args.output)
        plan = plan_theorem_capsule(
            Path(args.repo_root),
            args.theorem,
            timeout_seconds=args.timeout,
            max_rss_bytes=_max_rss_bytes(args),
        )
        _write_result(
            plan.to_payload(),
            args.output,
            args.format,
            text=_render_plan(plan),
        )
        return EXIT_SUCCESS
    if args.theorem_command == "materialize":
        return _materialize_command(args)
    if args.theorem_command == "replay":
        return _replay_command(args)
    if args.theorem_command == "extract":
        return _extract_command(args)
    raise CapsuleInvocationError(
        f"unsupported theorem operation {args.theorem_command!r}"
    )


def _validate_plan_output(repo_root: Path, output: str) -> None:
    """Keep the planning command read-only with respect to its target."""

    if output == "-":
        return
    root = repo_root.resolve()
    destination = Path(output).absolute().resolve(strict=False)
    if destination == root or destination.is_relative_to(root):
        raise CapsuleInvocationError(
            "theorem plan output must be outside the target repository"
        )


def _materialize_command(args: argparse.Namespace) -> int:
    from ladon.theorem_capsule_materialization import materialize_theorem_capsule

    manifest = materialize_theorem_capsule(
        TheoremPlan.load(Path(args.plan)),
        Path(args.output),
    )
    _write_command_result(
        {
            "operation": "materialize",
            "status": manifest.payload["status"],
            "capsuleIdentity": manifest.identity,
            "output": str(Path(args.output)),
        },
        args.format,
    )
    return EXIT_SUCCESS


def _replay_command(args: argparse.Namespace) -> int:
    from ladon.theorem_capsule_replay import replay_theorem_capsule

    receipt = replay_theorem_capsule(
        Path(args.capsule),
        timeout_seconds=args.timeout,
        max_rss_bytes=_max_rss_bytes(args),
        network=args.network,
    )
    _write_result(
        receipt,
        args.output,
        args.format,
        text=_render_receipt(receipt),
    )
    return EXIT_SUCCESS if receipt.get("status") == "verified" else EXIT_OPERATIONAL


def _extract_command(args: argparse.Namespace) -> int:
    from ladon.theorem_capsule_materialization import materialize_theorem_capsule

    plan = plan_theorem_capsule(
        Path(args.repo_root),
        args.theorem,
        timeout_seconds=args.timeout,
        max_rss_bytes=_max_rss_bytes(args),
    )
    manifest = materialize_theorem_capsule(plan, Path(args.output))
    result: dict[str, Any] = {
        "operation": "extract",
        "status": manifest.payload["status"],
        "planIdentity": plan.identity,
        "capsuleIdentity": manifest.identity,
        "output": str(Path(args.output)),
    }
    if args.verify:
        from ladon.theorem_capsule_replay import replay_theorem_capsule

        receipt = replay_theorem_capsule(
            Path(args.output),
            timeout_seconds=args.timeout,
            max_rss_bytes=_max_rss_bytes(args),
            network=args.network,
        )
        result["status"] = receipt["status"]
        result["receiptIdentity"] = receipt["receiptIdentity"]
    _write_command_result(result, args.format)
    return EXIT_SUCCESS if result["status"] in {"materialized_unverified", "verified"} else EXIT_OPERATIONAL


def _write_command_result(payload: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        sys.stdout.write(_json_text(payload))
        return
    lines = [
        f"Theorem capsule {payload.get('operation')}: {payload.get('status')}",
    ]
    for key in ("planIdentity", "capsuleIdentity", "receiptIdentity", "output"):
        if payload.get(key):
            lines.append(f"{key}: {payload[key]}")
    sys.stdout.write("\n".join(lines) + "\n")


def _write_result(
    payload: Mapping[str, Any],
    output: str,
    output_format: str,
    *,
    text: str,
) -> None:
    content = _json_text(payload) if output_format == "json" else text
    if output == "-":
        sys.stdout.write(content)
        return
    path = Path(output)
    if path.exists() and not path.is_file():
        raise CapsuleInvocationError(f"output is not a regular file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _json_text(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _render_plan(plan: TheoremPlan) -> str:
    target = plan.target
    semantic = plan.payload["semanticGraph"]
    build = plan.payload["buildGraph"]
    return "\n".join(
        (
            f"Theorem capsule plan: {target['name']}",
            f"Plan identity: {plan.identity}",
            f"Owner: {target['module']} ({target['path']})",
            f"Semantic nodes: {semantic['nodeCount']}",
            f"Build modules: {len(build['modules'])}",
            f"Eligible: {'yes' if plan.eligible else 'no'}",
            f"Guarantee: {plan.payload['guaranteeLevel']}",
            "",
        )
    )


def _render_receipt(receipt: Mapping[str, Any]) -> str:
    return "\n".join(
        (
            f"Theorem capsule replay: {receipt.get('status')}",
            f"Receipt identity: {receipt.get('receiptIdentity', '')}",
            f"Capsule identity: {receipt.get('capsuleIdentity', '')}",
            "",
        )
    )


def _positive_timeout(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be numeric") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("timeout must be positive")
    return parsed


def _positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _max_rss_bytes(args: argparse.Namespace) -> int | None:
    value = getattr(args, "max_rss_mib", None)
    return value * 1024 * 1024 if value is not None else None


__all__ = ["build_theorem_parser", "theorem_main"]
