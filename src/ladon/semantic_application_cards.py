"""Small mathematical views of owned versioned application observations."""
from __future__ import annotations

from collections.abc import Mapping

from ladon.semantic_projection_core import bounded_text, omit


def application_context_cards(check, projection, omissions, pointer):
    rows = check.get('residualContexts')
    if not isinstance(rows, list):
        omit(omissions, pointer, 'canonical-field-unavailable', 1)
        return None
    limit = 4 if projection == 'llm' else 6
    cards = []
    for ordinal, row in enumerate(rows[:limit]):
        cards.append({'residualOrdinal': ordinal,
                      'goalId': bounded_text(row['goalId'], 128, omissions, f'{pointer}/{ordinal}/goalId'),
                      'localContext': _local_cards(row['localContext'], limit, omissions, f'{pointer}/{ordinal}/localContext')})
    _collection_omission(rows, limit, omissions, pointer)
    return cards


def selected_declaration_card(selected, projection, omissions, pointer):
    if not isinstance(selected, Mapping):
        omit(omissions, pointer, 'canonical-field-unavailable', 1)
        return None
    limit = 4 if projection == 'llm' else 6
    omit(omissions, pointer + '/typeStructural', 'structural-evidence-omitted', 1)
    return {'name': bounded_text(selected['name'], 256, omissions, pointer + '/name'),
            'typeDisplay': bounded_text(selected['typeDisplay'], 512, omissions, pointer + '/typeDisplay'),
            'binders': _local_cards(selected['binders'], limit, omissions, pointer + '/binders')}


def _local_cards(rows, limit, omissions, pointer):
    cards = []
    for index, row in enumerate(rows[:limit]):
        card = {field: bounded_text(row[field], bound, omissions, f'{pointer}/{index}/{field}')
                for field, bound in [('localId', 128), ('userName', 96), ('binderInfo', 48), ('typeDisplay', 256)]}
        if row['valueDisplay']:
            card['valueDisplay'] = bounded_text(row['valueDisplay'], 256, omissions, f'{pointer}/{index}/valueDisplay')
        if row['dependencies']:
            card['dependencies'] = [bounded_text(value, 128, omissions, f'{pointer}/{index}/dependencies/{i}')
                                    for i, value in enumerate(row['dependencies'][:limit])]
            _collection_omission(row['dependencies'], limit, omissions, f'{pointer}/{index}/dependencies')
        cards.append(card)
    # Structural type/value bodies and origins are available from the exact owner.
    if rows:
        omit(omissions, pointer, 'compact-local-fields-omitted', min(len(rows), limit) * 3)
    _collection_omission(rows, limit, omissions, pointer)
    return cards


def _collection_omission(rows, limit, omissions, pointer):
    if len(rows) > limit:
        omit(omissions, pointer, 'projection-collection-limit', len(rows) - limit)
