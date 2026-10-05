"""Validate manifests or resolve explicitly supplied evidence without execution."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ladon.cli_execution import EXIT_INTERRUPTED, EXIT_INVOCATION, EXIT_OPERATIONAL
from ladon.result_bundle_cli import (
    add_bundle_commands,
    bundle_command,
    bundle_limit_arguments,
    bundle_view,
)
from ladon.result_bundles import is_result_bundle
from ladon.result_evidence_io import load_result_artifacts
from ladon.result_guides import GUIDE_SECTIONS, guide_result_manifest
from ladon.result_inspection import SECTIONS, inspect_result_manifest
from ladon.result_inspection_page import text_projection
from ladon.result_manifest import validate_result_manifest
from ladon.result_manifest_io import ResultManifestError, canonical_json, load_result_manifest
from ladon.result_manifest_summary import manifest_summary
from ladon.result_resolution import resolve_result_manifest


class ResultArgumentParser(argparse.ArgumentParser):
    """Translate parser errors using the ordinary structured CLI boundary."""

    def error(self, message: str) -> None:
        raise ResultManifestError(message)


def result_main(argv: Sequence[str] | None = None) -> int:
    """Keep offline integrity and explicit canonical resolution separate."""

    operation = argv[0] if argv and argv[0] in {'resolve', 'inspect', 'guide', 'export', 'verify'} else 'validate'
    try:
        args = _parser().parse_args(argv)
        result = _execute(args)
        output = canonical_json(result).decode() if args.format == "json" else _text(result)
        print(output)
        return 0
    except ResultManifestError as exc:
        return _failure("invocation", EXIT_INVOCATION, "manifest-invalid", str(exc), operation)
    except OSError:
        return _failure("operational", EXIT_OPERATIONAL, "manifest-unreadable", "Cannot read result input.", operation)
    except KeyboardInterrupt:
        return _failure("interrupted", EXIT_INTERRUPTED, "interrupted", "Operation interrupted.", operation)


def _parser() -> argparse.ArgumentParser:
    parser = ResultArgumentParser(prog="ladon result", description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    validate = commands.add_parser("validate", help="Check manifest integrity; does not check Lean or correspondence.")
    validate.add_argument("manifest", type=Path)
    validate.add_argument("--format", choices=("json", "text"), default="json")
    resolve = commands.add_parser("resolve", help="Bind targets to explicitly supplied local canonical evidence.")
    resolve.add_argument("manifest", type=Path)
    resolve.add_argument("--artifact", type=Path, action="append", default=[])
    resolve.add_argument("--target", help="Display one exact target ID; complete input remains validated.")
    resolve.add_argument("--format", choices=("json", "text"), default="json")
    inspect = commands.add_parser('inspect', help='Inspect supplied result evidence offline without running checks.')
    inspect.add_argument('--assessments', type=Path, help='Versioned attributable component assessments.')
    _view_arguments(inspect, SECTIONS, 'components')
    inspect.add_argument('--component', help='Exact component ID within the selected claim.')
    guide = commands.add_parser('guide', help='Read attributed explanations and citations alongside stored evidence.')
    guide.add_argument('--guide-inputs', type=Path, help='Versioned authored steps, citations and scoped reviews.')
    guide.add_argument('--assessments', type=Path, help='Versioned attributable component assessments.')
    guide.add_argument('--component', help='Exact component ID for the exposition section.')
    _view_arguments(guide, GUIDE_SECTIONS, 'steps')
    add_bundle_commands(commands)
    return parser


def _view_arguments(parser, sections, default):
    bundle_limit_arguments(parser)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--artifact', type=Path, action='append', default=[])
    parser.add_argument('--lineage-inputs', type=Path, help='Explicit stored lineage selections; no refresh.')
    parser.add_argument('--section', choices=sections, default=default)
    parser.add_argument('--claim', help='Exact claim ID.')
    parser.add_argument('--target', help='Exact target ID.')
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--cursor', help='Continuation from identical inputs and query.')
    parser.add_argument('--format', choices=('json', 'text'), default='json')


def _execute(args):
    if args.operation in {'export', 'verify'}:
        return bundle_command(args)
    if args.operation in {'inspect', 'guide'} and is_result_bundle(args.manifest):
        return bundle_view(args)
    manifest = validate_result_manifest(load_result_manifest(args.manifest))
    if args.operation in {'inspect', 'guide'}:
        return _view(args, manifest)
    if args.operation == 'resolve':
        return resolve_result_manifest(manifest, load_result_artifacts(args.artifact), target_id=args.target)
    return manifest_summary(manifest)


def _view(args, manifest):
    lineage = load_result_manifest(args.lineage_inputs) if args.lineage_inputs else None
    options = {'section': args.section, 'claim_id': args.claim,
               'target_id': args.target,
               'limit': args.limit, 'cursor': args.cursor, 'lineage_inputs': lineage,
               'lineage_base': args.lineage_inputs.parent if args.lineage_inputs else Path('.')}
    artifacts = load_result_artifacts(args.artifact)
    if args.operation == 'guide':
        companion = load_result_manifest(args.guide_inputs) if args.guide_inputs else None
        assessments = load_result_manifest(args.assessments) if args.assessments else None
        options['component_id'] = getattr(args, 'component', None)
        return guide_result_manifest(manifest, artifacts, guide_inputs=companion,
                                     assessments=assessments, **options)
    companion = load_result_manifest(args.assessments) if args.assessments else None
    options['component_id'] = getattr(args, 'component', None)
    return inspect_result_manifest(manifest, artifacts, assessments=companion, **options)


def _text(result: dict) -> str:
    # Render the same bounded sections as JSON; do not drop historical/omission data.
    return text_projection(result)


def _failure(exit_class: str, code: int, diagnostic: str, message: str, operation: str = "validate") -> int:
    result = {
        "schema": "ladon-result-terminal-v1", "operation": operation, "status": "failed",
        "exitClass": exit_class, "exitCode": code,
        "diagnostic": {"code": diagnostic, "message": message[:1024]},
    }
    print(canonical_json(result).decode(), file=sys.stderr)
    return code
