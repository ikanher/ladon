"""Bounded large-contract identity-chain resource probe; no Lean."""
from copy import deepcopy
from pathlib import Path
import json
import sys
import time

sys.path.insert(0,str(Path.cwd()/'tests'))
import ladon
ladon.__path__.insert(0,str(Path(sys.argv[1]).resolve()))
from support.proofir_v3_native import ENVIRONMENT,envelope,ref
from support.proof_contract_obligation_planner import request_kwargs
from test_proof_contract_propagation import _contract,_derivation,_step,_scope,_interface,_binding
from ladon.proof_contract_obligation_planner import ContractObligationPlanRequest,plan_contract_obligations
source=_contract('large-source',offset=3,dependencies=())
payload=deepcopy(source['payload']); record=payload['record']
universals=[f'u{i}:'+('x'*490) for i in range(64)]
existentials=[f'w{i}' for i in range(64)]
record['telescope']=[{'binderId':b,'typeId':'Nat','quantifier':'forall'} for b in universals]+[{'binderId':b,'typeId':'Nat','quantifier':'exists'} for b in existentials]
record['features']['witnessDependencies']=[{'binderId':b,'state':'known','allowedBinderIds':[],'reason':None} for b in existentials]
source=envelope('proofir.contract',payload,source['subjectRefs'],environment=ENVIRONMENT)
desired=deepcopy(record)
for row in desired['features']['witnessDependencies']: row['allowedBinderIds']=list(universals)
steps=[]; parent='large-source'
for i in range(60):
    output='goal' if i==59 else f'large-mid:{i}'
    steps.append(_step(f'large:{i}',[parent],output));parent=output
scope=_scope(source,statement='large-source');scope['binderMap']=[{'fromBinderId':b,'toBinderId':b} for b in universals+existentials]
case={'graph':_derivation(steps),'artifacts':[source],'interfaces':[_interface('out'),_interface('in',contract=source)],'scopes':[scope],'bindings':[_binding(s) for s in steps],'steps':steps,'routeASteps':[s['stepRef'] for s in steps],'desired':desired,'goalRef':ref('statement','goal')}
values=request_kwargs(case)
print(json.dumps({'inputBytes':len(json.dumps(values,separators=(',',':')).encode()),'desiredBytes':len(json.dumps(desired,separators=(',',':')).encode())}),flush=True)
t=time.monotonic();result=plan_contract_obligations(ContractObligationPlanRequest(**values))
print(json.dumps({'status':result['status'],'elapsedSeconds':time.monotonic()-t,'outputBytes':len(json.dumps(result,separators=(',',':')).encode()),'routes':len(result['routeComparisons']),'work':result['coverage']['workBudget']}),flush=True)
