"""Actual replay in a private package cannot accept an implementation change."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("mutate", [True, False])
def test_actual_checker_implementation_is_stable_through_replay(tmp_path, mutate):
    checkout = Path(__file__).resolve().parents[1]
    package = tmp_path / "package"
    shutil.copytree(checkout / "src/ladon", package / "ladon",
                    ignore=shutil.ignore_patterns("__pycache__"))
    repo = tmp_path / "repo"
    shutil.copytree(checkout / "tests/fixtures/correspondence_m1", repo,
                    ignore=shutil.ignore_patterns(".ladon", "*.olean"))
    script = tmp_path / "run.py"
    script.write_text('''import json,sys,threading,time
from pathlib import Path
import ladon.correspondence_check as checker
from ladon.proof_slice import extract_proof_slice
root=Path(sys.argv[1]); mutate=sys.argv[2]=='True'
actual=extract_proof_slice(root,'Proof.lean','Proof','Correspondence.term','Correspondence.bridge')
plan=checker.prepare_correspondence(json.loads((root/'positive.json').read_text()),actual,{'n':'n'})
def change():
    time.sleep(2)
    path=Path(checker.__file__)
    path.write_bytes(path.read_bytes()+b'\\n# private concurrent source change\\n')
worker=threading.Thread(target=change) if mutate else None
if worker: worker.start()
try:
    result=checker.check_correspondence(plan,[],root)
except ValueError as error:
    assert mutate and 'implementation changed' in str(error), str(error)
else:
    assert not mutate, 'accepted changed checker implementation'
    assert result['conditionalValidity']=='supported'
finally:
    if worker: worker.join()
print('actual implementation freshness control passed')
''')
    command = [sys.executable, str(script), str(repo), str(mutate)]
    process = subprocess.run(command, env={**os.environ, "PYTHONPATH": str(package)},
                             capture_output=True, text=True, timeout=300, check=False)
    assert process.returncode == 0, process.stdout + process.stderr
