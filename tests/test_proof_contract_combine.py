"""Loss-max combination has a distinct checked theorem from requirement maxima."""

import shutil
import subprocess
from pathlib import Path

from ladon.proof_contract_rules import PROFILE


def test_estimate_combination_and_constant_sum_have_real_lean_rules(tmp_path):
    assert PROFILE["rules"].get("identity") == "id"
    fixture = Path(__file__).parent / "fixtures/proof_contracts"
    source = (fixture / "ContractMath.lean").read_text()
    probe = tmp_path / "CheckCombine.lean"
    probe.write_text(source + "\n#check ContractMath.combine_estimates\n"
                     "#check ContractMath.permission_sum_union\n")
    lean = shutil.which("lean")
    assert lean is not None
    result = subprocess.run([lean, str(probe)], cwd=fixture, capture_output=True,
                            text=True, timeout=60, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
