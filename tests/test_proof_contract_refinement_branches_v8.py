"""Contract tests for immutable, source-bound proof finding refinements."""

import copy
import hashlib
import json

import pytest

from ladon.proof_contract_refinement import create_refinement_branch


def _source_reference(root, text, *, path="manuscript.txt", start_line=1, end_line=1):
    source_file = root / path
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text(text, encoding="utf-8")
    lines = text.splitlines()
    quote = "\n".join(lines[start_line - 1 : end_line])
    return {
        "path": path,
        "startLine": start_line,
        "endLine": end_line,
        "quote": quote,
        "sha256": hashlib.sha256(source_file.read_bytes()).hexdigest(),
    }


def _parent_identity(finding):
    encoded = json.dumps(
        finding, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _finding():
    return {
        "id": "finding-1",
        "status": "abstract-countermodel",
        "discrepancy": {"claim": "all inputs satisfy P", "observed": "x = -1"},
        "witness": {"id": "witness-1", "assignment": {"x": "-1"}},
    }


def _source_addition(root, *, path, text, constraint_id, expression):
    return {
        "id": constraint_id,
        "expression": expression,
        "justification": {
            "kind": "source-cited-refinement",
            "source": _source_reference(root, text, path=path),
            "nonclaim": "Span validation does not certify formula fidelity.",
        },
    }


def _first_source_branch(tmp_path):
    source = _source_addition(
        tmp_path,
        path="manuscript.txt",
        text="Assume x is an integer.\nAssume x is nonnegative.\n",
        constraint_id="constraint-nonnegative",
        expression="x >= 0",
    )
    return create_refinement_branch(_finding(), [source], source_root=tmp_path)


def test_source_refinements_are_content_addressed_and_preserve_finding(tmp_path):
    parent = _finding()
    original = copy.deepcopy(parent)
    addition = _source_addition(
        tmp_path,
        path="manuscript.txt",
        text="Assume x is nonnegative.\n",
        constraint_id="constraint-nonnegative",
        expression="x >= 0",
    )
    first = create_refinement_branch(parent, [addition], source_root=tmp_path)
    repeated = create_refinement_branch(parent, [addition], source_root=tmp_path)

    assert first["id"].startswith("sha256:")
    assert first["id"] == repeated["id"]
    assert first["parentId"] == _parent_identity(parent)
    assert first["originalFinding"] == original
    assert first["onlyNewConstraints"] == [addition]
    assert first["constraints"] == [addition]
    first["originalFinding"]["witness"]["assignment"]["x"] = "999"
    assert parent == original


def test_child_refinement_links_parent_and_accumulates_constraints(tmp_path):
    first = _first_source_branch(tmp_path)
    child_addition = _source_addition(
        tmp_path,
        path="other.txt",
        text="Assume x <= 10.\n",
        constraint_id="constraint-upper-bound",
        expression="x <= 10",
    )

    child = create_refinement_branch(first, [child_addition], source_root=tmp_path)

    assert child["parentId"] == first["id"]
    assert child["originalFinding"] == _finding()
    assert child["onlyNewConstraints"] == [child_addition]
    assert child["constraints"] == [first["constraints"][0], child_addition]
    assert child["id"] != first["id"]


@pytest.mark.parametrize("bad_reference", ["stale", "outside-root"])
def test_source_cited_refinement_rejects_stale_or_out_of_root_source(
    tmp_path, bad_reference
):
    source_root = tmp_path / "sources"
    source_root.mkdir()
    source = _source_reference(source_root, "Assume x >= 0.\n")
    if bad_reference == "stale":
        (source_root / source["path"]).write_text("Assume x < 0.\n", encoding="utf-8")
    else:
        outside = tmp_path / "outside.txt"
        outside.write_text("Assume x >= 0.\n", encoding="utf-8")
        source["path"] = "../outside.txt"
        source["sha256"] = hashlib.sha256(outside.read_bytes()).hexdigest()

    addition = {
        "id": "constraint-nonnegative",
        "expression": "x >= 0",
        "justification": {
            "kind": "source-cited-refinement",
            "source": source,
            "nonclaim": "Span validation does not certify formula fidelity.",
        },
    }
    with pytest.raises((ValueError, OSError)):
        create_refinement_branch(_finding(), [addition], source_root=source_root)


def _assert_repair_parent(branch, parent, original):
    assert branch["id"].startswith("sha256:")
    assert branch["parentId"] == _parent_identity(parent)
    assert branch["originalFinding"] == original


def _assert_repair_evidence(branch, original):
    assert branch["discrepancy"] == original["discrepancy"]
    assert branch["witness"] == original["witness"]


def _assert_repair_constraint(branch, repair):
    assert branch["onlyNewConstraints"] == [repair]
    assert branch["constraints"] == [repair]
    assert branch["branchKind"] == "proposed-repair"
    assert "not evidence for the original claim" in " ".join(branch["nonclaims"])


def test_absent_assumption_is_a_distinct_repair_branch_and_keeps_original_evidence(tmp_path):
    parent, repair = _finding(), {
        "id": "proposed-domain-assumption",
        "expression": "x >= 0",
        "justification": {
            "kind": "proposed-repair",
            "rationale": "The intended domain appears to require nonnegative inputs.",
        },
    }
    original = copy.deepcopy(parent)

    branch = create_refinement_branch(parent, [repair], source_root=tmp_path)

    _assert_repair_parent(branch, parent, original)
    _assert_repair_evidence(branch, original)
    _assert_repair_constraint(branch, repair)
    assert parent == original


def test_unsupported_justification_is_rejected(tmp_path):
    unsupported = {
        "id": "unsupported",
        "expression": "x >= 0",
        "justification": {"kind": "reviewer-assertion", "text": "trust me"},
    }

    with pytest.raises((TypeError, ValueError)):
        create_refinement_branch(_finding(), [unsupported], source_root=tmp_path)


def test_proposed_repair_requires_a_rationale(tmp_path):
    repair = {
        "id": "repair-without-rationale",
        "expression": "x >= 0",
        "justification": {"kind": "proposed-repair", "rationale": " "},
    }

    with pytest.raises((TypeError, ValueError)):
        create_refinement_branch(_finding(), [repair], source_root=tmp_path)


def test_tampered_parent_branch_cannot_be_extended(tmp_path):
    parent = _finding()
    repair = {
        "id": "repair-1",
        "expression": "x >= 0",
        "justification": {
            "kind": "proposed-repair",
            "rationale": "Suggested domain restriction.",
        },
    }
    branch = create_refinement_branch(parent, [repair], source_root=tmp_path)
    branch["witness"]["assignment"]["x"] = "10"

    with pytest.raises(ValueError, match="identity"):
        create_refinement_branch(branch, [repair], source_root=tmp_path)


def test_constraint_ids_remain_unique_across_parent_and_child(tmp_path):
    parent_constraint = {
        "id": "constraint-1",
        "expression": "x >= 0",
        "justification": {
            "kind": "proposed-repair",
            "rationale": "Initial proposed domain restriction.",
        },
    }
    parent = create_refinement_branch(_finding(), [parent_constraint], source_root=tmp_path)
    duplicate = {
        "id": "constraint-1",
        "expression": "x <= 10",
        "justification": {
            "kind": "proposed-repair",
            "rationale": "A second distinct domain restriction.",
        },
    }

    with pytest.raises(ValueError, match="unique"):
        create_refinement_branch(parent, [duplicate], source_root=tmp_path)


def test_origin_parent_identity_binds_all_finding_content(tmp_path):
    original = _finding()
    changed = copy.deepcopy(original)
    changed["discrepancy"]["observed"] = "x = 2"
    repair = {
        "id": "repair-1",
        "expression": "x >= 0",
        "justification": {
            "kind": "proposed-repair",
            "rationale": "Suggested domain restriction.",
        },
    }

    first = create_refinement_branch(original, [repair], source_root=tmp_path)
    second = create_refinement_branch(changed, [repair], source_root=tmp_path)

    assert original["id"] == changed["id"]
    assert first["parentId"] != second["parentId"]
    assert first["id"] != second["id"]


def test_oversized_depth_is_rejected_before_branch_copying(tmp_path):
    expression = {"leaf": "x"}
    for _ in range(40):
        expression = {"nested": expression}
    constraint = {
        "id": "deep-expression",
        "expression": expression,
        "justification": {
            "kind": "proposed-repair",
            "rationale": "Boundedness regression.",
        },
    }

    with pytest.raises(ValueError):
        create_refinement_branch(_finding(), [constraint], source_root=tmp_path)
