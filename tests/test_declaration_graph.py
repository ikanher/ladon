from __future__ import annotations

from ladon.analysis.declaration_graph import (
    classify_unresolved_candidate,
    summarize_declaration_graph,
)
from ladon.ir import LeanDeclaration


def test_declaration_graph_resolves_exact_edges_and_fan_counts() -> None:
    declarations = {
        "A.root": LeanDeclaration(
            name="A.root",
            module="A",
            kind="theorem",
            references=("A.helper", "A.leaf", "Nat.succ"),
        ),
        "A.helper": LeanDeclaration(
            name="A.helper",
            module="A",
            kind="lemma",
            references=("A.leaf",),
        ),
        "A.leaf": LeanDeclaration(name="A.leaf", module="A", kind="lemma"),
    }

    summary = summarize_declaration_graph(declarations, chosen_roots=("A.root",))

    assert summary["declaration_count"] == 3
    assert summary["edge_count"] == 3
    assert summary["unresolved_reference_count"] == 1
    assert summary["edges"] == {
        "A.helper": ["A.leaf"],
        "A.leaf": [],
        "A.root": ["A.helper", "A.leaf"],
    }
    assert summary["top_fan_in"][0]["declaration"] == "A.leaf"
    assert summary["top_fan_in"][0]["fan_in"] == 2
    assert summary["top_fan_out"][0]["declaration"] == "A.root"
    assert summary["top_fan_out"][0]["fan_out"] == 2
    assert summary["declarations_not_reachable_from_chosen_roots_count"] == 0


def test_declaration_graph_keeps_unreachable_known_declarations() -> None:
    declarations = {
        "A.root": LeanDeclaration(name="A.root", module="A", references=("A.helper",)),
        "A.helper": LeanDeclaration(name="A.helper", module="A"),
        "A.orphan": LeanDeclaration(name="A.orphan", module="A"),
    }

    summary = summarize_declaration_graph(declarations, chosen_roots=("A.root", "Missing.root"))

    assert summary["chosen_roots"] == ["A.root"]
    assert summary["declarations_not_reachable_from_chosen_roots"] == ["A.orphan"]
    assert summary["declarations_not_reachable_from_chosen_roots_count"] == 1


def test_declaration_graph_resolves_local_and_unique_basename_references() -> None:
    declarations = {
        "A.root": LeanDeclaration(
            name="A.root",
            module="A",
            references=("helper", "globalLeaf", "missing"),
        ),
        "A.helper": LeanDeclaration(name="A.helper", module="A"),
        "B.globalLeaf": LeanDeclaration(name="B.globalLeaf", module="B"),
    }

    summary = summarize_declaration_graph(declarations, chosen_roots=("A.root",))

    assert summary["edges"]["A.root"] == ["A.helper", "B.globalLeaf"]
    assert summary["unresolved_reference_count"] == 1


def test_declaration_graph_keeps_ambiguous_basename_unresolved() -> None:
    declarations = {
        "C.root": LeanDeclaration(name="C.root", module="C", references=("shared",)),
        "A.shared": LeanDeclaration(name="A.shared", module="A"),
        "B.shared": LeanDeclaration(name="B.shared", module="B"),
    }

    summary = summarize_declaration_graph(declarations, chosen_roots=("C.root",))

    assert summary["edges"]["C.root"] == []
    assert summary["unresolved_reference_count"] == 1


def test_declaration_graph_reports_common_unresolved_reference_candidates() -> None:
    declarations = {
        "A.root": LeanDeclaration(
            name="A.root",
            module="A",
            references=("missing", "other"),
        ),
        "A.helper": LeanDeclaration(name="A.helper", module="A", references=("missing",)),
        "A.leaf": LeanDeclaration(name="A.leaf", module="A"),
    }

    summary = summarize_declaration_graph(declarations, chosen_roots=("A.root",))

    assert summary["top_unresolved_references"][0] == {
        "candidate": "missing",
        "classification": "local_or_field_candidate",
        "count": 2,
        "sample_sources": ["A.helper", "A.root"],
    }
    assert summary["top_unresolved_references"][1]["candidate"] == "other"


