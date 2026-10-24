"""Fresh refinement workflow command and bounded CLI options."""

import math
import time
from pathlib import Path


def add_refinement_parser(sub):
    refine = sub.add_parser("refine", help="Check a cited refinement and proposed repair")
    refine.add_argument("--input", type=Path, required=True)
    refine.add_argument("--root", type=Path, required=True)
    refine.add_argument("--output", type=Path)
    refine.add_argument("--timeout-seconds", type=float, default=120)
    refine.add_argument("--deadline-monotonic", type=float)
    refine.add_argument("--max-rss-mib", type=int, default=12 * 1024)


def refine_command(args):
    if args.output is not None and (args.output.exists() or args.output.is_symlink()):
        raise ValueError("output already exists")
    _validate_limits(args)
    deadline = time.monotonic() + args.timeout_seconds
    if args.deadline_monotonic is not None:
        deadline = min(deadline, args.deadline_monotonic)
    from ladon.proof_contract_io import load_bounded_plans
    from ladon.proof_contract_refinement_workflow import refine

    request, = load_bounded_plans([args.input], max_bytes=1024**2)
    return refine(request, args.root, deadline_monotonic=deadline,
                  max_rss_bytes=args.max_rss_mib * 1024**2)


def _validate_limits(args):
    if not math.isfinite(args.timeout_seconds) or not 0 < args.timeout_seconds <= 3600:
        raise ValueError("timeout-seconds must be positive and at most 3600")
    if args.deadline_monotonic is not None and not math.isfinite(args.deadline_monotonic):
        raise ValueError("deadline-monotonic must be finite")
    if not 0 < args.max_rss_mib <= 12 * 1024:
        raise ValueError("max-rss-mib must be positive and at most 12288")
