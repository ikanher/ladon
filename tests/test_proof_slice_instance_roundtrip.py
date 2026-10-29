"""Closed proof printing must retain instances referenced by later binder types."""

import shutil
from pathlib import Path

import pytest

from ladon.proof_slice import extract_proof_slice
from ladon.proof_slice_validation import validate_slice_shape

FIXTURE = Path(__file__).parent / "fixtures/correspondence_m1"
SOURCE = """import Lean
namespace InstanceRoundtrip
class Carrier (α : Type) where
  value : α
class Ready (α : Type) [Carrier α] : Prop where
  ready : True
 theorem bridge (h : True) : True := h
 theorem selected {α : Type} [Carrier α] [Ready α]
     (dependent : Carrier.value (α := α) = Carrier.value (α := α))
     (h : True) : True := bridge h
 theorem used {α : Type} [Carrier α] [Ready α] (h : True) : True :=
   bridge (Ready.ready (α := α))
end InstanceRoundtrip
"""


@pytest.mark.parametrize("scoped", [False, True])
@pytest.mark.parametrize("declaration", ["selected", "used"])
def test_unused_instances_in_dependent_context_roundtrip(tmp_path, scoped, declaration):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo, ignore=shutil.ignore_patterns(".ladon", "*.olean"))
    source = repo / "InstanceRoundtrip.lean"
    source.write_text(SOURCE)
    result = extract_proof_slice(
        repo, source.name, "InstanceRoundtrip", f"InstanceRoundtrip.{declaration}",
        "InstanceRoundtrip.bridge", scoped=scoped,
    )
    assert result["complete"], "\n".join(r.get("stdout", "") for r in result["processReceipts"])
    validate_slice_shape(result)
    locals_ = result["localContext"]
    instances = [row for row in locals_ if row["binderInfo"] == "Lean.BinderInfo.instImplicit"]
    assert len(instances) == 2
    assert len({row["localId"] for row in instances}) == 2
    assert "InstanceRoundtrip.Carrier" in instances[0]["type"]["display"]
    assert "InstanceRoundtrip.Ready" in instances[1]["type"]["display"]
    assert any(row["name"] == "dependent" for row in locals_) is (declaration == "selected")
    assert source.read_text() == SOURCE