def test_unresolved_candidate_classifier_labels_common_noise() -> None:
    cases = {
        "[anonymous]": "parser_noise",
        "count": "local_or_field_candidate",
        "Fin": "external_candidate",
        "ENNReal.ofReal": "external_candidate",
        "Filter.Eventually.of_forall": "external_candidate",
        "Finset.univ": "external_candidate",
        "Fintype.sum_equiv": "external_candidate",
        "MeasurableSet": "external_candidate",
        "ProbabilityTheory.gaussianReal": "external_candidate",
        "StrictMonoOn": "external_candidate",
        "WellFounded.fix": "external_candidate",
        "C": "local_type_parameter_candidate",
        "X": "local_type_parameter_candidate",
        "Δ": "local_type_parameter_candidate",
        "Edge": "local_type_parameter_candidate",
        "_ht": "local_or_field_candidate",
        "t.rev": "local_or_field_candidate",
        "MissingTheorem": "actionable_unknown",
    }

    for candidate, expected in cases.items():
        assert classify_unresolved_candidate(candidate) == expected


def test_declaration_graph_splits_actionable_unresolved_candidates() -> None:
    declarations = {
        "A.root": LeanDeclaration(
            name="A.root",
            module="A",
            references=("count", "Fin", "MissingTheorem", "MissingTheorem"),
        )
    }

    summary = summarize_declaration_graph(declarations, chosen_roots=("A.root",))

    rows = {row["candidate"]: row for row in summary["top_unresolved_references"]}
    assert rows["count"]["classification"] == "local_or_field_candidate"
    assert rows["Fin"]["classification"] == "external_candidate"
    assert rows["MissingTheorem"]["classification"] == "actionable_unknown"
    assert summary["top_actionable_unresolved_references"] == [
        {
            "candidate": "MissingTheorem",
            "classification": "actionable_unknown",
            "count": 2,
            "sample_sources": ["A.root", "A.root"],
        }
    ]


def test_declaration_graph_excludes_calibrated_lean_noise_from_actionable_rows() -> None:
    declarations = {
        "A.root": LeanDeclaration(
            name="A.root",
            module="A",
            references=("Edge", "WellFounded.fix", "MissingTheorem"),
        )
    }

    summary = summarize_declaration_graph(declarations, chosen_roots=("A.root",))

    rows = {row["candidate"]: row for row in summary["top_unresolved_references"]}
    assert rows["Edge"]["classification"] == "local_type_parameter_candidate"
    assert rows["WellFounded.fix"]["classification"] == "external_candidate"
    assert summary["top_actionable_unresolved_references"] == [
        {
            "candidate": "MissingTheorem",
            "classification": "actionable_unknown",
            "count": 1,
            "sample_sources": ["A.root"],
        }
    ]


def test_declaration_graph_classifies_known_inventory_candidates() -> None:
    declarations = {
        "A.root": LeanDeclaration(
            name="A.root",
            module="A",
            references=("KnownImportedThing", "TrulyMissingThing"),
        )
    }

    summary = summarize_declaration_graph(
        declarations,
        chosen_roots=("A.root",),
        known_reference_names=("KnownImportedThing",),
    )

    rows = {row["candidate"]: row for row in summary["top_unresolved_references"]}
    assert rows["KnownImportedThing"]["classification"] == "known_inventory_candidate"
    assert rows["TrulyMissingThing"]["classification"] == "actionable_unknown"
    assert summary["unresolved_reference_classes"] == [
        {"classification": "actionable_unknown", "count": 1},
        {"classification": "known_inventory_candidate", "count": 1},
    ]
    assert summary["top_actionable_unresolved_references"] == [
        {
            "candidate": "TrulyMissingThing",
            "classification": "actionable_unknown",
            "count": 1,
            "sample_sources": ["A.root"],
        }
    ]


def test_actionable_unresolved_rows_are_not_hidden_by_high_count_noise() -> None:
    noisy_references = tuple(f"noise{i}" for i in range(20))
    declarations = {
        "A.root": LeanDeclaration(
            name="A.root",
            module="A",
            references=(*noisy_references, "TrulyMissingThing"),
        )
    }

    summary = summarize_declaration_graph(
        declarations,
        chosen_roots=("A.root",),
        known_reference_names=noisy_references,
    )

    assert summary["top_actionable_unresolved_references"] == [
        {
            "candidate": "TrulyMissingThing",
            "classification": "actionable_unknown",
            "count": 1,
            "sample_sources": ["A.root"],
        }
    ]


def test_declaration_graph_groups_declaration_name_families_by_suffix() -> None:
    declarations = {
        "A.alpha_ge_one": LeanDeclaration(name="A.alpha_ge_one", module="A"),
        "A.beta_ge_one": LeanDeclaration(name="A.beta_ge_one", module="A"),
        "A.gamma_nonneg": LeanDeclaration(name="A.gamma_nonneg", module="A"),
    }

    summary = summarize_declaration_graph(declarations)

    assert summary["declaration_name_families"] == [
        {
            "suffix": "ge_one",
            "count": 2,
            "sample_declarations": ["A.alpha_ge_one", "A.beta_ge_one"],
        }
    ]
