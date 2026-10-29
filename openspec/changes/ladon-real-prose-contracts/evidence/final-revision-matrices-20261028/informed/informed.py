"""Informed local integration only; no independent discovery credit."""
import copy
import json
import os
import sys
import tempfile
from pathlib import Path
from ladon.real_bound_native_production import produce_real_bound
from ladon.real_prose_native_production import produce_real_prose_bound
from ladon.real_prose_connection import connect_real_prose_bound

base = Path(__file__).resolve().parent
if os.environ.get('LADON_MATRIX_SCRATCH'):
    tempfile.tempdir = os.environ['LADON_MATRIX_SCRATCH']
mode = sys.argv[1]
formal_root = Path('.codex/state/navier-stokes-informed-diagnostic/formalization').resolve()
prose_root = Path('.codex/state/prose-observation-production/live/project').resolve()

def save(name,value):
    with (base/name).open('x') as stream: json.dump(value,stream,ensure_ascii=False)

if mode == 'formal':
    old = json.loads(Path('openspec/changes/ladon-real-bound-contracts/evidence/qualification-20261027/native/inverse_finiteJets-production.json').read_text())
    value = produce_real_bound(formal_root,old['request']['plan'],old['request']['terms'],timeout_seconds=600)
    save('FORMAL.json',value)
    print({'mode':mode,'status':value['status']},flush=True)
    assert value['status'] == 'admitted'
else:
    assert mode in {'five','four'}
    old = json.loads(Path('.codex/state/real-prose-native/live/navier-produced.json').read_text())
    request = copy.deepcopy(old['request'])
    if mode == 'five':
        request['interpretation']['id'] += ':five-order-control'
        request['interpretation']['symbols']['shift']['leanName'] = 'LadonSourcePair.shiftFive'
    authored = produce_real_prose_bound(prose_root,request['interpretation'],request['context'],
        alternative_id='informed:'+mode,author='informed-integration',timeout_seconds=120)
    save(mode+'-AUTHORED.json',authored)
    assert authored['status'] == 'authored',authored['check'].get('diagnostic')
    formal = json.loads((base/'FORMAL.json').read_text())
    term = json.loads(Path('.codex/state/real-prose-connection/probe-five.json').read_text())['term']
    connection = {'schema':'ladon-real-prose-connection-request-v1','term':term,'premises':[]}
    save(mode+'-REQUEST.json',connection)
    value = connect_real_prose_bound(formal,authored,formal_root,prose_root,connection,timeout_seconds=550)
    save(mode+'-CONNECTION.json',value)
    print({'mode':mode,'status':value['status'],'diagnostic':value['check']['diagnostic']},flush=True)
    assert value['status'] == ('connected' if mode == 'five' else 'unresolved')
    assert value['mathematicalFalsity'] == 'not-established'
