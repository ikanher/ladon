"""Lightweight investigation commands with an explicit finalization gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ladon.investigation import assess, initialize, load_plan


def investigation_main(argv=None):
    if argv and argv[0] == "contract":
        from ladon.proof_contract_cli import contract_main

        return contract_main(argv[1:])
    if argv and argv[0] in {"interpret", "align", "check", "inspect"}:
        from ladon.correspondence_cli import correspondence_main

        return correspondence_main(argv)
    args = _investigation_parser().parse_args(argv)
    try:
        return _run_investigation(args)
    except (ValueError, TypeError, OSError, KeyError, IndexError) as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}))
        return 2


def _investigation_parser():
    parser = argparse.ArgumentParser(prog="ladon investigation")
    sub = parser.add_subparsers(dest="command", required=True)
    from ladon.investigation_observation_cli import add_observation_parsers

    add_observation_parsers(sub)
    sub.add_parser("contract", help="Produce and inspect source-bound mathematical contracts")
    for name in ("interpret", "align", "check", "inspect"):
        sub.add_parser(name, help="Structured correspondence authoring and evidence inspection")
    init = sub.add_parser("init", help="Create a new source-bound plan without overwriting")
    init.add_argument("--text", type=Path, required=True)
    init.add_argument("--root", type=Path, required=True)
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--minutes", type=int, default=90)
    init.add_argument("--unit-lines", type=int, default=80)
    versions = init.add_mutually_exclusive_group()
    versions.add_argument("--derivations", action="store_true", help="Use version-two local challenges")
    versions.add_argument("--correspondence", action="store_true", help="Use opt-in version-three structured review")
    for name in ("attach", "ingest", "reconcile"):
        child = sub.add_parser(name, help="Publish an immutable version-three review transition")
        child.add_argument("--plan", type=Path, required=True)
        child.add_argument("--root", type=Path, required=True)
        child.add_argument("--output", type=Path, required=True)
        if name == "attach":
            child.add_argument("--bundle", type=Path, required=True)
        else:
            child.add_argument("--packet", type=Path, required=True)
            child.add_argument("--response", type=Path, required=True)
        if name == "reconcile":
            child.add_argument("--first", required=True)
    for name in ("challenge", "witness"):
        child = sub.add_parser(name)
        child.add_argument("--plan", type=Path, required=True)
        child.add_argument("--root", type=Path, required=True)
        child.add_argument("--claim", required=True)
        if name == "challenge":
            child.add_argument("--output", type=Path, required=True)
        else:
            child.add_argument("--step", required=True)
            child.add_argument("--assignment", type=Path, required=True)
    for name in ("checkpoint", "finalize"):
        child = sub.add_parser(name, help="Save a freshly bound immutable progress receipt")
        child.add_argument("--plan", type=Path, required=True)
        child.add_argument("--root", type=Path, required=True)
        child.add_argument("--output", type=Path, required=True)
        if name == "finalize":
            child.add_argument("--stop-record", type=Path)
    for name in ("status", "next", "finish"):
        child = sub.add_parser(name)
        child.add_argument("--plan", type=Path, required=True)
        child.add_argument("--root", type=Path, required=True)
        child.add_argument("--limit", type=int, default=8)
    return parser


def _initialize_plan(args):
    plan = initialize(
        args.text,
        args.root,
        minutes=args.minutes,
        unit_lines=args.unit_lines,
        derivations=args.derivations,
        correspondence=args.correspondence,
    )
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(plan, stream, indent=2)
        stream.write("\n")
    print(
        json.dumps(
            {"status": "initialized", "plan": str(args.output), "units": len(plan["units"])}
        )
    )
    return 0


def _run_investigation(args):
    from ladon.investigation_correspondence_cli import load_investigation, structured_transition
    from ladon.investigation_observation_cli import observation_command

    observed = observation_command(args)
    if observed is not None:
        return observed

    if args.command == "init":
        return _initialize_plan(args)
    if args.command in {"checkpoint", "finalize"}:
        return _progress_transition(args)
    if args.command in {"attach", "ingest", "reconcile"}:
        return structured_transition(args)
    if args.command == "challenge" and load_investigation(args.plan).get("version") == 3:
        return structured_transition(args)
    if args.command in ("challenge", "witness"):
        return _legacy_challenge(args)
    return _investigation_status(args)


def _progress_transition(args):
    from ladon.correspondence_cli import publish
    from ladon.investigation_correspondence_cli import load_investigation
    from ladon.investigation_finalization import progress_receipt

    stop = getattr(args, "stop_record", None)
    result, saved = progress_receipt(load_investigation(args.plan), args.root,
                                    finalize=args.command == "finalize",
                                    stop_record=load_plan(stop) if stop else None)
    if saved:
        publish(result, args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if saved else 2


def _legacy_challenge(args):
    from ladon.investigation_correspondence_cli import load_investigation
    from ladon.investigation_derivation import challenge_packet, find_step, step_subject
    from ladon.rational_witness import check_witness

    plan = load_investigation(args.plan)
    if plan.get("version") == 3:
        raise ValueError("version-three correspondence does not support rational witness commands")
    assess(plan, args.root)
    if args.command == "challenge":
        packet = challenge_packet(plan, args.claim)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(packet, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(
            json.dumps(
                {
                    "status": "challenge-exported",
                    "output": str(args.output),
                    "steps": len(packet["steps"]),
                }
            )
        )
    else:
        claim, step = find_step(plan, args.claim, args.step)
        if "arithmetic" not in step:
            raise ValueError("step has no rational arithmetic interpretation")
        checked = check_witness(step["arithmetic"], load_plan(args.assignment))
        checked.update(
            claim=claim["id"],
            step=step["id"],
            subjectSha256=step_subject(plan, claim, step),
            interpretation="Authored mapping to the original source, not certified.",
        )
        print(json.dumps(checked, ensure_ascii=False, sort_keys=True))
    return 0


def _investigation_status(args):
    from ladon.investigation_correspondence_cli import load_investigation

    if not 1 <= args.limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    result = assess(load_investigation(args.plan), args.root)
    result["nextOmitted"] = max(0, len(result["next"]) - args.limit)
    result["next"] = result["next"][: args.limit]
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if args.command == "finish" and not result["mayFinalize"] else 0
