"""Real Lean traversal retains occurrence semantics while sharing negative work."""

from pathlib import Path

import pytest

from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES

ROOT = Path(__file__).parent / "fixtures/correspondence_m1"
HELPER = Path(__file__).parents[1] / "src/ladon/lean/ladon_scoped_slice_helper.lean"

CASES = [
    ("shared_negative", """
  let mut tail := mkNatLit 0
  for _ in [:13] do tail := mkApp2 (mkConst ``Nat.add) tail tail
  let target := mkApp (mkConst ``Nat.succ) (mkNatLit 0)
  let rows ← scopedOccurrences (mkApp2 (mkConst ``Nat.add) target tail) ``Nat.succ
  unless rows.size == 1 && rows[0]!.scopePath == #[1] do
    throwError "lost or duplicated target"
""", None),
    ("scope_multiplicity", """
  let nat := mkConst ``Nat
  let target := mkApp (mkConst ``Nat.succ) (mkBVar 0)
  let left := mkLambda `left BinderInfo.default nat target
  let right := mkLambda `right BinderInfo.default nat target
  let pair := mkAppN (mkConst ``Prod.mk [Level.zero, Level.zero])
    #[← mkArrow nat nat, ← mkArrow nat nat, left, right]
  let rows ← scopedOccurrences pair ``Nat.succ
  unless rows.size == 2 do throwError "lost shared match"
  unless rows[0]!.scopePath == #[3, 1] && rows[1]!.scopePath == #[4, 1] do
    throwError "changed flattened DFS order"
  for i in [:2] do
    let row := rows[i]!
    withLCtx row.lctx row.instances do
      let arg := row.expr.getAppArgs[0]!
      let decl ← arg.fvarId!.getDecl
      unless decl.userName == (if i == 0 then `left else `right) do
        throwError "wrong scope"
      unless row.nestedLocalIds == #[(repr decl.fvarId.name).pretty] do
        throwError "wrong nested identity"
      unless (← inferType row.expr) == nat do throwError "wrong local type"
  unless rows[0]!.nestedLocalIds != rows[1]!.nestedLocalIds do
    throwError "merged distinct contexts"
""", None),
    ("node_budget", """
  let mut leaves := (List.range 4096).toArray.map mkNatLit
  for _ in [:12] do
    leaves := (List.range (leaves.size / 2)).toArray.map fun i =>
      mkApp2 (mkConst ``Nat.add) leaves[2*i]! leaves[2*i+1]!
  let _ ← scopedOccurrences leaves[0]! ``Nat.succ
""", "expression node count exceeds 8192"),
    ("depth_after_shared_negative", """
  let shared := mkApp2 (mkConst ``Nat.add) (mkNatLit 0) (mkNatLit 1)
  let mut deep := shared
  for _ in [:64] do deep := mkMData {} deep
  let _ ← scopedOccurrences (mkApp2 (mkConst ``Nat.add) shared deep) ``Nat.succ
""", "expression depth exceeds 64"),
]


@pytest.mark.parametrize(("name", "body", "error"), CASES, ids=[row[0] for row in CASES])
def test_scoped_traversal_contract(tmp_path, name, body, error):
    prefix = HELPER.read_text().split("private def resolveName", 1)[0]
    source = tmp_path / f"{name}.lean"
    source.write_text(prefix + "\nrun_meta do\n" + body)
    toolchain = pinned_toolchain(ROOT)
    result = run_bounded_target_process(
        [str(toolchain.lean_path), str(source)], cwd=ROOT,
        env=dict(toolchain.environment), timeout_seconds=60,
        max_output_bytes=1024**2, max_rss_bytes=DEFAULT_MAX_RSS_BYTES,
    )
    output = result.stdout + result.stderr
    if error is None:
        assert result.succeeded, output
    else:
        assert not result.succeeded
        assert error in output
