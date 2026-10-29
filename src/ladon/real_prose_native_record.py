"""Closed attributed Real features reconstructed from exact recognition history."""

from copy import deepcopy

from ladon.proof_contract_payloads import identifier
from ladon.real_prose_inputs import observation_identity

PROFILE_ID = 'real-bound-prose-v1'
PROFILE = {'profileId': PROFILE_ID, 'version': 1, 'meaning': 'attributed typed bound skeleton',
           'authority': 'none', 'admission': 'unresolved', 'fidelity': 'attributed-unreviewed'}
PROFILE_DIGEST = observation_identity(PROFILE)


def expression_subject(expression):
    digest = observation_identity({'expression': expression})
    return {'kind': 'expression', 'localId': 'expr:' + digest[7:],
            'fingerprint': {'scheme': {'name': 'ladon-authored-bound-expression', 'version': '1'},
                            'digest': digest}}


def build_record(recognition, interpretation_ref, source_ref, *, alternative_id, author):
    identifier(alternative_id, 'alternative ID')
    identifier(author, 'author')
    inner = recognition['check']['result']
    shape = inner['features']['candidate']
    subjects = {}

    def expression(value):
        descriptor = expression_subject(value)
        subjects[descriptor['localId']] = descriptor
        return {key: descriptor[key] for key in ('kind', 'localId')}

    telescope = [{**{key: value for key, value in row.items() if key != 'type'},
                  'typeRef': expression(row['type'])} for row in shape['telescope']]
    application = {'predicateRef': expression(shape['input']['predicate']),
                   'operatorRef': expression(shape['operator'])}
    fields = ['function', 'order', 'bound']
    if shape['scope']['kind'] == 'set-indexed':
        fields.insert(1, 'set')
    for side in ('input', 'output'):
        application[side] = {key + 'Ref': expression(shape[side][key]) for key in fields}
    observation = inner['observation']
    record = {'schema': 'ladon-authored-real-bound-record-v1', 'profileId': PROFILE_ID,
              'alternativeId': alternative_id, 'author': author,
              'source': {'interpretationRef': deepcopy(interpretation_ref), 'sourceMapRef': deepcopy(source_ref),
                         'recognitionId': recognition['snapshotId'], 'observationId': observation['snapshotId'],
                         'context': deepcopy(recognition['request']['context'])},
              'scope': deepcopy(shape['scope']), 'telescope': telescope,
              'roles': deepcopy(shape['roles']), 'application': application,
              'loss': shape['loss'], 'constant': deepcopy(shape['constant']),
              'guards': {'constantNonnegativeRef': expression(shape['guards']['constantNonnegative']['expression']),
                         'boundNonnegativeBinderIds': deepcopy(shape['guards']['boundNonnegativeBinderIds'])},
              'origins': {**{side: shape[side]['originPath'] for side in ('input', 'output')},
                          'constantGuard': shape['guards']['constantNonnegative']['originPath']},
              'admission': 'unresolved'}
    return record, list(subjects.values())


def contract_id(recognition, alternative_id, author):
    digest = observation_identity({'recognitionId': recognition['snapshotId'],
                                   'alternativeId': alternative_id, 'author': author})
    return 'contract:' + digest[7:]
