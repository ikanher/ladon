"""Build the source-first active-index delta without private databases or caches."""
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / 'temp/ladon-active-index-review-data-r03'
OUT.mkdir(parents=True, exist_ok=True)
MAPPINGS = []


def copy(source, target=None, role='current'):
    source = Path(source)
    target = target or str(source.relative_to(ROOT))
    destination = OUT / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    MAPPINGS.append({'archivePath': target, 'sourcePath': str(source), 'role': role,
                     'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'bytes': source.stat().st_size})


for source in sorted((ROOT / 'src').rglob('*')):
    if source.is_file() and '__pycache__' not in source.parts and source.suffix != '.pyc': copy(source)
qualification = json.loads((Path(__file__).parent / 'installed-check.json').read_text())
for source in qualification['tests']: copy(Path(source))
for name in ['README.md', 'pyproject.toml', 'uv.lock', 'build-constraints.txt', 'docs/CLI.md', 'docs/PROOF_SEARCH_INDEX_V1.md', 'docs/PRODUCT_SCOPE.md', 'skills/ladon/SKILL.md', 'scripts/python_quality.py', 'docs/MEASURED_ALPHA_PROFILE.md', 'openspec/changes/ladon-result-understanding-and-release-umbrella/sources.md']:
    copy(ROOT / name)
copy(ROOT.parent / 'codex-skills/ladon/SKILL.md', 'external-skills/ladon/SKILL.md')
change = ROOT / 'openspec/changes/ladon-evidence-preserving-index-update'
for source in sorted(change.rglob('*')):
    if source.is_file() and source.suffix != '.pyc' and '__pycache__' not in source.parts and source.name != 'packet-build.json':
        copy(source, role='historical' if any(part in {'historical-tests', 'earlier-installed'} for part in source.parts) or source.name in {'owner-inventory.md', 'strict-development.log', 'strict-final.log', 'strict-v022-final.log', 'strict-release-final.log'} else 'current')
for kind in ('fixture', 'adam'):
    project = ROOT / 'temp/index-history-field' / kind
    for name in ('lean-toolchain', 'lakefile.toml', 'lake-manifest.json'):
        copy(project / name, f'field-source/{kind}/build/{name}')
    sources = [project / 'CapsuleFixture.lean', *(project / 'CapsuleFixture').glob('*.lean')] if kind == 'fixture' else [project / 'Mf/Optimization/FiniteMemoryAdam/CumulativePairing.lean']
    for source in sources: copy(source, f'field-source/{kind}/' + str(source.relative_to(project)), role='source-excerpt')
for name in ('README.md', 'feedback.json'):
    with zipfile.ZipFile(ROOT / 'temp/ladon-adam-supported-bias-feedback-r03.zip') as archive:
        source = 'ladon-adam-supported-bias-feedback-r03/' + name
        target = 'feedback-r03/' + name
        (OUT / target).parent.mkdir(exist_ok=True)
        content = archive.read(source)
        (OUT / target).write_bytes(content)
        MAPPINGS.append({'archivePath': target, 'sourcePath': 'temp/ladon-adam-supported-bias-feedback-r03.zip!' + source, 'role': 'background-feedback', 'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)})
triage = ROOT / 'openspec/changes/ladon-proof-workflow-field-reliability/evidence/r01/FEEDBACK_R02_TRIAGE.md'
copy(triage, 'feedback-r02/TRIAGE.md', role='historical')
changed = subprocess.run(['git', 'diff', '--name-only'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
owned = [name for name in changed if name != 'FIRST-HAND-REPORT.md']
for name in owned:
    original = subprocess.run(['git', 'show', 'f1385a8d51b1fdd9e87a63008f78dd3642b05109:' + name], cwd=ROOT, capture_output=True, check=True).stdout
    target = OUT / 'data/before' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(original)
patch = subprocess.run(['git', 'diff', '--', *owned], cwd=ROOT, capture_output=True, text=True, check=True).stdout
(OUT / 'data').mkdir(exist_ok=True)
(OUT / 'data/working-tree.patch').write_text(patch)
(OUT / 'data/base-packet.json').write_text(json.dumps({'basePacket': 'ladon-active-index-review-data-r02.zip', 'sha256': hashlib.sha256((ROOT / 'temp/ladon-active-index-review-data-r02.zip').read_bytes()).hexdigest(), 'baseGitRevision': 'f1385a8d51b1fdd9e87a63008f78dd3642b05109', 'uncommitted': True}, indent=2)+'\n')
(OUT / 'data/source-map.json').write_text(json.dumps(MAPPINGS, indent=2)+'\n')
manifest = {'packetKind': 'delta-pro-review', 'topic': 'active-project index maintenance', 'version': '0.2.2', 'basePacket': 'ladon-active-index-review-data-r02.zip', 'nextDirectionRequired': True, 'bigPictureRequired': True, 'selfContainedReplay': False, 'entryPoints': ['README.md', 'REVIEW_PROMPT.md', 'REVIEW_DELTA.md', 'openspec/changes/ladon-evidence-preserving-index-update/evidence/r01/REPORT.md'], 'omissions': ['SQLite databases', 'wheel', 'compiled imports', 'virtual environments', 'full external Lean project', 'rendered PDF/HTML', 'shared source caches', 'unrelated FIRST-HAND-REPORT.md edits'], 'includedSourceEntries': len(MAPPINGS)}
(OUT / 'data/packet-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
summary = {'strictOpenSpec': subprocess.run(['openspec', 'validate', change.name, '--strict'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip(), 'jsonStrictParsing': True, 'sourceMapHashes': True, 'completeRuntimeSource': True, 'selfContainedLeanReplay': False, 'executionRenewedByPacketVerifier': False}
def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


for path in OUT.rglob('*.json'):
    json.loads(path.read_text(), object_pairs_hook=unique_object, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
for path in OUT.rglob('*.jsonl'):
    for line in path.read_text().splitlines():
        if line.strip(): json.loads(line, object_pairs_hook=unique_object, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
for entry in MAPPINGS:
    assert hashlib.sha256((OUT / entry['archivePath']).read_bytes()).hexdigest() == entry['sha256']
(OUT / 'data/validation-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
entries = [{'path': str(path.relative_to(OUT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size} for path in sorted(OUT.rglob('*')) if path.is_file() and path.name != 'entry-hashes.json']
(OUT / 'data/entry-hashes.json').write_text(json.dumps(entries, indent=2)+'\n')
zip_path = OUT.with_suffix('.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(OUT.rglob('*')):
        if path.is_file():
            assert path.suffix not in {'.pdf', '.html', '.olean', '.ilean', '.sqlite', '.whl', '.pyc'}, path
            assert not any(part in {'.lake', '__pycache__', '.git'} for part in path.parts), path
            archive.write(path, str(path.relative_to(OUT)))
with zipfile.ZipFile(zip_path) as archive:
    assert archive.testzip() is None
    for entry in entries: assert hashlib.sha256(archive.read(entry['path'])).hexdigest() == entry['sha256']
print(json.dumps({'packet': str(zip_path), 'entries': len(entries), 'bytes': zip_path.stat().st_size, 'sha256': hashlib.sha256(zip_path.read_bytes()).hexdigest()}))
