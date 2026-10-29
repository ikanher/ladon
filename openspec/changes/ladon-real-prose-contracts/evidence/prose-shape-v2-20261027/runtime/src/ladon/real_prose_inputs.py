"""Closed source-context requests and generated proposition ownership."""

import hashlib
import json
from pathlib import Path

from ladon.correspondence_interpretation import lower_formula, validate_interpretation
from ladon.proof_contract_payloads import closed
from ladon.proof_contract_source import snapshot_identity
from ladon.proof_contract_worker import _NAME, MAX_SOURCE_BYTES
from ladon.source_association_io import _read_regular, _source_path

SCHEMA = 'ladon-real-prose-observation-v1'
WORKER_SCHEMA = 'ladon-prose-proposition-worker-v1'
HELPER_VERSION = 'ladon-prose-proposition-helper-v1'
HELPER = Path(__file__).parent / 'lean/ladon_prose_observation.lean'
MAX_BYTES = 8 * 1024**2


def sha(value):
    return hashlib.sha256(value).hexdigest()


def validate_context(context):
    closed(context, {'schema', 'file', 'module', 'scope'}, 'prose bound context')
    if (context['schema'] != 'ladon-prose-bound-context-v1'
            or context['scope'] != 'file-end'):
        raise ValueError('unsupported prose context schema or scope')
    if not isinstance(context['module'], str) or not _NAME.fullmatch(context['module']):
        raise ValueError('prose context requires an ordinary module name')
    if not isinstance(context['file'], str):
        raise TypeError('prose context file must be a string')
    return dict(context)


def context_source(root, context):
    validate_context(context)
    path = _source_path(root, context['file'], context['module'])
    return _read_regular(path, MAX_SOURCE_BYTES)


def reading_request(root, interpretation, context):
    return {'interpretation': validate_interpretation(interpretation, root),
            'context': validate_context(context)}


def generated_source(request, source):
    reading = request['interpretation']
    lowered = lower_formula(reading['formula'], reading['symbols'])
    identity = snapshot_identity({'request': request, 'contextDigest': sha(source)})
    declaration = 'LadonProseReading_' + identity[7:]
    suffix = f'\n\nnoncomputable def _root_.{declaration} : Prop := {lowered}\n'
    content = source + suffix.encode()
    if len(content) > MAX_SOURCE_BYTES:
        raise ValueError('generated prose source exceeds 8 MiB')
    return content, {'declaration': declaration, 'sourceDigest': sha(content),
                     'sourceBytes': len(content), 'contextBytes': len(source)}


def implementation_identity():
    """Conservatively bind the complete shipped runtime, including shared readers."""
    directory = Path(__file__).parent
    paths = sorted(p for p in directory.rglob('*') if p.suffix in {'.py', '.lean'})
    return snapshot_identity({str(p.relative_to(directory)): sha(p.read_bytes()) for p in paths})


def observation_identity(snapshot):
    value = {k: v for k, v in snapshot.items() if k != 'snapshotId'}
    try:
        encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(',', ':'), allow_nan=False).encode()
    except (RecursionError, TypeError) as error:
        raise ValueError('prose snapshot exceeds bounded JSON shape') from error
    if len(encoded) > 32 * 1024**2:
        raise ValueError('prose snapshot exceeds 32 MiB')
    return 'sha256:' + sha(encoded)
