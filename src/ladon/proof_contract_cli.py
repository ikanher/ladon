"""Ordinary immutable contract production and source-bound inspection commands."""

import argparse
import json
import sys
from pathlib import Path

from ladon.correspondence_cli import load_plan, publish
from ladon.proof_contract_io import load_bounded_plans
from ladon.proof_contract_source import produce_prose_contract, verify_prose_snapshot
from ladon.resource_limits import DEFAULT_MAX_RSS_MIB


def _parser():
    from ladon.proof_contract_context_cli import add_context_bridge_parsers
    from ladon.proof_contract_obligation_cli import add_obligations_parser, add_source_checks_parser
    from ladon.proof_contract_probe_calibration_cli import add_probe_calibration_parsers
    from ladon.proof_contract_probe_cli import add_application_probe_parsers
    from ladon.proof_contract_provider_cli import add_provider_expansion_parser
    from ladon.proof_contract_route_context_cli import add_route_context_parsers

    parser = argparse.ArgumentParser(prog="ladon investigation contract")
    sub = parser.add_subparsers(dest="operation", required=True)
    audit = sub.add_parser("audit", help="Run a bounded resumable contract audit")
    audit.add_argument("--input", type=Path, required=True, help="Closed audit plan JSON")
    audit.add_argument("--output-dir", type=Path, required=True, help="New immutable run directory")
    audit.add_argument("--resume", type=Path, help="Prior immutable run directory")
    audit.add_argument("--max-stages", type=int, default=64)
    add_obligations_parser(sub)
    add_source_checks_parser(sub)
    add_provider_expansion_parser(sub)
    add_context_bridge_parsers(sub)
    add_route_context_parsers(sub)
    add_probe_calibration_parsers(sub)
    add_application_probe_parsers(sub)
    produce = sub.add_parser("produce", help="Snapshot an attributed source contract")
    produce.add_argument("--channel", choices=("prose", "formal"), required=True)
    produce.add_argument("--root", type=Path, required=True)
    for name in ("interpretation", "record", "origins"):
        produce.add_argument("--" + name, type=Path)
    for name in ("alternative-id", "environment-ref", "file", "module", "declaration"):
        produce.add_argument("--" + name)
    produce.add_argument("--author", default="caller")
    produce.add_argument("--timeout-seconds", type=float, default=60)
    produce.add_argument("--max-rss-mib", type=int, default=DEFAULT_MAX_RSS_MIB)
    produce.add_argument("--output", type=Path)
    inspect = sub.add_parser("inspect", help="Inspect a snapshot and verify its source binding")
    _input_arguments(inspect, source_root=False)
    inspect.add_argument("--context", type=Path, help="Native artifact batch for exact replay")
    from ladon.proof_contract_refinement_cli import add_refinement_parser

    add_refinement_parser(sub)
    propagate = sub.add_parser("propagate", help="Propagate conditional contracts on a native graph")
    propagate.add_argument("--derivation", type=Path, required=True)
    propagate.add_argument("--contract", type=Path, action="append", default=[])
    propagate.add_argument("--request", type=Path, required=True)
    propagate.add_argument("--analysis-id", required=True)
    propagate.add_argument("--output", type=Path)
    fidelity = sub.add_parser("fidelity-record", help="Prepare independent source review")
    _input_arguments(fidelity)
    expand = sub.add_parser("expand", help="Extract a selected application for a named obligation")
    _input_arguments(expand)
    expand.add_argument("--application", required=True)
    expand.add_argument("--obligation-id", required=True)
    expand.add_argument("--occurrence", type=int, default=0)
    return parser


def _input_arguments(parser, *, source_root=True):
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=source_root)
    parser.add_argument("--output", type=Path)


def contract_main(argv):
    from ladon.proof_contract_context_cli import context_bridge
    from ladon.proof_contract_obligation_cli import check_obligations, obligations
    from ladon.proof_contract_probe_calibration import ProbeCalibrationOutputLimit
    from ladon.proof_contract_probe_calibration_cli import probe_calibration
    from ladon.proof_contract_probe_cli import application_probe
    from ladon.proof_contract_probes import ApplicationProbeOutputLimit
    from ladon.proof_contract_provider_cli import expand_provider
    from ladon.proof_contract_route_context_cli import route_context_bridge

    args = _parser().parse_args(argv)
    try:
        if args.operation == "audit":
            from ladon.proof_contract_audit import run_contract_audit

            report = run_contract_audit(args.input, args.output_dir, resume=args.resume,
                                        max_stages=args.max_stages)
            publish(report, None)
            return 0 if report["status"] == "completed" else 2
        from ladon.proof_contract_refinement_cli import refine_command

        result = {"produce": _produce, "inspect": _inspect, "refine": refine_command,
                  "expand": _expand,
                  "fidelity-record": _fidelity_record, "propagate": _propagate,
                  "obligations": obligations, "check-obligations": check_obligations,
                  "expand-provider": expand_provider, "context-obligations": context_bridge,
                  "check-context-bridge": context_bridge,
                  "route-context-obligations": route_context_bridge,
                  "probe-calibration-profile": probe_calibration,
                  "probe-calibration": probe_calibration,
                  "probe-profile": application_probe,
                  "probe": application_probe, "check-probe": application_probe,
                  "review-probe": application_probe,
                  "check-route-context-bridge": route_context_bridge}[args.operation](args)
        publish(result, args.output)
        return _exit_status(result)
    except (ProbeCalibrationOutputLimit, ApplicationProbeOutputLimit) as error:
        print(str(error), file=sys.stderr)
        return 2
    except (ValueError, TypeError, OSError, KeyError, IndexError) as error:
        print(json.dumps({"status": "invalid", "error": str(error)}))
        return 2


