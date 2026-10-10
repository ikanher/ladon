"""Qualify the built wheel, never an editable source import, on Python 3.11/3.12."""
import hashlib
import json
import os
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).parent
PYTHONS = {'3.11': '/home/codex/miniconda3/bin/python3.11',
           '3.12': '/home/codex/.local/bin/python3.12'}
TESTS = sorted(str(p) for p in (ROOT / 'tests').glob('test_*.py') if any(
    p.name.startswith(prefix) for prefix in (
        'test_index_', 'test_proof_search_', 'test_sqlite_', 'test_theorem_lineage_',
        'test_semantic_', 'test_proofir_', 'test_result_', 'test_canonical_',
        'test_evidence_receipt', 'test_installed_cli_contract',
    )
))


def run(command, *, environment=None, cwd=ROOT):
    result = subprocess.run(command, cwd=cwd, env=environment, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f'{command}: {result.stdout[-5000:]} {result.stderr[-3000:]}')
    return result.stdout


def main():
    temporary = ROOT / 'temp/index-history-installed'
    temporary.mkdir(parents=True, exist_ok=True)
    run(['uv', 'build', '--force-pep517', '--build-constraints', 'build-constraints.txt',
         '--out-dir', str(temporary / 'dist'), '.'])
    wheel = next((temporary / 'dist').glob('*.whl'))
    requirements = temporary / 'dev.txt'
    requirements.write_text(run(['uv', 'export', '--locked', '--group', 'dev',
                                 '--no-emit-project', '--no-hashes']))
    summary = {'wheel': wheel.name, 'wheelSha256': hashlib.sha256(wheel.read_bytes()).hexdigest(),
               'tests': TESTS, 'runtimes': {}, 'wheelSourceHashes': {}}
    for version, interpreter in PYTHONS.items():
        venv = temporary / version
        run(['uv', 'venv', '--clear', '--python', interpreter, str(venv)])
        python = venv / 'bin/python'
        run(['uv', 'pip', 'install', '--python', str(python), str(wheel), '-r', str(requirements)])
        run(['uv', 'pip', 'check', '--python', str(python)])
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        env.pop('PYTHONHOME', None)
        env['PATH'] = str(venv / 'bin') + os.pathsep + env['PATH']
        env['LADON_CONSOLE'] = str(venv / 'bin/ladon')
        env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
        origin = run([str(python), '-c', 'import ladon; print(ladon.__file__)'], environment=env).strip()
        assert Path(origin).is_relative_to(venv), origin
        with zipfile.ZipFile(wheel) as archive:
            for name in archive.namelist():
                if name.startswith('ladon/') and not name.endswith('/'):
                    content = archive.read(name)
                    source = ROOT / 'src' / name
                    installed = Path(origin).parent.parent / name
                    assert content == source.read_bytes() == installed.read_bytes(), name
                    summary['wheelSourceHashes'][name] = hashlib.sha256(content).hexdigest()
        installed_version = json.loads(run([str(venv / 'bin/ladon'), 'version', '--json'], environment=env))
        log = run([str(python), '-m', 'pytest', '-q', *TESTS], environment=env)
        (OUT / f'installed-{version}.log').write_text(log)
        summary['runtimes'][version] = {'origin': origin, 'version': installed_version,
                                        'testResult': log.splitlines()[-1]}
        print(version, summary['runtimes'][version]['testResult'], flush=True)
    (OUT / 'installed-check.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')


if __name__ == "__main__":
    main()
