"""Exercise the real helper on shared proof DAGs and all expression children."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_constant_collector_preserves_coverage_and_visits_shared_nodes_once(tmp_path: Path) -> None:
    helper = (ROOT / "src/ladon/lean/ladon_theorem_capsule_helper.lean").read_text()
    start = helper.index("private structure ConstantCollector")
    finish = helper.index("private def declarationKind", start)
    cases = (ROOT / "tests/fixtures/constant_collector_cases.lean").read_text()
    source = tmp_path / "ConstantCollectorCheck.lean"
    source.write_text(cases.replace("-- INSERT_HELPER_COLLECTOR", helper[start:finish]))
    completed = subprocess.run(
        ["lean", str(source)],
        cwd=ROOT / "tests/fixtures/theorem_capsule",
        capture_output=True, text=True, check=False, timeout=45,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