def _require(args, names):
    missing = ["--" + name.replace("_", "-") for name in names if getattr(args, name) is None]
    if missing:
        raise ValueError("missing channel arguments: " + ", ".join(missing))


def _produce(args):
    if args.channel == "formal":
        from ladon.proof_contract_formal import produce_formal_snapshot

        _require(args, ("file", "module", "declaration"))
        return produce_formal_snapshot(
            args.root, args.file, args.module, args.declaration,
            timeout_seconds=args.timeout_seconds, max_rss_bytes=args.max_rss_mib * 1024**2,
        )
    _require(args, ("interpretation", "record", "origins", "alternative_id", "environment_ref"))
    return produce_prose_contract(
        args.root, load_plan(args.interpretation), load_plan(args.record), load_plan(args.origins),
        alternative_id=args.alternative_id, environment_ref=args.environment_ref,
        author=args.author,
    )


def _inspect(args):
    if args.context is None:
        snapshot, = load_bounded_plans([args.input], max_bytes=32 * 1024**2)
        context = None
    else:
        snapshot, context = load_bounded_plans([args.input, args.context], max_bytes=32 * 1024**2)
    if snapshot.get("artifactKind") == "proofir.contract-analysis":
        return _inspect_native(snapshot, context)
    if snapshot.get("schema") == "ladon-proof-contract-refinement-workflow-v1":
        if context is not None:
            raise ValueError("refinement inspection does not accept --context")
        from ladon.proof_contract_refinement_workflow import inspect_refinement

        _require(args, ("root",))
        return inspect_refinement(snapshot, args.root)
    _require(args, ("root",))
    if snapshot.get("channel") == "formal":
        from ladon.proof_contract_formal import verify_formal_snapshot

        return verify_formal_snapshot(snapshot, args.root)
    return verify_prose_snapshot(snapshot, args.root)


def _inspect_native(artifact, context):
    from ladon.proof_contract_payloads import closed
    from ladon.proofir_v3 import validate_envelope_batch

    if context is None:
        raise ValueError("native analysis inspection requires --context")
    closed(context, {"artifacts"}, "native replay context")
    artifacts = context["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) > 4096:
        raise ValueError("context.artifacts requires a bounded native artifact list")
    if artifact.get("payload", {}).get("stage") == "probes":
        from ladon.proof_contract_probe_cli import inspect_application_probe

        return inspect_application_probe(artifact, context)
    if artifact.get("payload", {}).get("stage") == "obligations":
        return _inspect_obligations(artifact, context)
    validate_envelope_batch([*artifacts, artifact])
    return artifact


def _inspect_obligations(artifact, context):
    import time

    from .proof_contract_obligation_supervision import run_obligation_validation

    checked = run_obligation_validation(artifact, context,
                                        deadline_monotonic=time.monotonic() + 30)
    return checked['result'] if checked['status'] == 'completed' else checked


def _propagate(args):
    from ladon.proof_contract_artifacts import propagation_artifact
    from ladon.proof_contract_payloads import closed

    if len(args.contract) > 4096:
        raise ValueError("aggregate contract file count exceeds limit")
    graph, request, *contracts = load_bounded_plans(
        [args.derivation, args.request, *args.contract], max_bytes=8 * 1024**2,
    )
    closed(request, {"goalRef", "ruleBindings", "endpointInterfaces", "scopeBindings", "bounds"},
           "propagation request")
    return propagation_artifact(
        graph, contracts,
        analysis_id=args.analysis_id, goal_ref=request["goalRef"],
        rule_bindings=request["ruleBindings"], endpoint_interfaces=request["endpointInterfaces"],
        scope_bindings=request["scopeBindings"], bounds=request["bounds"],
    )


def _expand(args):
    from ladon.proof_contract_formal import expand_formal_snapshot

    return expand_formal_snapshot(load_plan(args.input), args.root, application=args.application,
                                  obligation_id=args.obligation_id, occurrence=args.occurrence)


def _fidelity_record(args):
    from ladon.proof_contract_source import observation_from_prose_snapshot

    return observation_from_prose_snapshot(load_plan(args.input), args.root)


def _exit_status(result):
    if result.get("schema") == "ladon-proof-contract-refinement-workflow-v1":
        return 0 if result.get("status") == "completed" else 2
    if (result.get("schema") == "ladon-application-probe-v1"
            and result.get("status") in {"unsupported", "unresolved"}):
        return 2
    if result.get("status") in {"unavailable", "incomplete", "rejected"}:
        return 2
    if result.get("slice", {}).get("status") == "unavailable":
        return 2
    return 0
