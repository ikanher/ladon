"""Kernel checks for generic Real rules in an explicitly selected compiled Mathlib project."""

import hashlib
import json
import os
import shutil
import time
from pathlib import Path

import pytest

from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.semantic_lean_execution import prepare_direct_lean_execution

FIXTURES = Path(__file__).parent / "fixtures/real_bound_rules"
SOURCES = Path(__file__).parents[1] / "src/ladon/lean"
RULES = ["transfer_identity", "transfer_compose", "transfer_input_prefix",
         "transfer_output_prefix", "transfer_coefficient_mono", "scaled_bound_mono"]
CASES = {
    "PositiveRules": ["dependent_composition", "weaken_input", "weaken_output",
                      "weaken_coefficient", "scalar_to_pair", "pair_to_triple",
                      "scalar_to_triple", "scale_sequence", "sequence_context",
                      "scale_inequality", "identity_example"],
    "NegativeRules": ["negative_multiplier", "negative_input_bound", "pointwise_not_uniform",
                      "changed_predicate", "changed_set", "changed_order", "changed_object",
                      "changed_bound", "missing_sign", "missing_prefix"],
}


def compile_lean(root, name, deadline):
    execution = prepare_direct_lean_execution(root, None, pinned_toolchain(root),
                                              require_compiled_module=False)
    remaining = deadline - time.monotonic()
    assert remaining > 0, "shared rule qualification deadline expired"
    result = run_bounded_target_process(
        [*execution.command, "-o", f".lake/build/lib/lean/{name}.olean", f"{name}.lean"],
        cwd=root, env=execution.environment, timeout_seconds=min(60, remaining),
        max_output_bytes=8 * 1024**2, max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
    assert result.succeeded, result.stdout + result.stderr
    return result


@pytest.fixture(scope="module")
def rule_project(tmp_path_factory):
    selected = os.environ.get("LADON_MATHLIB_TEST_ROOT")
    if selected is None:
        pytest.skip("set LADON_MATHLIB_TEST_ROOT to an existing compiled Mathlib project")
    chosen = Path(selected).resolve(strict=True)
    context = pinned_toolchain(chosen)
    root = tmp_path_factory.mktemp("real-bound-rules")
    (root / "lean-toolchain").write_bytes((chosen / "lean-toolchain").read_bytes())
    (root / ".lake/build/lib/lean").mkdir(parents=True)
    for index, library in enumerate(context.library_roots):
        target = root / f".lake/packages/import{index}/.lake/build/lib/lean"
        target.parent.mkdir(parents=True)
        target.symlink_to(library, target_is_directory=True)
    deadline = time.monotonic() + 600
    for module in ("LadonRealBound", "LadonRealBoundComposition"):
        shutil.copy2(SOURCES / f"{module}.lean", root / f"{module}.lean")
        compile_lean(root, module, deadline)
    return root, deadline


def observer(names):
    encoded = ", ".join(json.dumps(name) for name in names)
    return f"""
run_cmd do
  let env ← Lean.getEnv
  let mut rows : Array Lean.Json := #[]
  for decl in [{encoded}] do
    let name := decl.toName
    unless (env.checked.get.find? name).isSome do
      throwError "rule test declaration was not kernel checked"
    let axioms ← Lean.collectAxioms name
    rows := rows.push (Lean.Json.mkObj [
      ("declaration", Lean.toJson decl), ("axioms", Lean.toJson (axioms.map toString))])
  Lean.Elab.Command.liftIO <| IO.println ("LADON_REAL_RULES " ++ (Lean.Json.arr rows).compress)
"""


@pytest.mark.parametrize("module", list(CASES))
def test_real_rules_and_controls_are_kernel_checked(rule_project, module):
    root, deadline = rule_project
    namespace = "RuleExamples" if module == "PositiveRules" else "RuleControls"
    names = [f"{namespace}.{name}" for name in CASES[module]]
    names += [f"Ladon.RealBound.{name}" for name in RULES]
    original = (FIXTURES / f"{module}.lean").read_bytes()
    path = root / f"{module}.lean"
    path.write_bytes(original + observer(names).encode())
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    result = compile_lean(root, module, deadline)
    frames = [line.removeprefix("LADON_REAL_RULES ") for line in result.stdout.splitlines()
              if line.startswith("LADON_REAL_RULES ")]
    assert len(frames) == 1
    rows = json.loads(frames[0])
    assert [row["declaration"] for row in rows] == names
    assert all(set(row["axioms"]) <= {"propext", "Classical.choice", "Quot.sound"} for row in rows)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
