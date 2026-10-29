import json
import hashlib
from pathlib import Path
import sys
import time

from ladon.process_supervisor import run_bounded_target_process

ROOT = Path.cwd()
OUT = ROOT / 'openspec/changes/ladon-real-bound-contracts/evidence/shape-observation-20261025'
FORMAL = ROOT / '.codex/state/navier-stokes-informed-diagnostic/formalization'
BASE = ROOT / 'openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/jet-contract-frontier-20261025'

rows = []
for name in ['inverse_finiteJets', 'nonbarPart_finiteJets', 'applyMultiplier_finiteJets']:
    source = BASE / (name + '.json')
    destination = OUT / (name + '.json')
    command = [sys.executable, '-m', 'ladon.entrypoint', 'investigation', 'contract',
               'observe-bound', '--input', str(source), '--root', str(FORMAL), '--output', str(destination)]
    started = time.monotonic()
    result = run_bounded_target_process(command, cwd=ROOT, timeout_seconds=60,
                                       max_rss_bytes=12*1024**3, max_output_bytes=8*1024**2)
    assert result.returncode == 2, str(result)
    observed = json.loads(destination.read_text())
    assert observed['statementSnapshot'] == json.loads(source.read_text())
    inspection = run_bounded_target_process(
        [sys.executable, '-m', 'ladon.entrypoint', 'investigation', 'contract',
         'inspect', '--input', str(destination), '--root', str(FORMAL)],
        cwd=ROOT, timeout_seconds=60, max_rss_bytes=12*1024**3, max_output_bytes=8*1024**2)
    assert inspection.returncode == 2, str(inspection)
    assert json.loads(inspection.stdout) == observed
    shape = observed['candidate']
    row = {'case':name,'command':command,'exitCode':result.returncode,
           'inspectionExitCode':inspection.returncode,'elapsedIncludingInspection':time.monotonic()-started,
           'status':observed['status'],'admission':observed['admission'],
           'loss':shape['loss'] if shape else None,'contract':observed['contract'],
           'residuals':observed['residuals'], 'sourceUnchanged':True}
    from dataclasses import asdict
    row['produceProcess']=asdict(result); row['inspectProcess']=asdict(inspection)
    # Output JSON is stored separately, not repeated in the process receipts.
    for key in ['produceProcess','inspectProcess']:
        for stream in ['stdout','stderr']:
            text=row[key].pop(stream, '')
            row[key][stream+'Digest']=hashlib.sha256(text.encode()).hexdigest()
    rows.append(row)
    print(name, row['status'], 'loss', row['loss'], flush=True)
(OUT/'REPLAY.json').write_text(json.dumps(rows,indent=2,default=str)+'\n')
