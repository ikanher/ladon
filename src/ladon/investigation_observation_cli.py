"""Public capture, review and reporting operations for source observations."""

import json
from pathlib import Path

from ladon.correspondence_cli import publish
from ladon.investigation import _array, _object, load_plan
from ladon.investigation_correspondence_cli import load_investigation
from ladon.investigation_observations import (
    challenge_observation,
    ingest_observation_response,
    inspect_observations,
    record_observation,
)
from ladon.investigation_reporting import aggregate_report


def add_observation_parsers(sub):
    capture = sub.add_parser("observe", help="Capture an immutable source-bound observation")
    capture.add_argument("--record", type=Path, required=True)
    for child in (capture, sub.add_parser("inspect-observations", help="Inspect recorded observations")):
        child.add_argument("--plan", type=Path, required=True)
        child.add_argument("--root", type=Path, required=True)
    capture.add_argument("--output", type=Path, required=True)
    report = sub.add_parser("report", help="Report compatible supplementary plans without merging them")
    report.add_argument("--plan", type=Path, action="append", required=True)
    report.add_argument("--root", type=Path, required=True)
    report.add_argument("--output", type=Path)
    report.add_argument("--refinement", type=Path, action="append", default=[])


def observation_command(args):
    if args.command == "report":
        return _report(args)
    if args.command in {"observe", "inspect-observations"}:
        return _capture_or_inspect(args)
    if args.command in {"challenge", "ingest", "reconcile"}:
        return _observation_transition(args)
    return None


def _report(args):
    if len(args.plan) > 16:
        raise ValueError("report requires 1..16 plans")
    if len(args.refinement) > 4:
        raise ValueError("report accepts at most four refinement supplements")
    if args.refinement:
        from ladon.proof_contract_io import load_bounded_plans

        refinements = load_bounded_plans(args.refinement, max_bytes=32 * 1024**2)
    else:
        refinements = None
    result = aggregate_report([load_investigation(p) for p in args.plan], args.root,
                              refinements=refinements)
    if args.output is not None:
        publish(result, args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


def _capture_or_inspect(args):
    plan = load_investigation(args.plan)
    if args.command == "observe":
        result = record_observation(plan, load_plan(args.record, max_bytes=1024**2), args.root)
        publish(result, args.output)
        print(json.dumps({"status": "published", "output": str(args.output), "operation": "observe"}))
    else:
        entries = inspect_observations(plan, args.root)
        schema = ("ladon-investigation-observations-v2"
                  if any(row["record"].get("schema") == "ladon-investigation-observation-v2"
                         for row in entries)
                  else "ladon-investigation-observations-v1")
        print(json.dumps({"schema": schema, "observations": entries}, ensure_ascii=False))
    return 0


def _observation_transition(args):
    plan = load_investigation(args.plan)
    response = (None if args.command == "challenge"
                else _object(load_plan(args.response, max_bytes=1024**2), "response"))
    subject = args.claim if response is None else response.get("subject")
    rows = _array(plan.get("observations", []), "observations")
    if not any(isinstance(row, dict) and row.get("observationId") == subject for row in rows):
        return None
    if response is None:
        result = challenge_observation(plan, subject, args.root)
    else:
        result = ingest_observation_response(plan, load_plan(args.packet), response, args.root,
                                              first=args.first if args.command == "reconcile" else None)
    publish(result, args.output)
    print(json.dumps({"status": "published", "output": str(args.output), "operation": args.command}))
    return 0
