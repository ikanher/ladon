"""Installed-CLI execution protocol for the large-inventory gate."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.benchmark_process import MeasuredProcess, run_measured
from ladon.large_inventory_models import (
    ANALYSIS_COMMAND_TEMPLATE,
    REPRESENTATIONS,
    REQUIRED_DECLARATION_COUNT,
    REQUIRED_MODULE_COUNT,
    REQUIRED_SAMPLE_COUNT,
    REQUIRED_SOURCE_LINE_COUNT,
    LargeInventoryGateError,
    MeasuredRunner,
    ReportValidator,
    RepresentationRun,
    ScaleCeilings,
)
from ladon.large_inventory_normalization import (
    normalized_report_bytes,
    progress_cache_evidence,
    progress_phase_evidence,
)
from ladon.large_inventory_results import build_gate_artifact


def run_large_inventory_measurements(
    *,
    analyzer: Path,
    fixture_root: Path,
    runtime_root: Path,
    environment: Mapping[str, str],
    candidate_identity: Mapping[str, Any],
    fixture_identity: Mapping[str, Any],
    sample_count: int = REQUIRED_SAMPLE_COUNT,
    ceilings: ScaleCeilings | None = None,
    runner: MeasuredRunner = run_measured,
    report_validator: ReportValidator | None = None,
    require_large_fixture: bool = True,
) -> dict[str, Any]:
    """Measure cold/warm installed CLI runs and evaluate every exact ceiling."""

    ceilings = ceilings or ScaleCeilings()
    _require_protocol_inputs(
        analyzer,
        fixture_root,
        runtime_root,
        fixture_identity,
        sample_count,
        require_large_fixture=require_large_fixture,
    )
    outputs = runtime_root / "large-inventory-outputs"
    caches = runtime_root / "large-inventory-caches"
    outputs.mkdir(parents=True, exist_ok=True)
    caches.mkdir(parents=True, exist_ok=True)
    cold = _run_temperature(
        "cold",
        analyzer=analyzer,
        fixture_root=fixture_root,
        outputs=outputs,
        caches=caches,
        environment=environment,
        sample_count=sample_count,
        ceilings=ceilings,
        runner=runner,
        report_validator=report_validator,
    )
    warm = _run_temperature(
        "warm",
        analyzer=analyzer,
        fixture_root=fixture_root,
        outputs=outputs,
        caches=caches,
        environment=environment,
        sample_count=sample_count,
        ceilings=ceilings,
        runner=runner,
        report_validator=report_validator,
    )
    return build_gate_artifact(
        cold,
        warm,
        candidate_identity=candidate_identity,
        fixture_identity=fixture_identity,
        ceilings=ceilings,
        sample_count=sample_count,
    )


def _require_protocol_inputs(
    analyzer: Path,
    fixture_root: Path,
    runtime_root: Path,
    fixture_identity: Mapping[str, Any],
    sample_count: int,
    *,
    require_large_fixture: bool,
) -> None:
    if sample_count < REQUIRED_SAMPLE_COUNT:
        raise LargeInventoryGateError(
            f"large-inventory gate requires at least {REQUIRED_SAMPLE_COUNT} samples"
        )
    if not analyzer.is_file():
        raise LargeInventoryGateError(f"installed Ladon executable is absent: {analyzer}")
    if not fixture_root.is_dir():
        raise LargeInventoryGateError(f"generated fixture is absent: {fixture_root}")
    if runtime_root.resolve() == fixture_root.resolve():
        raise LargeInventoryGateError("fixture and measurement roots must be distinct")
    if require_large_fixture:
        _require_fixture_cardinalities(fixture_identity)


def _require_fixture_cardinalities(fixture_identity: Mapping[str, Any]) -> None:
    required = {
        "moduleCount": REQUIRED_MODULE_COUNT,
        "sourceLineCount": REQUIRED_SOURCE_LINE_COUNT,
        "declarationCount": REQUIRED_DECLARATION_COUNT,
    }
    short = {
        key: {"observed": fixture_identity.get(key), "minimum": minimum}
        for key, minimum in required.items()
        if not isinstance(fixture_identity.get(key), int)
        or int(fixture_identity[key]) < minimum
    }
    if short:
        raise LargeInventoryGateError(
            "generated fixture misses required cardinalities: "
            + json.dumps(short, sort_keys=True)
        )


def _run_temperature(
    temperature: str,
    *,
    analyzer: Path,
    fixture_root: Path,
    outputs: Path,
    caches: Path,
    environment: Mapping[str, str],
    sample_count: int,
    ceilings: ScaleCeilings,
    runner: MeasuredRunner,
    report_validator: ReportValidator | None,
) -> tuple[RepresentationRun, ...]:
    runs: list[RepresentationRun] = []
    for sample in range(1, sample_count + 1):
        for representation in REPRESENTATIONS:
            cache = caches / f"{representation}-{sample}"
            _require_cache_state(cache, temperature)
            runs.append(
                _run_representation(
                    temperature,
                    sample,
                    representation,
                    analyzer=analyzer,
                    fixture_root=fixture_root,
                    cache=cache,
                    output=outputs / f"{temperature}-{sample}.{_suffix(representation)}",
                    environment=environment,
                    ceilings=ceilings,
                    runner=runner,
                    report_validator=report_validator,
                )
            )
    return tuple(runs)


def _require_cache_state(cache: Path, temperature: str) -> None:
    populated = cache.is_dir() and any(cache.iterdir())
    if temperature == "cold" and populated:
        raise LargeInventoryGateError(f"cold cache is not empty: {cache}")
    if temperature == "warm" and not populated:
        raise LargeInventoryGateError(f"warm cache was not populated by cold run: {cache}")


def _run_representation(
    temperature: str,
    sample: int,
    representation: str,
    *,
    analyzer: Path,
    fixture_root: Path,
    cache: Path,
    output: Path,
    environment: Mapping[str, str],
    ceilings: ScaleCeilings,
    runner: MeasuredRunner,
    report_validator: ReportValidator | None,
) -> RepresentationRun:
    command = analysis_command(
        analyzer,
        fixture_root=fixture_root,
        cache=cache,
        output=output,
        representation=representation,
    )
    measured = runner(
        command,
        cwd=output.parent,
        environment=environment,
        timeout_seconds=_process_deadline(temperature, ceilings),
    )
    cache_evidence = progress_cache_evidence(measured.stderr)
    phase_progress = progress_phase_evidence(measured.stderr)
    process_error = _process_failure(
        measured,
        temperature,
        sample,
        representation,
    )
    if process_error is not None or not output.is_file():
        error = process_error or (
            f"{temperature} sample {sample} {representation} emitted no report"
        )
        return RepresentationRun(
            temperature,
            sample,
            representation,
            measured,
            0,
            _sha256(b""),
            cache_evidence,
            error=error,
            phase_progress=phase_progress,
        )
    raw = output.read_bytes()
    if representation == "text":
        return RepresentationRun(
            temperature,
            sample,
            representation,
            measured,
            len(raw),
            _sha256(raw),
            cache_evidence,
            phase_progress=phase_progress,
        )
    payload = _load_json_report(raw, temperature, sample)
    if report_validator is not None:
        report_validator(payload)
    normalized, normalized_fields = normalized_report_bytes(payload)
    return RepresentationRun(
        temperature,
        sample,
        representation,
        measured,
        len(raw),
        _sha256(raw),
        cache_evidence,
        normalized_sha256=_sha256(normalized),
        normalized_bytes=len(normalized),
        analysis_fingerprint=_analysis_fingerprint(payload),
        normalized_fields=normalized_fields,
        phase_progress=phase_progress,
    )


def analysis_command(
    analyzer: Path,
    *,
    fixture_root: Path,
    cache: Path,
    output: Path,
    representation: str,
) -> list[str]:
    """Return the ordinary public CLI command used by every scale sample."""

    if representation not in REPRESENTATIONS:
        raise ValueError(f"unsupported gate representation: {representation}")
    replacements = {
        "ladon": str(analyzer),
        "{fixture}": str(fixture_root),
        "{cache}": str(cache),
        "{representation}": representation,
        "{output}": str(output),
    }
    return [
        replacements.get(token, token)
        for token in ANALYSIS_COMMAND_TEMPLATE
    ]


def _process_deadline(
    temperature: str,
    ceilings: ScaleCeilings,
) -> float:
    ceiling = (
        ceilings.cold_wall_seconds
        if temperature == "cold"
        else ceilings.warm_wall_seconds
    )
    return max(ceiling * 2.0, ceiling + 5.0)


def _process_failure(
    measured: MeasuredProcess,
    temperature: str,
    sample: int,
    representation: str,
) -> str | None:
    if measured.returncode == 0 and not measured.timed_out:
        return None
    detail = measured.stderr.strip() or measured.stdout.strip()
    if len(detail) > 2_000:
        detail = detail[-2_000:]
    return (
        f"{temperature} sample {sample} {representation} failed "
        f"({measured.returncode}, timed_out={measured.timed_out}): {detail}"
    )


def _load_json_report(
    raw: bytes,
    temperature: str,
    sample: int,
) -> Mapping[str, Any]:
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LargeInventoryGateError(
            f"{temperature} sample {sample} emitted invalid JSON: {exc}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise LargeInventoryGateError("canonical JSON report must be an object")
    projection = payload.get("projection")
    if (
        not isinstance(projection, Mapping)
        or projection.get("name") != "review"
    ):
        raise LargeInventoryGateError(
            "canonical JSON report did not identify the review projection"
        )
    return payload


def _analysis_fingerprint(payload: Mapping[str, Any]) -> str | None:
    projection = payload.get("projection")
    if not isinstance(projection, Mapping):
        return None
    value = projection.get("analysis_fingerprint")
    return str(value) if isinstance(value, str) else None


def _suffix(representation: str) -> str:
    return "json" if representation == "json" else "txt"


def _sha256(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


__all__ = [
    "analysis_command",
    "run_large_inventory_measurements",
]
