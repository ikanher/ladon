"""Exercise ordinary index CLI on a disposable Lean source tree."""
from __future__ import annotations
import hashlib
import json
import os
import sqlite3
import subprocess
import tempfile
from pathlib import Path

CLI = Path(os.environ.get('LADON_CLI', str(Path(__file__).resolve().parents[5] / '.venv/bin/ladon')))

def call(repo: Path, args: list[str]) -> dict:
    command=[str(CLI),'proof-search',*args,'--repo-root',str(repo),'--format','json']
    run=subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False)
    if run.returncode:
        raise RuntimeError(f'{command}: {run.stderr}')
    result=json.loads(run.stdout)
    return {'args':args,'status':result.get('status'),'freshness':result.get('freshness'),'returned':result.get('returned'),'exact':result.get('matchSummary',{}).get('exactMatches'),'sourceChanges':result.get('sourceChanges',{}).get('counts'),'generationIdentity':result.get('generationIdentity'),'outputSha256':hashlib.sha256(run.stdout.encode()).hexdigest(),'payload':result}

with tempfile.TemporaryDirectory(prefix='ladon-active-index-smoke-') as raw:
    repo=Path(raw)
    (repo/'Main.lean').write_text('theorem oldLemma : True := True.intro\n')
    old=call(repo,['index','build'])
    (repo/'Fresh.lean').write_text('theorem newLemma : True := True.intro\n')
    miss=call(repo,['search','name','--text','newLemma'])
    status=call(repo,['index','status','--changed'])
    updated=call(repo,['index','update'])
    found=call(repo,['search','name','--text','newLemma'])
    clean=call(repo,['index','build','--index',str(repo/'clean.sqlite')])
    clean_found=call(repo,['search','name','--index',str(repo/'clean.sqlite'),'--text','newLemma'])
    (repo/'Fresh.lean').write_text('theorem newestLemma : True := True.intro\n')
    changed=call(repo,['index','status','--changed'])
    private=call(repo,['index','build','--index',str(repo/'.ladon/index/proof-search.agent.sqlite')])
    evidence=call(repo,['index','build','--index',str(repo/'.ladon/index/proof-search.evidence.sqlite')])
    evidence_path=repo/'.ladon/index/proof-search.evidence.sqlite'
    with sqlite3.connect(evidence_path) as connection:
        declaration=connection.execute('SELECT id FROM declarations LIMIT 1').fetchone()[0]
        connection.execute('INSERT INTO binders VALUES (?,?,?,?,?,?,?,?)',
                           (declaration,0,'h','explicit','True',1,'lexical','True'))
    evidence_hash=hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    listed=call(repo,['index','list'])
    preview=call(repo,['index','prune','--select','proof-search.agent.sqlite',
                       '--select','proof-search.evidence.sqlite'])
    protected=repo/'.ladon/index/proof-search.sqlite'
    protected_hash=hashlib.sha256(protected.read_bytes()).hexdigest()
    preview_path=repo/'preview.json'
    preview_path.write_text(json.dumps(preview['payload']))
    applied=call(repo,['index','prune','--apply','--preview-file',str(preview_path)])
    assert miss['exact']==0 and miss['freshness']=='stale-source'
    assert found['exact']==1 and found['freshness']=='fresh'
    assert updated['generationIdentity']==found['generationIdentity']
    assert clean['generationIdentity']==updated['generationIdentity']
    assert clean_found['payload']['results']==found['payload']['results']
    assert changed['sourceChanges']['changed']==1
    assert applied['payload']['reclaimedBytes']>0
    assert applied['payload']['reclaimedBytes']==preview['payload']['eligibleBytes']
    assert hashlib.sha256(protected.read_bytes()).hexdigest()==protected_hash
    assert hashlib.sha256(evidence_path.read_bytes()).hexdigest()==evidence_hash
    assert any(row['reason']=='retained-evidence:binders' for row in preview['payload']['rows'])
    assert (repo/'.ladon/index/proof-search.agent.sqlite.lock').exists()
    print(json.dumps({
        'runs': {name: {key:value for key,value in row.items() if key!='payload'} for name,row in locals().copy().items() if name in {'old','miss','status','updated','found','clean','clean_found','changed','private','evidence','listed','preview','applied'}},
        'protectedDefaultSha256':protected_hash,
        'protectedEvidenceSha256':evidence_hash,
        'previewEligibleBytes':preview['payload']['eligibleBytes'],
        'reclaimedBytes':applied['payload']['reclaimedBytes'],
        'cleanBuildRowsEqual':True,
    },indent=2))
