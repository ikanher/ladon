"""Publish immutable structured-review transitions through the ordinary CLI."""

import json

from ladon.correspondence_cli import publish
from ladon.investigation import load_plan
from ladon.investigation_correspondence import attach_bundle, challenge_packet_v3, ingest_response


def load_investigation(path):
    plan = load_plan(path, max_bytes=32 * 1024**2)
    if plan.get("version") in (1, 2) and path.stat().st_size > 4 * 1024**2:
        raise ValueError("plan exceeds 4194304 bytes")
    return plan


def structured_transition(args):
    plan = load_investigation(args.plan)
    if plan.get("version") != 3:
        raise ValueError("structured review command requires an opt-in version-three plan")
    if args.command == "attach":
        value = attach_bundle(plan, load_plan(args.bundle, max_bytes=32 * 1024**2), args.root)
    elif args.command == "challenge":
        value = challenge_packet_v3(plan, args.claim, args.root)
    else:
        packet = load_plan(args.packet, max_bytes=32 * 1024**2)
        response = load_plan(args.response, max_bytes=1024**2)
        value = ingest_response(plan, packet, response, args.root,
                                first=args.first if args.command == "reconcile" else None)
    publish(value, args.output)
    print(json.dumps({"status": "published", "output": str(args.output), "operation": args.command}))
    return 0
