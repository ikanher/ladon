"""Ordinary additive CLI for source-bound application probes."""
from pathlib import Path

from .proof_contract_io import load_bounded_plans


def add_application_probe_parsers(subparsers):
    profile = subparsers.add_parser('probe-profile', help='Describe supported application-probe families')
    profile.add_argument('--output', type=Path)
    for operation in ('probe', 'check-probe'):
        parser = subparsers.add_parser(operation, help='Plan or check source-bound application probes')
        parser.add_argument('--input', type=Path, required=True)
        parser.add_argument('--output', type=Path)
        if operation == 'check-probe':
            parser.add_argument('--plan-id', required=True)
            parser.add_argument('--terms', type=Path, required=True)
            parser.add_argument('--reuse-result', type=Path,
                help='Reuse exact accepted receipts from trusted local Ladon output; '
                     'not authenticated against writers of this repository')
    review = subparsers.add_parser(
        'review-probe', help='Export source and checker attempts without Ladon conclusions'
    )
    review.add_argument('--input', type=Path, required=True,
                        help='Original source-bound probe request')
    review.add_argument('--artifact', type=Path, required=True,
                        help='Native planning artifact produced by probe')
    review.add_argument('--attempt', type=Path, action='append', required=True,
                        help='A complete check-probe result; repeat to preserve attempt order')
    review.add_argument('--output', type=Path)


def application_probe(args):
    from .proof_contract_probes import (
        application_probe_profile,
        check_application_probe,
        plan_application_probe,
    )

    if args.operation == 'probe-profile':
        return application_probe_profile()
    if args.operation == 'review-probe':
        return _review_application_probe(args)
    paths = [args.input] if args.operation == 'probe' else [args.input, args.terms]
    if args.operation == 'check-probe' and args.reuse_result is not None:
        paths.append(args.reuse_result)
    inputs = load_bounded_plans(paths, max_bytes=8 * 1024**2)
    if args.operation == 'probe':
        return plan_application_probe(inputs[0])
    cached = None
    if len(inputs) == 3:
        prior = inputs[2]
        cached = prior.get('cache') if isinstance(prior, dict) and prior.get('schema') == 'ladon-application-probe-v1' else prior
    return check_application_probe(inputs[0], args.plan_id, inputs[1], cached_result=cached)


def _review_application_probe(args):
    from ._proof_contract_probe_inputs import probe_inputs
    from .proof_contract_probe_review import MAX_REVIEW_BYTES, review_application_probe

    if len(args.attempt) > 64:
        raise ValueError('probe reviewer export accepts at most 64 attempts')
    paths = [args.input, args.artifact, *args.attempt]
    inputs = load_bounded_plans(paths, max_bytes=MAX_REVIEW_BYTES)
    request = probe_inputs(inputs[0])
    return review_application_probe(
        inputs[1], request['context'], inputs[2:], request['repoRoot']
    )


def inspect_application_probe(artifact, context):
    """Pure semantic replay in a bounded worker; no source freshness claim."""
    import time

    from ._proof_contract_planned_source_inputs import _planned_input_size
    from .proof_contract_probes import _stage

    request = {'artifact': artifact, 'context': context}
    if _planned_input_size(request) > 8 * 1024**2:
        raise ValueError('probe inspection input exceeds 8 MiB')
    owned = {'deadlineMonotonic': time.monotonic() + 30,
        'limits': {'timeout_seconds': 30, 'max_output_bytes': 8 * 1024**2,
                   'max_rss_bytes': 12 * 1024**3}}
    checked = _stage('inspect-probe', request, owned)
    return checked['result'] if checked['status'] == 'completed' else checked
