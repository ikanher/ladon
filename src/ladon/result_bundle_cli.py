"""CLI adapters for explicit bundle transport and existing result views."""
from __future__ import annotations

from pathlib import Path

from ladon.result_bundle_contract import DEFAULT_BUNDLE_BYTES, DEFAULT_BUNDLE_MEMBERS
from ladon.result_bundles import export_result_bundle, open_result_bundle, verify_result_bundle
from ladon.result_dossier import project_dossier
from ladon.result_guide_cards import selected_guide_targets
from ladon.result_guide_inputs import guide_currencies
from ladon.result_guides import _guide_prepared
from ladon.result_inspection import _inspect_prepared, _selected_targets
from ladon.result_manifest_io import ResultManifestError


def bundle_limit_arguments(parser):
    parser.add_argument('--max-bytes', type=int, default=DEFAULT_BUNDLE_BYTES,
                        help='Finite archive/expanded-byte ceiling (default 256 MiB).')
    parser.add_argument('--max-members', type=int, default=DEFAULT_BUNDLE_MEMBERS,
                        help='Finite archive member ceiling (default 10000).')


def add_bundle_commands(commands):
    export = commands.add_parser('export', help='Export explicitly disclosed files into a portable core bundle.')
    export.add_argument('manifest', type=Path)
    export.add_argument('--selection', type=Path, required=True)
    export.add_argument('--output', type=Path, required=True)
    verify = commands.add_parser('verify', help='Verify bundle integrity only; does not replay proofs.')
    verify.add_argument('bundle', type=Path)
    verify.add_argument('--extract-to', type=Path, help='Publish verified contents into a new directory.')
    for parser in (export, verify):
        bundle_limit_arguments(parser)
        parser.add_argument('--format', choices=('json', 'text'), default='json')


def bundle_command(args):
    options = {'max_bytes': args.max_bytes, 'max_members': args.max_members}
    if args.operation == 'export':
        return export_result_bundle(args.manifest, args.selection, args.output, **options)
    return verify_result_bundle(args.bundle, extract_to=args.extract_to, **options)


def bundle_view(args):
    extras = (args.artifact, args.lineage_inputs, getattr(args, 'assessments', None),
              getattr(args, 'guide_inputs', None))
    if any(extras):
        raise ResultManifestError('bundle input cannot be mixed with external evidence flags')
    with open_result_bundle(args.manifest, max_bytes=args.max_bytes,
                            max_members=args.max_members) as inputs:
        options = {'section': args.section, 'claim_id': args.claim,
                   'target_id': args.target, 'component_id': getattr(args, 'component', None),
                   'limit': args.limit, 'cursor': args.cursor,
                   'bundle_identity': inputs.identity}
        return _prepared_view(inputs, args.operation, options)


def _prepared_view(inputs, operation, options):
    if operation == 'guide':
        companion = inputs.guide
        currencies = guide_currencies(companion, inputs.manifest) if companion is not None else {}
        selected = selected_guide_targets(inputs.manifest, companion, currencies,
                                          options['claim_id'], options['target_id'])
        prepared = project_dossier(inputs.dossier, inputs.manifest, selected)
        return _guide_prepared(inputs.manifest, prepared, guide_inputs=companion, **options)
    selected = _selected_targets(inputs.manifest, options['claim_id'],
                                 options['component_id'], options['target_id'])
    prepared = project_dossier(inputs.dossier, inputs.manifest, selected)
    return _inspect_prepared(inputs.manifest, prepared, **options)
