"""Development-only arithmetic endpoint classification comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

parser=argparse.ArgumentParser()
parser.add_argument('--implementation',required=True)
parser.add_argument('--output',required=True)
args=parser.parse_args()
root=Path.cwd()
sys.path.insert(0,str(root/'tests'))
import ladon
implementation=Path(args.implementation).resolve()
ladon.__path__.insert(0,str(implementation))
from ladon.proof_contract_obligation_planner import ContractObligationPlanRequest,plan_contract_obligations
from support.proof_contract_obligation_planner import request_kwargs
from test_proof_contract_obligation_planner_oracle import CASES,_case
rows=[]
for source,final,dependent in CASES:
    values=request_kwargs(_case(source,final,dependent))
    started=time.monotonic()
    result=plan_contract_obligations(ContractObligationPlanRequest(**values))
    described=next(row for row in result['routeComparisons'] if row['describedRoute'])
    actual=described['endpoint']['status']=='conditional-profile-support'
    expected=final<=3 and not dependent
    rows.append({'sourceLoss':source,'finalLoss':final,'dependent':dependent,'expectedSupport':expected,'actualSupport':actual,'endpointSupport':result['endpoint']['status'],'elapsedSeconds':time.monotonic()-started,'requestDigest':result['requestDigest'],'analysisId':result['analysisId']})
counts={'cases':len(rows),'correct':sum(r['actualSupport']==r['expectedSupport'] for r in rows),'truePositive':sum(r['actualSupport'] and r['expectedSupport'] for r in rows),'falsePositive':sum(r['actualSupport'] and not r['expectedSupport'] for r in rows),'trueNegative':sum(not r['actualSupport'] and not r['expectedSupport'] for r in rows),'falseNegative':sum(not r['actualSupport'] and r['expectedSupport'] for r in rows)}
paths=list((root/'src/ladon').rglob('*.py'))+list(implementation.glob('*planner*.py'))+[root/'tests/test_proof_contract_obligation_planner_oracle.py',root/'tests/support/proof_contract_obligation_planner.py',root/'tests/test_proof_contract_propagation.py',root/'tests/support/proofir_v3_native.py']
output={'schema':'ladon-conditional-method-oracle-v1','scope':'constructed-development-conditional-profile-only','implementation':str(implementation),'counts':counts,'rows':rows,'sourceHashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))},'limitations':['not-held-out','not-source-fidelity','not-mathematical-falsity','not-exposition-fault-detection','supplementary-reproduction-after-failing-pytest']}
Path(args.output).write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
print(json.dumps(counts,sort_keys=True))
