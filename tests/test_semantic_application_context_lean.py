"""Observe introduced dependent locals and declaration binders in real Lean."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

from ladon.lean_toolchain import resolve_toolchain_context
from ladon.process_supervisor import run_bounded_target_process
from ladon.proofir_v3 import validate_envelope_batch
from ladon.semantic_candidate_batch_worker import check_semantic_candidates
from ladon.semantic_candidate_worker import SemanticCandidateRequest, check_semantic_candidate

SOURCE = """namespace BinderFixture
theorem use {α : Type} ⦃β : Type⦄ [Inhabited α]
    (x : α) (y : β) (h : x = x) (k : y = y) : (x = x) ∧ (y = y) :=
  And.intro h k
end BinderFixture
"""
GOAL = "∀ (α β : Type) [Inhabited α] (x : α) (y : β), (x = x) ∧ (y = y)"


def _request(tmp_path):
    fixture = next(
        parent / "tests/fixtures/lean_integration"
        for parent in Path(__file__).resolve().parents
        if (parent / "tests/fixtures/lean_integration/lean-toolchain").is_file()
    )
    prefix = subprocess.run(
        ["lean", "--print-prefix"], cwd=fixture, capture_output=True,
        text=True, check=True, timeout=15,
    ).stdout.strip()
    lean = Path(prefix) / "bin/lean"
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy2(fixture / "lean-toolchain", repo / "lean-toolchain")
    (repo / "BinderFixture.lean").write_text(SOURCE)
    compiled = repo / ".lake/build/lib/lean"
    compiled.mkdir(parents=True)
    build = run_bounded_target_process(
        [str(lean), "-o", str(compiled / "BinderFixture.olean"), "BinderFixture.lean"],
        cwd=repo, timeout_seconds=20, max_output_bytes=8 * 1024**2,
        max_rss_bytes=32 * 1024**3,
    )
    assert build.succeeded, build.stdout + build.stderr
    context = resolve_toolchain_context(
        repo, lean_path=lean, lake_path=lean.with_name("lake"), selection_mode="explicit",
    )
    request = SemanticCandidateRequest(
        repo, "BinderFixture", GOAL, "BinderFixture.use", toolchain=context,
        timeout_seconds=20, max_rss_bytes=32 * 1024**3,
    )
    return request


def _assert_observations(result, protocol):
    assert result["status"] == "applicable-with-residuals", result
    assert result["applicationObservationVersion"] == 4
    assert result["semanticProtocol"] == protocol
    assert [row["typeDisplay"] for row in result["residualPremises"]] == ["x = x", "y = y"]
    contexts = _assert_residual_contexts(result)
    selected = _assert_declaration_telescope(result)
    validate_envelope_batch(result["artifacts"])
    owner = next(s for s in result["artifacts"][1]["subjectRefs"] if s["kind"] == "candidate-application")
    assert owner["searchShape"]["selectedDeclaration"] == selected
    assert owner["searchShape"]["residualContexts"] == contexts


def _assert_residual_contexts(result):
    contexts = result["residualContexts"]
    assert len(contexts) == 2 and contexts[0]["goalId"] != contexts[1]["goalId"]
    for row in contexts:
        locals_ = row["localContext"]
        names = [local["userName"] for local in locals_]
        assert names.index("α") < names.index("β") < names.index("x") < names.index("y")
        ids = {local["userName"]: local["localId"] for local in locals_}
        x = next(local for local in locals_ if local["userName"] == "x")
        assert ids["α"] in x["dependencies"]
        assert any("Inhabited" in local["typeDisplay"] for local in locals_)
    return contexts


def _assert_declaration_telescope(result):
    selected = result["selectedDeclaration"]
    assert selected["name"] == "BinderFixture.use"
    assert selected["typeDisplay"] and selected["typeStructural"]
    _assert_binder_kinds(selected["binders"])
    _assert_binder_dependencies(selected["binders"])
    return selected


def _assert_binder_kinds(binders):
    assert [b["userName"] for b in binders if b["userName"] in {"α", "β", "x", "y", "h", "k"}] == ["α", "β", "x", "y", "h", "k"]
    kinds = {b["userName"]: b["binderInfo"].rsplit(".", 1)[-1] for b in binders}
    assert kinds["α"] == "implicit" and kinds["β"] == "strictImplicit"
    assert kinds["x"] == "default" and any(b["binderInfo"].endswith("instImplicit") for b in binders)


def _assert_binder_dependencies(binders):
    x = next(b for b in binders if b["userName"] == "x")
    h = next(b for b in binders if b["userName"] == "h")
    assert x["localId"] in h["dependencies"]
    assert all(b["origin"] == "declaration-parameter" for b in binders)


@pytest.mark.skipif(shutil.which("lean") is None, reason="Lean toolchain unavailable")
@pytest.mark.parametrize("batch", [False, True])
def test_real_v4_application_observes_introduced_context_and_full_telescope(tmp_path, batch):
    request = _request(tmp_path)
    before = {str(p.relative_to(request.repo_root)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in request.repo_root.rglob("*") if p.is_file()}
    assert request.local_context == ()
    if batch:
        result = check_semantic_candidates(request, [request.candidate]).to_dict()
        assert result["status"] == "available", result
        _assert_observations(result["rows"][0], "ladon-lean-semantic-v4/check-candidates")
    else:
        result = check_semantic_candidate(request).to_dict()
        assert result["callerLocalContext"] == []
        _assert_observations(result, "ladon-lean-semantic-v4/check-candidate")
    after = {str(p.relative_to(request.repo_root)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in request.repo_root.rglob("*") if p.is_file()}
    assert after == before
