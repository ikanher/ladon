import hashlib
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

from ladon._bounded_json_graph import canonical
from ladon.bounded_json_transport import pack_json, unpack_json
from ladon.process_supervisor import run_bounded_target_process

base = Path(__file__).resolve().parent
started = time.monotonic()
formal = json.loads(Path('openspec/changes/ladon-real-bound-contracts/evidence/qualification-20261027/native/inverse_finiteJets-production.json').read_text())
authored = json.loads(Path('.codex/state/real-prose-native/live/navier-produced.json').read_text())
value = {'formal': formal, 'authored': authored}
original = canonical(value)
packed = pack_json(value)
assert len(original) > 8*1024**2 and len(packed) <= 8*1024**2
(base/'PAIR-WIRE.json').write_bytes(packed)
packed_at = time.monotonic()
result = run_bounded_target_process([sys.executable, str(base/'worker.py')], cwd=Path.cwd(),
    env={**os.environ, 'PYTHONPATH':str(Path('src').resolve())},
    input_bytes=packed, timeout_seconds=600-(time.monotonic()-started),
    max_output_bytes=8*1024**2, max_rss_bytes=12*1024**3)
assert result.succeeded, result.stderr
returned = result.stdout.encode('ascii')
assert returned == packed
restored = unpack_json(returned)
assert canonical(restored) == original
assert restored['formal']['snapshotId'] == formal['snapshotId']
assert restored['authored']['snapshotId'] == authored['snapshotId']
receipt = asdict(result)
receipt['stdout'] = '<identical to PAIR-WIRE.json; root compared complete bytes>'
receipt['stdoutBytes'] = len(returned)
receipt['stdoutDigest'] = 'sha256:'+hashlib.sha256(returned).hexdigest()
(base/'WORKER-PROCESS.json').write_text(json.dumps(receipt,indent=2)+'\n')
summary = {'schema':'ladon-transport-qualification-v1','status':'exact-worker-roundtrip',
           'expandedBytes':len(original),'wireBytes':len(packed),'wireLimitBytes':8*1024**2,
           'packSeconds':packed_at-started,'workerSeconds':result.elapsed_seconds,
           'seconds':time.monotonic()-started,'workerPeakRssBytes':result.peak_rss_bytes,
           'dagNodes':len(json.loads(packed)['nodes']), 'completeBytesCompared':True,
           'nativeIdentitiesUnchanged':True,'historyStringsOpaque':True,
           'nativeConnection':False,'freshFormalAdmission':False,
           'limitsChangedForExistingProfiles':False}
(base/'QUALIFICATION.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
