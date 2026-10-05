"""Deterministic bounded result pages with input-bound continuation."""
from __future__ import annotations

import base64
import hashlib
import json

from ladon.result_manifest_io import MAX_RESULT_BYTES, ResultManifestError, canonical_json


class InspectionRowOverflow(ResultManifestError):
    """A valid projected row cannot fit within the available byte budget."""


def inspection_digest(value):
    """Identify supplied data, not producer authenticity."""
    return 'sha256:' + hashlib.sha256(canonical_json(value)).hexdigest()


def text_projection(result):
    """Keep every section in the same projection as JSON."""
    return '\n'.join(f'{key}: {canonical_json(value).decode()}' for key, value in result.items())


def _fits(result):
    return max(len(canonical_json(result)), len(text_projection(result).encode())) + 1 <= MAX_RESULT_BYTES


def inspect_page(result, rows, binding, limit, cursor):
    """Fit rows and framing before publishing a continuation offset."""
    offset = _offset(cursor, binding, len(rows))
    result['rows'] = []
    for index in range(offset, min(len(rows), offset + limit)):
        if result.get('section') == 'exposition':
            if not _append_exposition_row(result, rows[index], len(rows), offset, binding):
                break
        else:
            candidate = compact_row(rows[index])
            result['rows'].append(candidate)
            _pagination(result, len(rows), offset, binding)
            if not _fits(result):
                result['rows'].pop()
                break
    _pagination(result, len(rows), offset, binding)
    if (offset < len(rows) and not result['rows']) or not _fits(result):
        raise ResultManifestError('inspection metadata exceeds compact byte limit')
    return result


def _append_exposition_row(result, row, total, offset, binding):
    for text_limit, list_limit in ((2048, 10), (512, 3), (128, 1)):
        candidate = _compact_exposition_level(row, text_limit, list_limit)
        if candidate is None:
            continue
        result['rows'].append(candidate)
        _pagination(result, total, offset, binding)
        if _fits(result):
            return True
        result['rows'].pop()
    return False


def _compact_exposition_level(row, text_limit, list_limit):
    try:
        return compact_row(row, profile='exposition',
                           text_limit=text_limit, list_limit=list_limit)
    except InspectionRowOverflow:
        return None


def _pagination(result, total, offset, binding):
    count = len(result['rows'])
    end = offset + count
    result['pagination'] = {'total': total, 'returned': count, 'omitted': total - end,
                            'offset': offset, 'nextCursor': _cursor(binding, end) if end < total else None}


def _cursor(binding, offset):
    body = canonical_json({'binding': binding, 'offset': offset})
    encoded = base64.urlsafe_b64encode(body).decode().rstrip('=')
    return encoded + '.' + hashlib.sha256(body).hexdigest()


def _offset(cursor, binding, total):
    if cursor is None:
        return 0
    try:
        if not isinstance(cursor, str) or len(cursor) > 1024:
            raise ValueError('invalid cursor type or size')
        encoded, _ = cursor.split('.')
        raw = base64.b64decode(encoded + '=' * (-len(encoded) % 4), altchars=b'-_', validate=True)
        value = json.loads(raw)
        offset = value['offset']
        if (type(offset) is not int or not 0 < offset < total
                or value != {'binding': binding, 'offset': offset}
                or cursor != _cursor(binding, offset)):
            raise ValueError('cursor inputs or query changed')
        return offset
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise ResultManifestError('invalid or stale inspection cursor') from exc


def compact_row(row, *, profile='default', text_limit=None, list_limit=None):
    """Bound a row, keeping focused exposition prose ahead of repeated records."""
    from ladon.result_exposition_page import focused_exposition_row
    source = focused_exposition_row(row) if profile == 'exposition' else row
    references = row.get('references', {})
    levels = ((text_limit, list_limit),) if text_limit is not None else (
        (2048, 10), (512, 3), (128, 1),
    )
    priorities = _exposition_priorities() if profile == 'exposition' else frozenset()
    for candidate_text_limit, candidate_list_limit in levels:
        omissions = list(source.get('fieldOmissions', [])) if profile == 'exposition' else []
        value = _compact(source, '', references, omissions,
                         candidate_text_limit, candidate_list_limit,
                         excerpt_types=profile == 'exposition', priority_paths=priorities)
        if omissions:
            value['fieldOmissions'] = omissions
        if len(canonical_json(value)) < 24 * 1024:
            return value
    raise InspectionRowOverflow('inspection row metadata exceeds compact byte limit')


def _exposition_priorities():
    return frozenset({
        '/paragraph/explanation', '/paragraph/purpose', '/reviews/0/rationale',
        '/selectedComponent/componentId',
        '/selectedComponent/claimComponentCoverage/components',
    })


def _compact(value, path, references, omissions, text_limit, list_limit, *,
             excerpt_types=False, priority_paths=frozenset()):
    if _is_priority(path, value, priority_paths):
        return value
    if isinstance(value, str):
        return _compact_text(value, path, references, omissions, text_limit, excerpt_types)
    if isinstance(value, list):
        return _compact_list(value, path, references, omissions, text_limit, list_limit,
                             excerpt_types, priority_paths)
    if isinstance(value, dict):
        return _compact_mapping(value, path, references, omissions, text_limit, list_limit,
                                excerpt_types, priority_paths)
    return value


def _is_priority(path, value, priorities):
    return path in priorities and (not isinstance(value, str) or len(value.encode()) <= 512)


def _compact_text(value, path, references, omissions, text_limit, excerpt_types):
    if len(value.encode()) <= text_limit:
        return value
    kept = value.encode()[:text_limit].decode('utf-8', errors='ignore')
    reference = _reference(path, references)
    omitted_bytes = len(value.encode()) - len(kept.encode())
    if excerpt_types and path.endswith('/typeText'):
        kept = ('EXCERPT. Route template: ladon result inspect INPUT --section targets '
                '--target TARGET_ID --format json. Replace INPUT with the supplied '
                'manifest or bundle and TARGET_ID with the shown targetId. Complete '
                'text: the exact input/pointer in fieldOmissions.\n' + kept)
    omissions.append({'path': path, 'omittedBytes': omitted_bytes, 'reference': reference})
    return kept


def _compact_list(value, path, references, omissions, text_limit, list_limit,
                  excerpt_types, priority_paths):
    if len(value) > list_limit:
        omissions.append({'path': path, 'omittedRows': len(value) - list_limit,
                          'reference': _reference(path, references)})
    return [_compact(item, f'{path}/{index}', references, omissions, text_limit, list_limit,
                     excerpt_types=excerpt_types, priority_paths=priority_paths)
            for index, item in enumerate(value[:list_limit])]


def _compact_mapping(value, path, references, omissions, text_limit, list_limit,
                     excerpt_types, priority_paths):
    nested = {**references, **{path + key: ref for key, ref in value.get('references', {}).items()}}
    return {key: (child if key == 'references' else
                  _compact(child, f'{path}/{_escape(key)}', nested, omissions, text_limit, list_limit,
                           excerpt_types=excerpt_types, priority_paths=priority_paths))
            for key, child in value.items()}


def _reference(path, references):
    parents = [key for key in references if path == key or path.startswith(key + '/')]
    if not parents:
        return references.get('', {'reason': 'projection metadata'})
    prefix = max(parents, key=len)
    reference = dict(references[prefix])
    if reference.pop('appendPath', True):
        reference['pointer'] += path[len(prefix):]
    return reference


def _escape(value):
    return value.replace('~', '~0').replace('/', '~1')
