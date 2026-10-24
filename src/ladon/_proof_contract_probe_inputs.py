"""Closed, aggregate-bounded public application-probe inputs."""
import copy
import math

from ._proof_contract_planned_source_inputs import _planned_input_size
from ._proof_contract_probe_pair import MAX_BYTES, probe_context, probe_side
from .proof_contract_bridge_supervision import bridge_limits
from .proof_contract_context_bridge import _DIGEST
from .proof_contract_payloads import closed


def probe_inputs(request, plan_id=None, terms=None, cached_result=None, *, checking=False):
    from ._proof_contract_probe_templates import validate_template

    if _planned_input_size([request, plan_id, terms, cached_result]) > MAX_BYTES:
        raise ValueError('aggregate application probe input exceeds 8 MiB')
    closed(request, {'repoRoot', 'context', 'left', 'right', 'template',
                     'deadlineMonotonic', 'limits'}, 'application probe request')
    if not isinstance(request['repoRoot'], str) or not request['repoRoot']:
        raise ValueError('probe requires a source repository path')
    deadline = request['deadlineMonotonic']
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError('application probe deadline must be finite')
    probe_context(request['context'])
    probe_side(request['left'])
    probe_side(request['right'])
    validate_template(request['template'])
    if checking:
        _check_terms(plan_id, terms, cached_result)
    supplied = request['limits']
    defaults = {'timeout_seconds': 30, 'max_output_bytes': MAX_BYTES,
                'max_rss_bytes': 12 * 1024**3}
    if not isinstance(supplied, dict) or not set(supplied) <= set(defaults):
        raise ValueError('invalid application probe limits')
    limits = bridge_limits({**defaults, **supplied})
    limits['max_output_bytes'] = min(MAX_BYTES, limits['max_output_bytes'])
    owned = copy.deepcopy(request)
    owned['limits'] = limits
    return owned


def _check_terms(plan_id, terms, cached_result):
    if not isinstance(plan_id, str) or not _DIGEST.fullmatch(plan_id):
        raise ValueError('application check requires an exact saved SHA-256 plan ID')
    if not isinstance(terms, dict) or not set(terms) <= {'formal-reading', 'probe'}:
        raise ValueError('terms may only name generated application-probe goals')
    for term in terms.values():
        if not isinstance(term, str) or not term.strip() or len(term.encode()) > 1024**2:
            raise ValueError('probe terms must be nonempty bounded strings')
    if cached_result is not None:
        _validate_cached_result(cached_result)


def _validate_cached_result(cached_result):
    if not isinstance(cached_result, dict):
        raise TypeError('invalid application probe result cache')
    schema = _cache_schema(cached_result)
    rows = _cache_rows(cached_result)
    seen = set()
    for entry in rows:
        _validate_cached_goal(entry, schema, seen)


def _cache_schema(cached_result):
    from .proof_contract_payloads import closed

    schema = cached_result.get('schema')
    if schema == 'ladon-application-probe-cache-v1':
        closed(cached_result, {'schema', 'planId', 'goals'}, 'application probe result cache')
        return schema
    if schema == 'ladon-application-probe-v1':
        if (not isinstance(cached_result.get('status'), str)
                or not isinstance(cached_result.get('checkerAuthority'), str)):
            raise ValueError('invalid prior application probe result')
        return schema
    raise ValueError('invalid application probe result cache schema')


def _cache_rows(cached_result):
    rows = cached_result.get('goals')
    plan_id = cached_result.get('planId')
    if (not isinstance(plan_id, str) or not _DIGEST.fullmatch(plan_id)
            or not isinstance(rows, list) or len(rows) > 2):
        raise ValueError('invalid application probe result cache identity')
    return rows


def _validate_cached_goal(entry, schema, seen):
    _closed_cache_goal(entry, schema)
    if not isinstance(entry, dict) or not _valid_cache_goal(entry, schema, seen):
        raise ValueError('invalid bounded cached application probe goal')
    _validate_cached_evidence(entry, schema)
    seen.add(entry['goalId'])


def _closed_cache_goal(entry, schema):
    if schema == 'ladon-application-probe-cache-v1':
        from .proof_contract_payloads import closed

        closed(entry, {'goalId', 'goalDigest', 'goal', 'term', 'termDigest', 'result'},
               'cached application probe goal')


def _valid_cache_goal(entry, schema, seen):
    if not isinstance(entry, dict):
        return False
    return (_valid_cache_identity(entry, seen)
            and _valid_cache_term(entry)
            and _valid_cache_schema_fields(entry, schema))


def _valid_cache_identity(entry, seen):
    return (entry.get('goalId') in {'formal-reading', 'probe'}
            and entry['goalId'] not in seen
            and isinstance(entry.get('goalDigest'), str)
            and _DIGEST.fullmatch(entry['goalDigest']) is not None
            and isinstance(entry.get('goal'), str) and bool(entry['goal']))


def _valid_cache_term(entry):
    term = entry.get('term')
    return (isinstance(term, str) and bool(term.strip())
            and len(term.encode()) <= 1024**2)


def _valid_cache_schema_fields(entry, schema):
    if schema == 'ladon-application-probe-cache-v1':
        digest = entry.get('termDigest')
        return isinstance(digest, str) and _DIGEST.fullmatch(digest) is not None
    return entry.get('status') == 'checked-support'


def _validate_cached_evidence(entry, schema):
    ref = entry.get('result')
    if (not isinstance(ref, dict) or ref.get('status') != 'supported'
            or not isinstance(ref.get('completion'), dict)
            or ref['completion'].get('status') != 'completed'
            or not isinstance(ref['completion'].get('termDigest'), str)
            or (schema == 'ladon-application-probe-cache-v1'
                and ref['completion']['termDigest'] != entry['termDigest'])):
        raise ValueError('cached application probe goal lacks matching checked evidence')
