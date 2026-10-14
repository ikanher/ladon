"""Ordinary command entry points for attributed correspondence work."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ladon.correspondence_check import check_correspondence, prepare_correspondence
from ladon.correspondence_interpretation import (
    UnsupportedInterpretation,
    lower_formula,
    validate_interpretation,
)
from ladon.investigation import load_plan as _load_plan
from ladon.proofir_correspondence import (
    bind_native_interpretation,
    correspondence_artifacts,
    interpretation_artifacts,
)
from ladon.proofir_v3 import validate_envelope_batch


def load_plan(path):
    return _load_plan(path, max_bytes=32 * 1024**2)


def publish(value, output):
    # Use complete ordinary JSON. Check the consumer's unchanged cap before
    # creating any output; failed publication must leave no partial receipt.
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")) + "\n"
    if len(encoded.encode("utf-8")) > 32 * 1024**2:
        raise ValueError("complete compact output exceeds 32 MiB")
    if output is None:
        print(encoded, end="")
    else:
        with output.open("x", encoding="utf-8") as stream:
            stream.write(encoded)


def proof_slice_main(argv):
    from ladon.proof_slice import extract_proof_slice

    parser = argparse.ArgumentParser(prog="ladon proof-search proof slice")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--declaration", required=True)
    parser.add_argument("--application", required=True)
    parser.add_argument("--occurrence", type=int, default=0)
    parser.add_argument("--scoped", action="store_true", help="Open bounded nested local scopes")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = extract_proof_slice(
            args.repo, args.source, args.module, args.declaration, args.application, args.occurrence,
            scoped=args.scoped,
        )
        publish(result, args.output)
        return 0 if result["complete"] else 2
    except (ValueError, TypeError, OSError, KeyError, IndexError) as error:
        _publish_failure(error)
        return 2


def _parser():
    parser = argparse.ArgumentParser(prog="ladon investigation")
    commands = parser.add_subparsers(dest="command", required=True)
    interpret = commands.add_parser(
        "interpret", help="Bind one scoped interpretation to exact source bytes"
    )
    interpret.add_argument("--record", type=Path, required=True)
    interpret.add_argument("--root", type=Path, required=True)
    interpret.add_argument(
        "--slice", type=Path, help="Use this actual slice's environment for native references"
    )
    interpret.add_argument("--output", type=Path)
    align = commands.add_parser(
        "align", help="Generate the original missing implications from an actual application"
    )
    align.add_argument("--interpretation", type=Path, required=True)
    align.add_argument("--slice", type=Path, required=True)
    align.add_argument("--map", type=Path, required=True)
    align.add_argument("--root", type=Path, required=True)
    align.add_argument("--output", type=Path)
    check = commands.add_parser(
        "check", help="Replay bounded terms against exact generated obligations"
    )
    check.add_argument("--plan", type=Path, required=True)
    check.add_argument("--terms", type=Path, required=True)
    check.add_argument("--repo", type=Path, required=True)
    check.add_argument("--root", type=Path, required=True)
    check.add_argument("--output", type=Path)
    check.add_argument("--preparation", choices=("ordinary", "request"), default="ordinary")
    inspect = commands.add_parser("inspect", help="Inspect generated obligations and residuals")
    inspect.add_argument("--plan", type=Path, required=True)
    inspect.add_argument("--output", type=Path)
    inspect.add_argument("--root", type=Path, help="Required for source-bound version-three plans")
    return parser


def _interpret(args):
    record = validate_interpretation(load_plan(args.record), args.root)
    try:
        lowered = lower_formula(record["formula"], record["symbols"])
        residuals = []
    except UnsupportedInterpretation as error:
        lowered, residuals = None, [str(error)]
    result = {
        "schema": "ladon-interpretation-v1",
        "record": record,
        "loweredFormula": lowered,
        "fidelity": "attributed-unreviewed",
        "residuals": residuals,
    }
    environment = (
        load_plan(args.slice)["environment"]
        if args.slice
        else "sha256:" + record["source"]["sha256"]
    )
    result["artifacts"] = list(interpretation_artifacts(record, environment, source_root=args.root))
    validate_envelope_batch(result["artifacts"])
    return result


def _align(args):
    value = load_plan(args.interpretation)
    record = value["record"] if value.get("schema") == "ladon-interpretation-v1" else value
    record = validate_interpretation(record, args.root)
    if "artifacts" in value:
        from ladon.proofir_correspondence_payloads import (
            validate_native_interpretation_batch,
        )

        validate_envelope_batch(value["artifacts"])
        validate_native_interpretation_batch(
            record,
            value["artifacts"],
            value["artifacts"][0]["environmentRef"],
            source_root=args.root,
        )
    proof_slice = load_plan(args.slice)
    artifacts = list(
        interpretation_artifacts(record, proof_slice["environment"], source_root=args.root)
    )
    plan = prepare_correspondence(record, proof_slice, load_plan(args.map))
    plan = bind_native_interpretation(plan, artifacts, source_root=args.root)
    artifacts.append(correspondence_artifacts(plan))
    validate_envelope_batch(artifacts)
    result = {
        "schema": "ladon-correspondence-bundle-v1",
        "plan": plan,
        "artifacts": artifacts,
    }
    return result


def _check(args):
    value = load_plan(args.plan)
    plan = value["plan"] if value.get("schema") == "ladon-correspondence-bundle-v1" else value
    artifacts = value.get("artifacts")
    result = check_correspondence(
        plan,
        load_plan(args.terms),
        args.repo,
        source_root=args.root,
        native_artifacts=artifacts,
        preparation=args.preparation,
    )
    if artifacts is not None:
        from ladon.correspondence_evidence import completion_artifacts

        checks, refs = completion_artifacts(plan, result)
        result["checkRunRefs"] = refs
        result["artifacts"] = [*artifacts, *checks, correspondence_artifacts(plan, result)]
        validate_envelope_batch(result["artifacts"])
        result["plan"] = plan
    _measure_bundle_bytes(result)
    return result


def _measure_bundle_bytes(result):
    metrics = result["executionAccounting"]
    for _ in range(3):
        metrics["serializedBundleBytes"] = len((json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode())


def _inspect(args):
    value = load_plan(args.plan)
    if value.get("version") == 3:
        if args.root is None:
            raise ValueError("version-three inspection requires --root")
        from ladon.investigation_correspondence import assess_v3

        return assess_v3(value, args.root)
    plan = value.get("plan", value)
    result = {
        "schema": "ladon-correspondence-inspection-v1",
        "planId": plan["planId"],
        "obligations": plan["obligations"],
        "residuals": plan["residuals"],
        "interpretationFidelity": "attributed-unreviewed",
        "methodCorrespondence": "unreviewed",
        "elaboratedInterpretations": [row["typedSubject"] for row in value.get("checks", [])
                                     if row.get("obligation") == "interpretation"
                                     and "typedSubject" in row],
        "interpretationCheckScope": "typing-only; no source fidelity or truth claim",
    }
    if "artifacts" in value:
        import sqlite3

        from ladon.proofir_sqlite_v3 import project_envelopes
        from ladon.proofir_v3_queries import query_v3_correspondence

        artifacts = value["artifacts"]
        validate_envelope_batch(artifacts)
        if value.get("schema") == "ladon-correspondence-check-v1":
            from ladon.investigation_correspondence_inputs import validate_check_receipt_bindings
            validate_check_receipt_bindings(value)
        native = [row for row in artifacts if row["artifactKind"] == "proofir.correspondence"][-1]
        with sqlite3.connect(":memory:") as database:
            project_envelopes(database, artifacts)
            result["native"] = query_v3_correspondence(
                database,
                {
                    "artifactRef": native["artifactId"],
                    "kind": "correspondence",
                    "localId": native["payload"]["correspondenceId"],
                },
                limit=100,
            )
    return result


def correspondence_main(argv):
    args = _parser().parse_args(argv)
    handlers = {"interpret": _interpret, "align": _align, "check": _check, "inspect": _inspect}
    try:
        publish(handlers[args.command](args), args.output)
        return 0
    except (ValueError, TypeError, OSError, KeyError, IndexError) as error:
        _publish_failure(error)
        return 2


def _publish_failure(error):
    from dataclasses import asdict

    from ladon.correspondence_preparation import SourcePreparationFailure
    result = {"status": "invalid", "error": str(error)}
    if isinstance(error, SourcePreparationFailure):
        result.update(planId=error.plan_id, unattemptedObligations=error.unattempted,
                      process=asdict(error.process))
    else:
        encoded = json.dumps(result)
        if len(encoded.encode()) > 32 * 1024**2:
            encoded = json.dumps({"status": "invalid", "error": "Complete failure message exceeds 32 MiB; no receipt published."})
        print(encoded)
        return
    try:
        publish(result, None)
    except ValueError:
        # Failed evidence publication grants no checking authority; preserve
        # the bounded frontier rather than emit an over-cap diagnostic stream.
        result.pop("process", None)
        result["error"] = "Complete failure evidence exceeds 32 MiB; no check receipt published."
        publish(result, None)
