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
