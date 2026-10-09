"""The Lean codec retains annotations and every expression constructor."""
import json
import shutil
import subprocess
from importlib import resources
from pathlib import Path

import pytest

from ladon._expr_graph_protocol import PREFIX, validate_structural_text


@pytest.mark.skipif(shutil.which('lean') is None, reason='Lean unavailable')
def test_codec_preserves_constructor_and_annotation_distinctions(tmp_path):
    codec = resources.files('ladon').joinpath('lean/ladon_expr_graph.lean').read_text()
    source = 'import Lean\nopen Lean\n' + codec + r'''
def main : IO Unit := do
  let ty := Expr.sort .zero
  let body := Expr.bvar 0
  let examples := #[
    body, Expr.fvar ⟨`x⟩, Expr.mvar ⟨`x⟩, ty,
    Expr.const `f [.param `u], Expr.app body body,
    Expr.lam `x ty body .default, Expr.lam `y ty body .default,
    Expr.lam `x ty body .implicit, Expr.forallE `x ty body .default,
    Expr.letE `x ty body body false, Expr.letE `x ty body body true,
    Expr.lit (.natVal 1), Expr.lit (.strVal "one"),
    Expr.mdata (KVMap.empty.insert `tag (.ofString "one")) body,
    Expr.mdata (KVMap.empty.insert `tag (.ofString "two")) body,
    Expr.proj `Prod 0 body, Expr.proj `Prod 1 body]
  IO.println (Json.compress (toJson (examples.map structuralText)))
  if structuralText (Expr.app body body) != structuralText (Expr.app body body) then
    throw (IO.userError "nondeterministic encoding")
'''
    path = tmp_path / 'Codec.lean'
    path.write_text(source)
    fixture = Path(__file__).parent / 'fixtures/lean_integration'
    output = subprocess.run(['lean', '--run', str(path)], cwd=fixture,
                            capture_output=True, text=True, timeout=30, check=False)
    assert output.returncode == 0, output.stdout + output.stderr
    strings = json.loads(output.stdout)
    assert len(strings) == len(set(strings)) == 18
    tags = set()
    for encoded in strings:
        validate_structural_text(encoded)
        graph = json.loads(encoded.removeprefix(PREFIX))
        tags.update(node[0] for node in graph['nodes'])
        assert json.loads(json.dumps(graph)) == graph
    assert tags == {'bvar', 'fvar', 'mvar', 'sort', 'const', 'app', 'lam',
                    'forallE', 'letE', 'lit', 'mdata', 'proj'}
    assert len(json.loads(strings[5].removeprefix(PREFIX))['nodes']) == 2
