from __future__ import annotations

import json
from pathlib import Path

import pytest
from support.proofir_v3_native import claim_artifact

from ladon import proofir_v3_cli
from ladon.proofir_v3 import canonical_bytes
from ladon.proofir_v3_cli import proofir_v3_main


def test_v3_cli_validates_and_canonicalizes_through_ordinary_command(
    tmp_path: Path,
) -> None:
    artifact = claim_artifact()
    source = tmp_path / "artifact.json"
    source.write_text(json.dumps(artifact), encoding="utf-8")
    assert proofir_v3_main(["validate", str(source)]) == 0
    canonical = tmp_path / "canonical.json"
    assert proofir_v3_main(["canonicalize", str(source), "--out", str(canonical)]) == 0
    assert canonical.read_bytes() == canonical_bytes(artifact)


def test_v3_cli_canonicalize_stdout_is_exact_canonical_bytes(
    tmp_path: Path, capsys
) -> None:
    artifact = claim_artifact()
    source = tmp_path / "artifact.json"
    source.write_text(json.dumps(artifact), encoding="utf-8")

    assert proofir_v3_main(["canonicalize", str(source)]) == 0
    assert capsys.readouterr().out.encode("utf-8") == canonical_bytes(artifact)


def test_v3_cli_reports_bounded_progress_and_rejects_oversized_input(
    tmp_path: Path, capsys
) -> None:
    artifact = claim_artifact()
    source = tmp_path / "artifact.json"
    source.write_text(json.dumps(artifact), encoding="utf-8")
    assert proofir_v3_main(["validate", str(source), "--progress"]) == 0
    progress = capsys.readouterr().err
    assert '"schema": "ladon-proofir-progress-v1"' in progress
    assert '"inputBytes"' in progress
    assert (
        proofir_v3_main(["validate", str(source), "--max-input-mib", "0.000001"]) == 2
    )
    assert "input byte limit" in capsys.readouterr().err


def test_v3_cli_atomic_output_leaves_no_temporary_file(tmp_path: Path) -> None:
    artifact = claim_artifact()
    source = tmp_path / "artifact.json"
    source.write_text(json.dumps(artifact), encoding="utf-8")
    output = tmp_path / "canonical.json"
    assert proofir_v3_main(["canonicalize", str(source), "--out", str(output)]) == 0
    assert output.is_file()
    assert not (tmp_path / ".canonical.json.tmp").exists()


def test_v3_cli_output_cap_preserves_prior_destination(tmp_path: Path, capsys) -> None:
    source = tmp_path / "artifact.json"
    source.write_text(json.dumps(claim_artifact()), encoding="utf-8")
    output = tmp_path / "canonical.json"
    output.write_bytes(b"prior-destination")

    assert (
        proofir_v3_main(
            [
                "canonicalize",
                str(source),
                "--out",
                str(output),
                "--max-output-mib",
                "0.000001",
            ]
        )
        == 2
    )
    assert "output byte limit" in capsys.readouterr().err
    assert output.read_bytes() == b"prior-destination"
    assert not (tmp_path / ".canonical.json.tmp").exists()


def test_v3_cli_rechecks_deadline_after_validation_before_publish(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "artifact.json"
    source.write_text(json.dumps(claim_artifact()), encoding="utf-8")
    output = tmp_path / "canonical.json"
    output.write_bytes(b"prior-destination")
    times = iter((0.0, 0.0, 2.0))
    monkeypatch.setattr(proofir_v3_cli.time, "monotonic", lambda: next(times))

    assert (
        proofir_v3_main(
            [
                "canonicalize",
                str(source),
                "--out",
                str(output),
                "--deadline-seconds",
                "1",
            ]
        )
        == 2
    )
    assert "deadline" in capsys.readouterr().err
    assert output.read_bytes() == b"prior-destination"


def test_v3_cli_rejects_retired_convert_before_reading_input(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        proofir_v3_main(
            [
                "convert",
                str(tmp_path / "missing.json"),
                "--out",
                str(tmp_path / "out.json"),
            ]
        )
