"""Corrected proposal for actual-Lean prepared correspondence-context regressions.

Scratch evidence only. This draft is not executed while root owns live replay/build
activity. It retains the first draft separately and supersedes its positive fixture.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

LADON = Path(__file__).resolve().parents[1]
FIXTURE = LADON / "tests/fixtures/correspondence_m1"
PUBLIC_SOURCE = b'''import Lean
namespace PreparedContextRegression
theorem bridge (n : Nat) : n = n := rfl
theorem selected (n : Nat) : n = n := bridge n
end PreparedContextRegression
'''
PRIVATE_SOURCE = b'''import Lean
namespace PreparedContextRegression
private theorem unrelatedPrivate (n : Nat) : n = n := rfl
theorem bridge (n : Nat) : n = n := rfl
theorem selected (n : Nat) : n = n := bridge n
end PreparedContextRegression
'''


def _case(tmp_path: Path, *, private_source=False):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo, ignore=shutil.ignore_patterns(".ladon", ".lake", "*.olean"))
    source = repo / "Proof.lean"
    source.write_bytes(PRIVATE_SOURCE if private_source else PUBLIC_SOURCE)
    compiled_root = repo / ".lake/build/lib/lean"
    compiled_root.mkdir(parents=True)

    # The fixture omits the canonical compiled root. Create it before pinning and
    # extraction so the environment identity sees the root the owner may use.
    from ladon.correspondence_preparation import prepare_source_context
    from ladon.proof_slice import extract_proof_slice, pinned_toolchain

    toolchain = pinned_toolchain(repo)
    fresh = extract_proof_slice(
        repo, "Proof.lean", "Proof", "PreparedContextRegression.selected",
        "PreparedContextRegression.bridge",
    )
    assert fresh["complete"] is True, fresh
    compiled_before = {p.relative_to(compiled_root) for p in compiled_root.rglob("*") if p.is_file()}
    return repo, source, compiled_root, fresh, toolchain, prepare_source_context, compiled_before


def _assert_good_and_bad_siblings(repo, source, fresh, toolchain, prepare, order):
    from ladon.correspondence_check import _check_goal

    with prepare(repo, fresh, source.read_bytes(), toolchain) as prepared:
        assert prepared is not None, "public source fixture should support preparation"
        prepared.verify()
        results = {}
        goals = {
            "bad": ("False", "True.intro"),
            "good": ("∀ n : Nat, n = n", "by intro n; rfl"),
        }
        for name in order:
            goal, term = goals[name]
            results[name] = _check_goal(
                goal, term, repo, source.read_bytes(), {}, toolchain, prepared=prepared,
            )
            prepared.verify()

        good = results["good"]
        _assert_good(good)

        bad = results["bad"]
        assert bad["status"] == "unresolved", bad
        assert bad["capture"]["status"] == "captured", bad
        assert bad["completion"]["status"] != "completed", bad
        assert bad["completion"]["trust"]["accepted"] is False, bad
        assert results["good"]["completion"]["replay"]["status"] == "accepted"


@pytest.mark.parametrize("order", [("bad", "good"), ("good", "bad")])
def test_real_valid_and_invalid_siblings_are_independent_in_both_orders(tmp_path, order):
    repo, source, _, fresh, toolchain, prepare, _ = _case(tmp_path)
    _assert_good_and_bad_siblings(repo, source, fresh, toolchain, prepare, order)


def test_private_source_shape_is_declined_before_prepared_evidence_is_used(tmp_path):
    repo, source, _, fresh, toolchain, prepare, _ = _case(tmp_path, private_source=True)
    with prepare(repo, fresh, source.read_bytes(), toolchain) as prepared:
        assert prepared is None, "private-source shape must select the ordinary per-goal fallback"
    from ladon.correspondence_check import _check_goal

    fallback = _check_goal(
        "∀ n : Nat, n = n", "by intro n; exact PreparedContextRegression.bridge n",
        repo, source.read_bytes(), {}, toolchain,
    )
    assert fallback["status"] == "supported", fallback
    assert fallback["capture"]["status"] == "captured", fallback
    assert fallback["completion"]["replay"]["status"] == "accepted", fallback
    assert fallback["completion"]["trust"]["accepted"] is True, fallback


@pytest.mark.parametrize("mutation", ["source", "context-source", "context-olean", "context-sidecar"])
def test_prepared_owner_rejects_state_change_even_after_bytes_are_restored(tmp_path, mutation):
    repo, source, compiled_root, fresh, toolchain, prepare, compiled_before = _case(tmp_path)
    from ladon.correspondence_check import _check_goal

    # A stale owner also refuses ordinary exit/cleanup authority; this outer
    # rejection supplements the per-use rejection and retains foreign residue.
    with (pytest.raises((ValueError, RuntimeError), match="(?i)(stale|changed|mutat|identity|fingerprint)"),
          prepare(repo, fresh, source.read_bytes(), toolchain) as prepared):
        assert prepared is not None
        prepared.verify()
        target = _mutation_target(prepared, compiled_root, compiled_before, mutation, source, repo)
        # Lean 4.32 ordinary compilation emits no sidecars. Verify its
        # recorded absence by injecting a new file; newer compiler output
        # is mutated when present. Neither branch fabricates proof evidence.
        _mutate_and_restore(target, prepared)
        # A mutation remains stale after an attacker restores the exact old bytes.
        with pytest.raises((ValueError, RuntimeError), match="(?i)(stale|changed|mutat|identity|fingerprint)"):
            prepared.verify()
        with pytest.raises((ValueError, RuntimeError), match="(?i)(stale|changed|mutat|identity|fingerprint)"):
            _check_goal("True", "True.intro", repo, source.read_bytes(), {}, toolchain,
                        prepared=prepared)


def test_owner_cleans_its_context_source_compiled_module_and_sidecars(tmp_path):
    repo, source, compiled_root, fresh, toolchain, prepare, compiled_before = _case(tmp_path)
    context_source = None
    with prepare(repo, fresh, source.read_bytes(), toolchain) as prepared:
        assert prepared is not None
        prepared.verify()
        context_source = Path(prepared.source_path)
        if not context_source.is_absolute():
            context_source = repo / context_source
    compiled_after = {p.relative_to(compiled_root) for p in compiled_root.rglob("*") if p.is_file()}
    assert compiled_after == compiled_before, "request-owned compiled files and sidecars must be removed"
    assert context_source is not None and not context_source.exists(), "request source snapshot must be cleaned"


def _assert_good(good):
    assert good["status"] == "supported", good
    assert good["capture"]["status"] == "captured", good
    completion = good["completion"]
    assert completion["status"] == "completed", completion
    assert completion["replay"]["status"] == "accepted", completion
    assert completion["trust"]["accepted"] is True, completion
    assert completion["trust"]["policy"] == "lean-standard-no-placeholders-v1", completion
    assert completion["trust"]["coverage"] == "complete", completion
    assert completion["trust"]["observedAxioms"] is not None, completion
    assert "sorryAx" not in completion["trust"]["observedAxioms"], completion



def _mutation_target(prepared, compiled_root, compiled_before, mutation, source, repo):
    context_source = Path(prepared.source_path)
    if not context_source.is_absolute():
        context_source = repo / context_source
    sidecars, olean = _compiled_targets(compiled_root, compiled_before)
    targets = {
        "source": source,
        "context-source": context_source,
        "context-olean": olean[0] if olean else None,
        "context-sidecar": sidecars[0] if sidecars else olean[0].with_suffix(".ir"),
    }
    target = targets[mutation]
    assert target is not None, f"no owned artifact available for {mutation}"
    return target


def _mutate_and_restore(target, prepared):
    original = target.read_bytes() if target.exists() else None
    target.write_bytes((original or b"") + b"\n-- request-state mutation probe\n")
    try:
        with pytest.raises((ValueError, RuntimeError), match="(?i)(stale|changed|mutat|identity|fingerprint)"):
            prepared.verify()
    finally:
        if original is None:
            target.unlink()
        else:
            target.write_bytes(original)


def _compiled_targets(compiled_root, compiled_before):
    new_compiled = [p for p in compiled_root.rglob("*") if p.is_file()
                    and p.relative_to(compiled_root) not in compiled_before]
    sidecars = [p for p in new_compiled if p.suffix in {".private", ".server", ".ir", ".ir.sig"}]
    olean = [p for p in new_compiled if p.suffix == ".olean"]
    return sidecars, olean
