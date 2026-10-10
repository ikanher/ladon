"""Repeat broad gates serially on unchanged candidate bytes, retaining all outcomes."""
from __future__ import annotations

import hashlib
import json
import os
import runpy
import subprocess
import sys
import zipfile
from pathlib import Path

OUT = Path(__file__).parent.resolve()
ROOT = OUT.parents[4]


def main():
    candidate = json.loads((OUT / 'candidate-hashes.json').read_text())
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
               for name, digest in candidate['sha256'].items())
    with (OUT / 'strict-serial.log').open('w') as log:
        strict = subprocess.run([sys.executable, 'scripts/python_quality.py', '--strict'],
                                cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=False)
    helpers = runpy.run_path(str(OUT / 'installed-check.py'))
    wheel = ROOT / 'temp/let-signature-installed/dist/ladon-0.2.3-py3-none-any.whl'
    summary = {'wheelSha256': hashlib.sha256(wheel.read_bytes()).hexdigest(),
               'strictExitCode': strict.returncode, 'tests': helpers['TESTS'], 'runtimes': {}}
    for version in ('3.11', '3.12'):
        venv = ROOT / 'temp/let-signature-installed' / version
        python = venv / 'bin/python'
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        env.pop('PYTHONHOME', None)
        env['PATH'] = str(venv / 'bin') + os.pathsep + env['PATH']
        env['LADON_CONSOLE'] = str(venv / 'bin/ladon')
        env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
        origin = subprocess.check_output([str(python), '-c', 'import ladon; print(ladon.__file__)'],
                                         env=env, cwd=ROOT, text=True).strip()
        assert Path(origin).is_relative_to(venv)
        with zipfile.ZipFile(wheel) as archive:
            for name in archive.namelist():
                if name.startswith('ladon/') and not name.endswith('/'):
                    assert archive.read(name) == (ROOT / 'src' / name).read_bytes() == (Path(origin).parent.parent / name).read_bytes(), name
        installed_version = json.loads(subprocess.check_output(
            [str(venv / 'bin/ladon'), 'version', '--json'], env=env, cwd=ROOT, text=True))
        assert installed_version['package']['version'] == '0.2.3'
        if version == '3.11':
            logfile = OUT / 'installed-3.11.log'
            assert logfile.read_text().splitlines()[-1].startswith('1501 passed')
            exit_code = 0
        else:
            logfile = OUT / 'installed-3.12-serial.log'
            with logfile.open('w') as log:
                result = subprocess.run([str(python), '-m', 'pytest', '-q', *helpers['TESTS']],
                                        env=env, cwd=ROOT, stdout=log,
                                        stderr=subprocess.STDOUT, check=False)
            exit_code = result.returncode
        summary['runtimes'][version] = {'origin': origin, 'version': installed_version,
                                       'testResult': logfile.read_text().splitlines()[-1],
                                       'exitCode': exit_code, 'log': logfile.name}
    assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
               for name, digest in candidate['sha256'].items())
    (OUT / 'serial-qualification.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: summary[key] for key in ('strictExitCode', 'runtimes')}, indent=2))
    return strict.returncode or summary['runtimes']['3.12']['exitCode']


if __name__ == '__main__':
    raise SystemExit(main())
