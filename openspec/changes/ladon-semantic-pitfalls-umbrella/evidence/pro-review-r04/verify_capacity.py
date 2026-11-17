#!/usr/bin/env python3
'''Bounded review probes using exact r04 source definitions.

This is not the Ladon runtime or a Lean replay. Missing package dependencies are
not mocked into successful validators. Only the canonical bounds/encoding/hash
functions are loaded, plus exact diagnostic return expressions and the artifact
producer prefix needed to demonstrate its failure before artifact construction.
'''

from __future__ import annotations

import ast
import copy
import dataclasses
import hashlib
import json
import math
import sys
import types
from decimal import Decimal
from pathlib import Path


PACKET = Path(__file__).resolve().parents[2] / 'ladon-semantic-strategy-review-data-r04'
SRC = PACKET / 'sources/src/ladon'
NATIVE = PACKET / 'sources/openspec/changes/ladon-proofir-correspondence-context/evidence/mf-native-r01'
OUT = Path(__file__).with_name('verification-results.json')
RESULTS = {'scope': 'isolated exact-source Python verification; no Lean replay or full runtime tests',
           'checks': [], 'diagnostic_probes': [], 'source_hashes': {}}


def load_definitions(filename, names, namespace):
    path = SRC / filename
    raw = path.read_bytes()
    RESULTS['source_hashes'][filename] = hashlib.sha256(raw).hexdigest()
    tree = ast.parse(raw, filename=str(path))
    selected = [node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    assert {node.name for node in selected} == set(names)
    module = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0),
                             *selected], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), 'exec'), namespace)


def record(label, predicate):
    assert predicate, label
    RESULTS['checks'].append({'name': label, 'result': 'passed'})


def rejects(label, value, expected, **kwargs):
    try:
        canonical(value, **kwargs)
    except Error as error:
        record(label, expected in str(error))
    else:
        raise AssertionError(f'{label}: unexpectedly accepted')


module = types.ModuleType('review_exact_canonical')
sys.modules[module.__name__] = module
ns = module.__dict__
ns.update(copy=copy, hashlib=hashlib, json=json, math=math, dataclass=dataclasses.dataclass,
          Decimal=Decimal)
constant_names = {'PROOFIR_V3_VERSION', 'SAFE_INTEGER_MIN', 'SAFE_INTEGER_MAX',
                  'MAX_ARTIFACT_BYTES', 'MAX_CANONICAL_BYTES', 'MAX_DEPTH',
                  'MAX_COLLECTION_ITEMS', 'MAX_COMPILED_MODULES', 'MAX_STRING_BYTES'}
constants = [node for node in ast.parse((SRC / 'proofir_v3.py').read_text()).body
             if isinstance(node, ast.Assign) and len(node.targets) == 1
             and isinstance(node.targets[0], ast.Name) and node.targets[0].id in constant_names]
assert {node.targets[0].id for node in constants} == constant_names
exec(compile(ast.Module(body=constants, type_ignores=[]), str(SRC / 'proofir_v3.py'), 'exec'), ns)
load_definitions('proofir_v3.py', {
    'ProofIRV3Diagnostic', 'ProofIRV3Error', 'canonical_bytes', '_validate_bounds',
    '_validate_string_bound', '_validate_integer_bound', '_reject_float', '_validate_list_bounds',
    '_validate_object_bounds', '_slice_module_paths', '_receipt_module_paths',
    '_is_environment_manifest', '_is_environment_envelope', 'detached_content_id'}, ns)
load_definitions('proofir_correspondence.py', {'_as_exact_decimal_strings'}, ns)
load_definitions('correspondence_evidence.py', {'_hash', '_accepted', '_subject_mismatch_diagnostics',
                                             '_row_artifacts'}, ns)
canonical, Error, row_hash = ns['canonical_bytes'], ns['ProofIRV3Error'], ns['_hash']


def envelope(count):
    return {'proofirVersion': '3.0', 'artifactKind': 'proofir.correspondence', 'payload': {
        'slice': {'schema': 'ladon-proof-slice-v1',
                  'observation': {'importedModules': [f'M{i}' for i in range(count)]},
                  'compiledInventory': {'modules': [{'module': f'M{i}'} for i in range(count)]}}}}


