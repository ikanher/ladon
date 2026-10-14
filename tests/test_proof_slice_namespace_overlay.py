"""Private target compilation must preserve qualified sibling import resolution."""
import shutil
from pathlib import Path

from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import extract_proof_slice, pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution


def test_private_qualified_module_keeps_canonical_sibling_imports(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    fixture = Path(__file__).parent / 'fixtures/correspondence_m1'
    shutil.copy(fixture / 'lean-toolchain', root / 'lean-toolchain')
    (root / 'Pkg').mkdir()
    dependency = root / 'Pkg/Dependency.lean'
    dependency.write_text('namespace Pkg\ntheorem bridge (n : Nat) (h : n < 8) : n < 9 := Nat.lt.step h\nend Pkg\n')
    source = root / 'Pkg/Target.lean'
    source.write_text('import Pkg.Dependency\nnamespace Pkg\ntheorem selected (x₀ : Nat) (h : x₀ < 8) : x₀ < 9 := bridge x₀ h\nend Pkg\n')
    compiled = root / '.lake/build/lib/lean/Pkg/Dependency.olean'
    compiled.parent.mkdir(parents=True)
    execution = prepare_direct_lean_execution(root, None, pinned_toolchain(root),
                                              require_compiled_module=False)
    build = run_bounded_target_process([*execution.command, '-o', str(compiled), str(dependency)],
        cwd=root, env=execution.environment, timeout_seconds=60, max_output_bytes=8*1024**2,
        max_rss_bytes=32*1024**3)
    assert build.succeeded, build.stdout + build.stderr
    original = source.read_bytes(), compiled.read_bytes()
    observed = extract_proof_slice(root, 'Pkg/Target.lean', 'Pkg.Target', 'Pkg.selected',
                                  'Pkg.bridge', scoped=True)
    assert observed['complete'], observed
    assert observed['selection']['module'] == 'Pkg.Target'
    assert observed['source']['module'] == 'Pkg.Target'
    assert source.read_bytes() == original[0] and compiled.read_bytes() == original[1]
