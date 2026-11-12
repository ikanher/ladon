"""Checks for this authored development corpus; not a general prose translator."""
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from unittest.mock import patch
import check_isolation as iso
ROOT = Path(__file__).resolve().parents[1]

def declarations(path):
    ns, result = [], set()
    for line in path.read_text().splitlines():
        if m := re.match(r'namespace (\S+)', line): ns.append(m[1])
        elif re.match(r'end(?:\s|$)', line):
            if ns: ns.pop()
        elif m := re.match(r'(?:noncomputable )?(?:def|theorem|axiom|class) (\w+)', line): result.add('.'.join([*ns, m[1]]))
    return result

def validate(data):
    cases = data['cases']
    assert len(cases) == len({c['caseId'] for c in cases}) == 24
    for family in {c['family'] for c in cases}:
        rows=[c for c in cases if c['family']==family]
        assert len(rows)==4 and sum(c['role']=='fault' for c in rows)==sum(c['role']=='control' for c in rows)==2
    for c in cases:
        goal, span = c['comparisonGoal'], c['sourceSpan']
        assert goal['formalDeclaration']==c['leanSource'] and goal['sourceSpan']==span
        text=(ROOT/c['sourcePath']).read_text(); quote=c['sourceQuote']
        assert text.count(quote)==1 and span['startLine']==span['endLine']
        assert text.splitlines()[span['startLine']-1][span['startColumn']:span['endColumn']]==quote
        assert hashlib.sha256(quote.encode()).hexdigest()==span['quoteSha256']
        assert hashlib.sha256(text.encode()).hexdigest()==span['sourceFileSha256']
        refs=[c['leanSource'],*c.get('evidenceSources',[])]
        if c.get('oracleSource'): refs.append(c['oracleSource'])
        for ref in refs:
            file,symbol=ref.split('#'); assert symbol in declarations(ROOT/file),ref
        if c['caseId']=='domain-quantifier-01':
            assert quote=='One bound works for every natural number.'
            assert goal['sourceClaim']==goal['formalClaim']=='∃ k : Nat, ∀ n : Nat, n < k'
            assert 'refutes' in goal['obligation'] and 'pointwise' not in goal['obligation']

def must_fail(fn,label):
    try: fn()
    except (AssertionError,RuntimeError): print('PASS countercheck:',label)
    else: raise AssertionError('countercheck accepted: '+label)

def main():
    data=json.loads((ROOT/'cases.json').read_text()); validate(data)
    print('PASS 24 corpus bindings, spans, role counts and named evidence locators')
    changed=copy.deepcopy(data); changed['cases'][0]['comparisonGoal']['sourceClaim']='∀ n : Nat, ∃ k : Nat, n < k'
    must_fail(lambda: validate(changed),'wrong quantifiers with unchanged source span')
    changed=copy.deepcopy(data); changed['cases'][0]['evidenceSources'].append('lean/Pitfalls.lean#removed_helper')
    must_fail(lambda: validate(changed),'stale evidence locator')
    for code,message in [(1,'fatal: out of memory'),(-9,''),(1,'Probe.lean:1:0: error: unknown identifier Foo'),(1,"Probe.lean:1:0: error: unknown module prefix 'Other'")]:
        must_fail(lambda: iso.classify_probe('Validation',False,subprocess.CompletedProcess([],code,message,'')),repr((code,message)))
    missing = "Probe.lean:1:0: error: unknown module prefix 'Validation'\n\nNo directory 'Validation' or file 'Validation.olean' in the search path entries:\n/tmp/overlay\n"
    assert iso.classify_probe('Validation',False,subprocess.CompletedProcess([],1,missing,''))=='module-unavailable'
    for extra in ['fatal: out of memory\n', 'Killed\n', 'unrelated failure\n']:
        must_fail(lambda: iso.classify_probe('Validation',False,subprocess.CompletedProcess([],1,missing+extra,'')), 'missing-module diagnostic plus '+extra.strip())
    must_fail(lambda: iso.classify_probe('Validation',False,subprocess.CompletedProcess([],0,'','')),'successful forbidden import')
    real_copy=iso.shutil.copy2; project=ROOT/'lean'
    source=project/'.lake/build/lib/lean/CoreCases/domain_quantifier_02.olean'
    def contaminated_copy(src,dst):
        result=real_copy(src,dst)
        if Path(dst).name=='Pitfalls.olean':
            dest=Path(dst).parent/'CoreCases/domain_quantifier_02.olean'; dest.parent.mkdir(parents=True,exist_ok=True); real_copy(source,dest)
        return result
    with patch.object(iso.shutil,'copy2',side_effect=contaminated_copy):
        must_fail(lambda: iso.env_for(project,'Pitfalls',data['cases'][0],data['cases'][1]),'actual exposed sibling module')

if __name__=='__main__': main()
