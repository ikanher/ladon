from __future__ import annotations

from pathlib import Path

from ladon.evaluation_adapters import build_evaluation_adapters, evaluate_retrieval


def test_evaluation_adapters_report_availability_and_nonclaims() -> None:
    adapters = build_evaluation_adapters(Path("/repo"))
    assert {adapter.name for adapter in adapters} == {"ladon", "exact?", "apply?", "#check", "rg", "editor-search"}
    assert all(adapter.nonclaims for adapter in adapters)


def test_retrieval_metrics_keep_incorrect_suggestions_separate() -> None:
    metrics = evaluate_retrieval({"good", "wrong"}, {"good"})
    assert metrics["recall"] == 1.0
    assert metrics["incorrectSuggestionRate"] == 0.5


def test_retrieval_recall_is_not_assessed_without_expected_labels() -> None:
    metrics = evaluate_retrieval({"wrong"}, set())
    assert metrics["recall"] is None
    assert metrics["recallStatus"] == "not-assessed"
    assert metrics["incorrectSuggestionRate"] == 1.0
