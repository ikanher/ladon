"""Pure malformed checkpoint/term red tests for context-bridge checking."""
from __future__ import annotations

import importlib
import time

import pytest


def _api():
    return importlib.import_module("ladon.proof_contract_context_bridge")


def _request():
    return {"repoRoot": ".",
            "correspondenceRef": {"artifactRef": "sha256:" + "b" * 64,
                                  "kind": "correspondence", "localId": "correspondence:unowned"},
            "context": {"artifacts": []}, "deadlineMonotonic": time.monotonic() + 30,
            "limits": {"timeout_seconds": 30, "max_output_bytes": 8 * 1024**2,
                       "max_rss_bytes": 12 * 1024**3}}


def _assert_unresolved(result):
    assert result["wholeMethodAuthority"] == "none"
    assert result["mathematicalFalsity"] == "not-established"
    assert result.get("checkedGoals", []) == []
    assert result.get("status") in {"rejected", "incomplete", "unresolved"}


@pytest.mark.parametrize("plan_id", [None, "", {}, "sha256:" + "0" * 63])
def test_malformed_or_unknown_plan_id_never_reuses_a_plan(plan_id):
    result = _api().check_context_bridge(_request(), plan_id, {})
    _assert_unresolved(result)
    assert result.get("planId") is None


@pytest.mark.parametrize("terms", [
    None,
    [],
    {"unknown-goal": "by assumption"},
    {"goal:source-premise:0": 1},
    {"goal:source-premise:0": "x" * (8 * 1024**2 + 1)},
])
def test_malformed_terms_reject_without_claiming_checked_goals(terms):
    result = _api().check_context_bridge(_request(), "sha256:" + "c" * 64, terms)
    _assert_unresolved(result)


def test_cyclic_terms_fail_closed_and_expired_check_is_incomplete():
    terms = {}
    terms["goal:source-premise:0"] = terms
    cyclic = _api().check_context_bridge(_request(), "sha256:" + "d" * 64, terms)
    _assert_unresolved(cyclic)

    request = _request()
    request["deadlineMonotonic"] = time.monotonic() - 1
    expired = _api().check_context_bridge(request, "sha256:" + "d" * 64, {})
    assert expired["status"] == "incomplete"
    _assert_unresolved(expired)
