"""Frozen-input alternating full-build/update pilot; no external repository writes."""
from __future__ import annotations
import hashlib
import json
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CLI = ROOT / '.venv/bin/ladon'
MODULES = 2000
DECLS = 10
SAMPLES = 5

def directory_bytes(directory: Path) -> int:
    total = 0
    for path in directory.iterdir():
        try:
            total += path.stat().st_size
        except FileNotFoundError:
            # SQLite may remove a journal between directory listing and stat.
            continue
    return total

def run(args: list[str], cwd: Path, *, executable: Path = CLI) -> dict:
    stamp = time.perf_counter()
    measured = subprocess.Popen(['/usr/bin/time', '-f', 'MEASURED cpu_user=%U cpu_sys=%S peak_rss_kib=%M', str(executable), *args], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    peak_disk = 0
    directory = cwd / '.ladon/index'
    while measured.poll() is None:
        if directory.exists():
            peak_disk = max(peak_disk, directory_bytes(directory))
        time.sleep(0.01)
    stdout, stderr = measured.communicate()
    if measured.returncode:
        raise RuntimeError(f'{args}: {stderr[-3000:]}')
    if directory.exists():
        peak_disk = max(peak_disk, directory_bytes(directory))
    payload = json.loads(stdout)
    row = {'wallSeconds': round(time.perf_counter()-stamp, 6), 'resultHash': hashlib.sha256(stdout.encode()).hexdigest(), 'outputBytes': len(stdout.encode()), 'databaseBytes': payload.get('databaseBytes'), 'identity': payload.get('generationIdentity'), 'reused': payload.get('reusedModules'), 'extracted': payload.get('extractedModules'), 'temporaryDiskPeakBytes': peak_disk}
    row.update(dict(field.split('=',1) for field in stderr.split('MEASURED ')[-1].strip().split()))
    return row

with tempfile.TemporaryDirectory(prefix='ladon-index-update-r01-') as raw:
    repo=Path(raw)
    for ordinal in range(MODULES):
        (repo/f'M{ordinal:04d}.lean').write_text('\n'.join(f'theorem lemma_{ordinal}_{j} : True := True.intro' for j in range(DECLS))+'\n')
    base = run(['proof-search','index','build','--repo-root',str(repo),'--format','json'], repo)
    snapshot_code = 'import json,sys;from pathlib import Path;from ladon.proof_search_index import capture_repository_snapshot;s=capture_repository_snapshot(Path(sys.argv[1]));print(json.dumps({"generationIdentity":s.generation_identity}))'
    source_snapshot = run(['-c',snapshot_code,str(repo)],repo,executable=ROOT/'.venv/bin/python')
    source_status = run(['proof-search','index','status','--repo-root',str(repo),'--format','json'],repo)
    query_baseline = run(['proof-search','search','name','--repo-root',str(repo),'--text','lemma_0000_0','--format','json'],repo)
    private = run(['proof-search','index','build','--repo-root',str(repo),'--index',str(repo/'.ladon/index/proof-search.private.sqlite'),'--format','json'],repo)
    private_inventory = run(['proof-search','index','list','--repo-root',str(repo),'--format','json'],repo)
    rows=[]
    for pair in range(SAMPLES):
        (repo/'M0000.lean').write_text('\n'.join(f'theorem changed_{pair}_{j} : True := True.intro' for j in range(DECLS))+'\n')
        order=['update','full'] if pair%2==0 else ['full','update']
        current={'pair':pair,'order':order}
        for operation in order:
            if operation=='update':
                args=['proof-search','index','update','--repo-root',str(repo),'--format','json']
            else:
                args=['proof-search','index','build','--repo-root',str(repo),'--index',str(repo/'.ladon/index/full.sqlite'),'--format','json']
            current[operation]=run(args,repo)
        current['identityEqual']=current['update']['identity']==current['full']['identity']
        current['diskBytesAfterPair']=directory_bytes(repo/'.ladon/index')
        rows.append(current)
    med_update=statistics.median(r['update']['wallSeconds'] for r in rows)
    med_full=statistics.median(r['full']['wallSeconds'] for r in rows)
    print(json.dumps({'fixture':{'modules':MODULES,'declarationsPerModule':DECLS,'changedModulesPerPair':1},'base':base,'sourceSnapshotProcess':source_snapshot,'sourceStatus':source_status,'queryBaseline':query_baseline,'private':private,'privateInventory':private_inventory,'pairs':rows,'medians':{'update':med_update,'full':med_full,'reduction':round(1-med_update/med_full,4)},'allIdentitiesEqual':all(r['identityEqual'] for r in rows)},indent=2))
