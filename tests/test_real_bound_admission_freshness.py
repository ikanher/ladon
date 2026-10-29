"""Fresh source/environment binding rejects reuse even when names are unchanged."""

import hashlib
from types import SimpleNamespace

import pytest
from test_real_bound_admission_plan import request

from ladon.real_bound_admission import plan_prefix_admission
from ladon.real_bound_admission_check import verify_plan_source


def fixture_plan(tmp_path, monkeypatch):
    import ladon.real_bound_admission_check as checking

    data = b"def sameName := True\n"
    (tmp_path / "PrefixExamples.lean").write_bytes(data)
    value = request()
    value["source"]["sha256"] = hashlib.sha256(data).hexdigest()
    monkeypatch.setattr(checking, "pinned_toolchain", lambda _root:
                        SimpleNamespace(context_identity=value["environmentRef"]))
    return plan_prefix_admission(value)


def test_changed_definition_same_name_rejects_original_plan(tmp_path, monkeypatch):
    plan = fixture_plan(tmp_path, monkeypatch)
    verify_plan_source(tmp_path, plan)
    (tmp_path / "PrefixExamples.lean").write_text("def sameName := False\n")
    with pytest.raises(ValueError, match="stale.*source"):
        verify_plan_source(tmp_path, plan)


def test_changed_environment_rejects_unchanged_source(tmp_path, monkeypatch):
    import ladon.real_bound_admission_check as checking

    plan = fixture_plan(tmp_path, monkeypatch)
    monkeypatch.setattr(checking, "pinned_toolchain", lambda _root:
                        SimpleNamespace(context_identity="sha256:" + "0" * 64))
    with pytest.raises(ValueError, match="stale.*environment"):
        verify_plan_source(tmp_path, plan)
