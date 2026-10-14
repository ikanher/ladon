"""One frozen pilot; root-owned recording, not a Ladon production adapter."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

from ladon.evaluation_process import measure_command

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
STATE = ROOT / '.codex/state/correspondence-discovery'
NATIVE = Path('/home/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin')
CONDA = Path('/home/codex/miniconda3')
SOURCE = ROOT / 'src/ladon'
LEAN = Path('/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0')
PACKAGES = ROOT / '.codex/state/proof-correspondence-audit-r70/fixture/.lake/packages'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(stem, input_path, assisted):
    private = STATE / 'namespaces' / stem
    private.mkdir(parents=True, exist_ok=False)
    profile = private / 'profile'
    profile.mkdir()
    shutil.copyfile('/home/codex/.codex/auth.json', profile / 'auth.json')
    os.chmod(profile / 'auth.json', 0o600)
    work = private / 'work'
    work.mkdir()
    tool = private / 'ladon'
    tool.write_text('#!/bin/sh\nexec /home/codex/miniconda3/bin/python -c "from ladon.entrypoint import main; main()" "$@"\n')
    tool.chmod(0o755)
    cmd = ['bwrap', '--unshare-all', '--share-net', '--die-with-parent', '--new-session']
    for source, target in [('/usr', '/usr'), ('/bin', '/bin'), ('/lib', '/lib'), ('/lib64', '/lib64'),
                           ('/etc/ssl', '/etc/ssl'), ('/etc/resolv.conf', '/etc/resolv.conf'),
                           ('/etc/hosts', '/etc/hosts'), (str(NATIVE), '/runner'),
                           (str(CONDA), str(CONDA)), (str(LEAN), '/lean'),
                           (str(PACKAGES), '/lean-packages'), (str(input_path), '/input/INPUT.md')]:
        cmd += ['--ro-bind', source, target]
    cmd += ['--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
            '--bind', str(profile), '/home/codex/.codex', '--bind', str(work), '/work']
    if assisted:
        cmd += ['--ro-bind', str(SOURCE), '/opt/ladon/ladon',
                '--ro-bind', str(tool), '/tools/ladon',
                '--ro-bind', str(ROOT / 'docs/CORRESPONDENCE_DISCOVERY.md'), '/procedure.md']
    lean_path = ':'.join('/lean-packages/' + p.name + '/.lake/build/lib/lean'
                         for p in sorted(PACKAGES.iterdir()) if p.is_dir())
    cmd += ['--chdir', '/work', '--clearenv', '--setenv', 'HOME', '/home/codex',
            '--setenv', 'PATH', '/tools:/lean/bin:/usr/bin:/bin',
            '--setenv', 'PYTHONPATH', '/opt/ladon', '--setenv', 'LEAN_PATH', lean_path]
    return private, work, cmd


def codex_args(prompt):
    return ['/runner/codex', 'exec', '--ephemeral', '--ignore-user-config', '--ignore-rules',
            '--skip-git-repo-check', '--dangerously-bypass-approvals-and-sandbox',
            '-m', 'gpt-6-luna', '-c', 'model_reasoning_effort="medium"',
            '-c', 'web_search="disabled"', '--json', '-o', '/work/first-report.json', prompt]


def run_case(case, arm, config):
    stem = case + '-' + arm
    output = HERE / 'runs' / stem
    output.mkdir(parents=True, exist_ok=False)
    input_path = HERE / 'cases' / case / 'INPUT.md'
    private, work, cmd = prepare(stem, input_path, arm == 'ladon-assisted')
    prompt = (HERE / 'COMMON-PROMPT.txt').read_text() + '\n' + config['armInstructions'][arm]
    (output / 'prompt.txt').write_text(prompt)
    command = cmd + codex_args(prompt)
    try:
        rec = measure_command(command, cwd=ROOT, environment=os.environ.copy(),
            bounds={'timeoutSeconds': config['longSelectionTimeoutSeconds'] if case.startswith('l') else config['excerptTimeoutSeconds'],
                    'maxOutputBytes': 8 * 1024 * 1024, 'maxRssBytes': config['leanRssLimitBytes']},
            output=output, stem='first-attempt')
        events = []
        for line in (output / 'first-attempt.stdout').read_text().splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        usage = [e['usage'] for e in events if e.get('type') == 'turn.completed']
        total = sum(u.get('input_tokens', 0) + u.get('output_tokens', 0) for u in usage)
        calls = sum(e.get('type') == 'item.completed' and e.get('item', {}).get('type') in
                    ['command_execution', 'mcp_tool_call', 'web_search', 'code_mode'] for e in events)
        report = work / 'first-report.json'
        if report.exists():
            shutil.copyfile(report, output / 'first-report.json')
        rec.update({'case': case, 'arm': arm, 'inputSha256': digest(input_path),
                    'configurationSha256': digest(HERE / 'configuration.json'),
                    'tokenUsage': usage, 'accountedTokens': total if usage else None,
                    'tokenAllowance': config['tokenAllowance'], 'tokenOverrun': total > config['tokenAllowance'],
                    'completedToolItems': calls, 'interventions': [],
                    'reportSha256': digest(report) if report.exists() else None,
                    'status': 'completed' if rec['exitCode'] == 0 and usage and report.exists() and total <= config['tokenAllowance'] else 'incomplete'})
        with (output / 'record.json').open('x') as f:
            json.dump(rec, f, indent=2)
            f.write('\n')
        print(json.dumps({'case': case, 'arm': arm, 'status': rec['status'], 'seconds': rec['runtimeSeconds'], 'tokens': rec['accountedTokens']}), flush=True)
        return rec
    finally:
        # Credential copy and private agent state are never evaluation artifacts.
        shutil.rmtree(private)


def main():
    config = json.loads((HERE / 'configuration.json').read_text())
    expected = json.loads((HERE / 'freeze.json').read_text())['files']
    for path, sha in expected.items():
        assert digest(HERE / path) == sha, path
    assert not (HERE / 'runs').exists(), 'First attempts already exist; never overwrite or retest.'
    (HERE / 'runs').mkdir()
    jobs = [(case, arm) for case in config['caseOrder'] for arm in config['arms']]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_case, c, a, config) for c, a in jobs]
        results = [f.result() for f in futures]
    (HERE / 'run-summary.json').write_text(json.dumps({'runs': len(results), 'completed': sum(r['status'] == 'completed' for r in results)}, indent=2) + '\n')


if __name__ == '__main__':
    main()