def receipt(count):
    return {'goalOrigin': 'generated-correspondence-obligation',
            'capture': {'schema': 'ladon-source-goal-capture-result-v1',
                        'operation': 'capture-source-goal', 'capture': {'environment': {
                            'compiledInventory': {'modules': [{'module': f'M{i}'} for i in range(count)]}}}}}


def reference(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


for count in [0, 10000, 10001, 32768]:
    value = envelope(count)
    record(f'envelope count {count}: unchanged canonical bytes', canonical(value) == reference(value))
    selected = value['payload']['slice']
    record(f'standalone slice count {count}: unchanged canonical bytes', canonical(selected) == reference(selected))
    for wrapped in [False, True]:
        value = receipt(count)
        if wrapped:
            value = {'planId': 'p', 'receipt': value}
        record(f'receipt count {count}, wrapped={wrapped}: unchanged hash',
               row_hash(value) == 'sha256:' + hashlib.sha256(reference(value)).hexdigest())

for location in ['observation', 'compiledInventory']:
    value = envelope(0)
    field = 'importedModules' if location == 'observation' else 'modules'
    value['payload']['slice'][location][field] = [None] * 32769
    rejects(f'{location}: upper cap', value, 'collection exceeds item limit: 32768')
rejects('receipt: upper cap', receipt(32769), 'collection exceeds item limit: 32768')

for location in ['nested', 'extension', 'wrong-kind', 'wrong-schema', 'other-list', 'row']:
    value = envelope(10001)
    if location == 'nested':
        value = {'unrelated': value}
    elif location == 'extension':
        value['extensions'] = {'slice': value['payload'].pop('slice')}
    elif location == 'wrong-kind':
        value['artifactKind'] = 'proofir.observation'
    elif location == 'wrong-schema':
        value['payload']['slice']['schema'] = 'unknown'
    elif location == 'other-list':
        value = envelope(0)
        value['payload']['slice']['observation']['applications'] = [None] * 10001
    else:
        value = envelope(0)
        value['payload']['slice']['compiledInventory']['modules'] = [{'nested': [None] * 10001}]
    rejects(f'slice path isolation: {location}', value, 'collection exceeds item limit: 10000')

for mutation in ['nested', 'wrong-origin', 'wrong-schema', 'wrong-operation', 'row', 'extra-wrapper']:
    value = receipt(10001)
    if mutation == 'nested':
        value = {'unrelated': value}
    elif mutation == 'wrong-origin':
        value['goalOrigin'] = 'unknown'
    elif mutation in {'wrong-schema', 'wrong-operation'}:
        value['capture'][mutation.removeprefix('wrong-')] = 'unknown'
    elif mutation == 'row':
        value = receipt(1)
        value['capture']['capture']['environment']['compiledInventory']['modules'][0]['other'] = [None] * 10001
    else:
        value = {'planId': 'p', 'receipt': value, 'unrelated': True}
    rejects(f'receipt path isolation: {mutation}', value, 'collection exceeds item limit: 10000')
rejects('byte cap remains in force', envelope(10001), 'canonical payload exceeds byte limit', max_bytes=1024)
rejects('ordinary collection unchanged', {'items': [None] * 10001}, 'collection exceeds item limit: 10000')
rejects('unicode string cap remains in force', {'text': 'é' * 600000}, 'string exceeds byte limit')
rejects('object cardinality cap remains in force', {str(i): None for i in range(10001)}, 'object exceeds item limit')
deep = None
for _ in range(65):
    deep = [deep]
rejects('depth cap remains in force', deep, 'canonical payload exceeds nesting limit')
rejects('boolean byte allowance rejected', {}, 'invalid canonical byte bound', max_bytes=True)

for case in ['fdp', 'adam']:
    bundle = json.loads((NATIVE / case / 'checked-1800-r02.json').read_text())
    for index, artifact in enumerate(bundle['artifacts']):
        record(f'{case} native artifact {index}: canonical content id',
               ns['detached_content_id'](artifact) == artifact['artifactId'])
    record(f'{case}: standalone slice canonicalization',
           canonical(ns['_as_exact_decimal_strings'](bundle['plan']['slice'])) ==
           reference(ns['_as_exact_decimal_strings'](bundle['plan']['slice'])))
    checks = {artifact['artifactId']: artifact for artifact in bundle['artifacts']
              if artifact['artifactKind'] == 'proofir.check-run'}
    for row, ref in zip(bundle['checks'], bundle['checkRunRefs'], strict=True):
        retained = checks[ref['artifactRef']]['extensions']['ladon.correspondence-receipt/v1']
        record(f'{case} {row["obligation"]}: retained receipt hash', row_hash(row) == retained['receiptDigest'])

# Evaluate the exact source return expressions, constructing the diagnostic
# state deliberately. This verifies error serialization, not native reachability.
check_source = (SRC / 'correspondence_check.py').read_bytes()
RESULTS['source_hashes']['correspondence_check.py'] = hashlib.sha256(check_source).hexdigest()
tree = ast.parse(check_source)
goal_function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_check_goal')
for code in ['prepared-goal-subject-mismatch', 'unexpected-generated-goal-context']:
    ret = next(node for node in ast.walk(goal_function) if isinstance(node, ast.Return)
               and any(isinstance(c, ast.Constant) and c.value == code for c in ast.walk(node)))
    fixture = copy.deepcopy(bundle['checks'][0])
    fixture['capture']['capture']['environment']['compiledInventory']['modules'] = [
        {'module': f'M{i}'} for i in range(10001)]
    typed = dataclasses.make_dataclass('TypedFixture', [(key, object) for key in fixture['typecheck']])(
        **fixture['typecheck'])
    checked = eval(compile(ast.Expression(body=ret.value), str(SRC / 'correspondence_check.py'), 'eval'),
                   {'capture': fixture['capture'], 'typed': typed, 'typed_subject': fixture['typedSubject']})
    row = {'obligation': fixture['obligation'], 'mode': fixture['mode'], 'goal': fixture['goal'], **checked}
    probe = {'diagnostic': code, 'constructed_state': True, 'native_execution_claimed': False,
             'return_expression_source_line': ret.lineno, 'goalOrigin_present': 'goalOrigin' in row,
             'inventory_count': 10001}
    try:
        ns['_row_artifacts'](bundle['plan'], row, bundle['implementationDigest'])
    except Error as error:
        probe['artifact_production_error'] = str(error)
        record(f'{code}: unresolved artifact production fails at old generic cap',
               str(error) == 'collection exceeds item limit: 10000')
    else:
        raise AssertionError(f'{code}: expected large diagnostic serialization failure')
    retained_row = copy.deepcopy(row)
    retained_row['capture'] = copy.deepcopy(bundle['checks'][0]['capture'])
    probe['retained_capture_inventory_count'] = len(
        retained_row['capture']['capture']['environment']['compiledInventory']['modules'])
    try:
        ns['_row_artifacts'](bundle['plan'], retained_row, bundle['implementationDigest'])
    except Error as error:
        probe['retained_capture_hash_error'] = str(error)
        record(f'{code}: unchanged retained capture also exceeds generic hash cap',
               str(error) == 'collection exceeds item limit: 10000')
    else:
        raise AssertionError(f'{code}: unchanged retained capture unexpectedly hashed')
    for count in [10000, 10001]:
        candidate = copy.deepcopy(row)
        candidate['capture']['capture']['environment']['compiledInventory']['modules'] = [
            {'module': f'M{i}'} for i in range(count)]
        if count == 10000:
            record(f'{code}: same diagnostic below generic cap hashes', bool(row_hash(candidate)))
        else:
            candidate['goalOrigin'] = 'generated-correspondence-obligation'
            record(f'{code}: retained exact origin marker allows large diagnostic hash', bool(row_hash(candidate)))
    RESULTS['diagnostic_probes'].append(probe)

RESULTS['passed_check_count'] = len(RESULTS['checks'])
OUT.write_text(json.dumps(RESULTS, indent=2) + '\n')
print(json.dumps({'passed_check_count': RESULTS['passed_check_count'],
                  'diagnostic_probes': RESULTS['diagnostic_probes'], 'results': str(OUT)}, indent=2))
