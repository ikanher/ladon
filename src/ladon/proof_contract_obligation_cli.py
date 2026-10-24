"""Public obligations command using bounded native input and immutable publication."""
from .proof_contract_io import load_bounded_plans


def add_obligations_parser(subparsers):
    from pathlib import Path

    parser = subparsers.add_parser('obligations', help='Plan ordered conditional route obligations')
    parser.add_argument('--derivation', type=Path, required=True)
    parser.add_argument('--contract', type=Path, action='append', default=[])
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--analysis-id', required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--timeout-seconds', type=float, default=60)
    parser.add_argument('--max-rss-mib', type=int, default=12 * 1024)


def add_source_checks_parser(subparsers):
    from pathlib import Path

    parser = subparsers.add_parser('check-obligations',
        help='Check all retained source demands under one shared budget')
    for name in ('input', 'context', 'sources', 'root', 'output-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--timeout-seconds', type=float, default=180)
    parser.add_argument('--max-rss-mib', type=int, default=12 * 1024)
    parser.add_argument('--max-check-attempts', type=int, default=16)
    parser.set_defaults(output=None)


def check_obligations(args):
    import time

    from .proof_contract_obligation_checks import check_obligation_sources

    deadline = time.monotonic() + args.timeout_seconds
    artifact, context, sources = load_bounded_plans(
        [args.input, args.context, args.sources], max_bytes=8 * 1024**2)
    return check_obligation_sources({'repoRoot': args.root, 'analysisArtifact': artifact,
        'context': context, 'sourceBindings': sources, 'outputDir': args.output_dir,
        'deadlineMonotonic': deadline, 'maxCheckAttempts': args.max_check_attempts,
        'limits': {'timeout_seconds': min(30, args.timeout_seconds),
                   'max_output_bytes': 8 * 1024**2,
                   'max_rss_bytes': args.max_rss_mib * 1024**2}})


def obligations(args):
    import time

    from .proof_contract_obligation_artifacts import request_from_payload
    from .proof_contract_obligation_supervision import run_obligation_planner

    if len(args.contract) > 4096:
        raise ValueError('aggregate contract file count exceeds limit')
    graph, payload, *contracts = load_bounded_plans(
        [args.derivation, args.request, *args.contract], max_bytes=8 * 1024**2)
    request = request_from_payload(graph, contracts, payload)
    checked = run_obligation_planner(request,
        deadline_monotonic=time.monotonic() + args.timeout_seconds,
        limits={'timeout_seconds': args.timeout_seconds, 'max_output_bytes': 8 * 1024**2,
                'max_rss_bytes': args.max_rss_mib * 1024**2},
        operation='artifact-v2', analysis_id=args.analysis_id)
    if checked['status'] != 'completed':
        return checked
    return _attach_receipt(checked)


def _attach_receipt(checked):
    from ._proof_contract_planned_source_inputs import _planned_input_size
    from .proofir_v3 import detached_content_id, validate_envelope

    artifact = checked['result']
    artifact['extensions']['ladon.obligation-supervision/v1'] = _native_receipt({
        'workerInputDigest': checked['workerInputDigest'], 'bounds': checked['bounds'],
        'processReceipt': checked['processReceipt']})
    artifact['artifactId'] = detached_content_id(artifact)
    if _planned_input_size(artifact) > 8 * 1024**2:
        raise ValueError('native obligation artifact and receipt exceed 8 MiB')
    return validate_envelope(artifact).to_dict()


def _native_receipt(value):
    """Keep exact round-trippable seconds outside native integer-only numbers."""
    if isinstance(value, float):
        return 'seconds:' + repr(value)
    if isinstance(value, dict):
        return {key: _native_receipt(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_native_receipt(item) for item in value]
    return value
