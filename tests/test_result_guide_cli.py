"""CLI boundary and offline behavior for result guide projection."""

from __future__ import annotations

import json
import socket
import subprocess

from support.result_guide import guide_inputs


def _write_inputs(tmp_path):
    manifest, artifacts, guide = guide_inputs()
    manifest_path = tmp_path / "manifest.json"
    guide_path = tmp_path / "guide.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    guide_path.write_text(json.dumps(guide, ensure_ascii=False), encoding="utf-8")
    artifact_paths = []
    for index, artifact in enumerate(artifacts):
        path = tmp_path / f"artifact-{index}.json"
        path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
        artifact_paths.append(path)
    return manifest_path, guide_path, artifact_paths


def _argv(manifest, guide, artifacts, *extra):
    argv = ["result", "guide", str(manifest), "--guide-inputs", str(guide)]
    for path in artifacts:
        argv.extend(["--artifact", str(path)])
    argv.extend(extra)
    return argv


def test_guide_cli_is_offline_has_matching_text_and_preserves_inspect_contract(
    monkeypatch, tmp_path, capsys
):
    from ladon.entrypoint import main

    def forbidden(*_args, **_kwargs):
        raise AssertionError("result guide attempted process or network activity")

    manifest, guide, artifacts = _write_inputs(tmp_path)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)

    assert main(_argv(manifest, guide, artifacts, "--section", "steps", "--limit", "20")) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["operation"] == "guide"
    assert [row["id"] for row in result["rows"]] == ["condition", "argument"]
    assert result["scope"] == "offline-supplied-evidence"

    assert (
        main(
            _argv(
                manifest,
                guide,
                artifacts,
                "--section",
                "steps",
                "--limit",
                "20",
                "--format",
                "text",
            )
        )
        == 0
    )
    decoded = {
        key: json.loads(value)
        for key, value in (line.split(": ", 1) for line in capsys.readouterr().out.splitlines())
    }
    assert decoded == result

    _assert_inspect_unchanged(main, manifest, artifacts, capsys)


def _assert_inspect_unchanged(main, manifest, artifacts, capsys):
    inspect_argv = ["result", "inspect", str(manifest), "--section", "targets"]
    for path in artifacts:
        inspect_argv.extend(["--artifact", str(path)])
    assert main(inspect_argv) == 0
    inspect_result = json.loads(capsys.readouterr().out)
    assert inspect_result["operation"] == "inspect"
    assert inspect_result["schema"] == "ladon-result-inspection-v1"
    assert "guideStatus" not in inspect_result
    assert inspect_result["rows"]


def test_guide_cli_validates_full_companion_before_selector_and_writes_no_success_output(
    tmp_path, capsys
):
    from ladon.entrypoint import main

    manifest, guide, artifacts = _write_inputs(tmp_path)
    invalid = json.loads(guide.read_text(encoding="utf-8"))
    invalid["citations"][0]["revision"] = "sha256:" + "0" * 64
    guide.write_text(json.dumps(invalid), encoding="utf-8")
    result = main(_argv(manifest, guide, artifacts, "--section", "steps", "--claim", "paper-theorem-1"))
    assert result != 0
    captured = capsys.readouterr()
    assert not captured.out
    diagnostic = json.loads(captured.err)
    assert diagnostic["operation"] == "guide"
    assert diagnostic["status"] == "failed"


def test_guide_cli_rejects_unknown_exact_selectors_without_partial_view(tmp_path, capsys):
    from ladon.entrypoint import main

    manifest, guide, artifacts = _write_inputs(tmp_path)
    result = main(
        _argv(manifest, guide, artifacts, "--section", "steps", "--target", "missing-target")
    )
    assert result != 0
    captured = capsys.readouterr()
    assert not captured.out
    assert json.loads(captured.err)["operation"] == "guide"
