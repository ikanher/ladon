"""Installed-CLI execution and separated result families for portable benchmarks."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ladon.analysis.benchmark_oracles import evaluate_oracles
from ladon.benchmark_contract import promotion_readiness
from ladon.benchmark_metrics import (
    classification_metrics,
    known_case_recall,
    semantic_parity,
)
from ladon.benchmark_process import MeasuredProcess, platform_capabilities, run_measured
from ladon.report_serialization import canonical_json_bytes


ReportValidator = Callable[[Mapping[str, Any]], None]
PROCESS_DEADLINE_SECONDS = 30.0


class BenchmarkFailure(RuntimeError):
    """Raised when an installed benchmark case violates a required contract."""


@dataclass(frozen=True)
class CaseContext:
    """Materialized paths and environment for one installed CLI case."""

    case: Mapping[str, Any]
    fixture: Path
    root: Path
    environment: Mapping[str, str]
    helper_log: Path


def run_portable_suite(
    candidate_root: Path,
    runtime_root: Path,
    analyzer: Path,
    environment: Mapping[str, str],
    manifest: Mapping[str, Any],
    validate_report: ReportValidator,
) -> dict[str, Any]:
    """Run required cases and return machine-readable separated metrics."""

    cases = [
        run_case(
            prepare_case(candidate_root, runtime_root, environment, case),
            analyzer,
            manifest["budgets"],
            validate_report,
        )
        for case in manifest["cases"]
        if case.get("required")
    ]
    labels = [
        label
        for case in manifest["cases"]
        if case.get("required")
        for label in case.get("labels", [])
    ]
    labels.extend(manifest.get("controlLabels", []))
    readiness = promotion_readiness(labels)
    return {
        "artifactKind": "ladon_signal_benchmark_results",
        "schemaVersion": 1,
        "manifest": {
            "schemaVersion": manifest["schemaVersion"],
            "productVersion": manifest["productVersion"],
            "reportVersion": manifest["reportVersion"],
        },
        "environment": platform_capabilities(),
        "cases": cases,
        "metricFamilies": summarize_metric_families(cases),
        "promotionReadiness": readiness,
        "passed": all(case["passed"] for case in cases)
        and all(row["ready"] for row in readiness),
        "nonClaims": [
            "Benchmark results characterize labeled Ladon behavior, not Lean theorem truth.",
            "Resource ceilings are broad synthetic regression bounds, not throughput guarantees.",
            "No composite repository-quality, proof-quality, or model-quality score is computed."
        ],
    }


def prepare_case(
    candidate_root: Path,
    runtime_root: Path,
    environment: Mapping[str, str],
    case: Mapping[str, Any],
) -> CaseContext:
    """Copy one fixture and create optional deterministic tool stand-ins."""

    case_root = runtime_root / "cases" / str(case["id"])
    fixture = case_root / "fixture"
    shutil.copytree(candidate_root / str(case["fixture"]), fixture)
    case_environment = dict(environment)
    helper_log = case_root / "helper-launches.log"
    if case.get("setup") == "fake_lake":
        install_fake_lake(case_root, fixture, helper_log, case_environment)
    return CaseContext(
        case=case,
        fixture=fixture,
        root=case_root,
        environment=case_environment,
        helper_log=helper_log,
    )


def install_fake_lake(
    case_root: Path,
    fixture: Path,
    helper_log: Path,
    environment: dict[str, str],
) -> None:
    """Install a PATH-local deterministic Lake stand-in for helper cases."""

    fake_bin = case_root / "bin"
    fake_bin.mkdir(parents=True)
    lake = fake_bin / "lake"
    lake.write_text(
        "\n".join(
            [
                f"#!{sys.executable}",
                "import json",
                "import os",
                "import subprocess",
                "import sys",
                "import time",
                "from pathlib import Path",
                "if sys.argv[1] == 'build':",
                "    for source in Path.cwd().rglob('*.lean'):",
                "        if source.name == 'lakefile.lean' or '.lake' in source.parts:",
                "            continue",
                "        relative = source.relative_to(Path.cwd()).with_suffix('.olean')",
                "        compiled = Path.cwd() / '.lake/build/lib/lean' / relative",
                "        compiled.parent.mkdir(parents=True, exist_ok=True)",
                "        if not compiled.exists():",
                "            compiled.write_bytes(b'portable-benchmark-olean-v1')",
                "    raise SystemExit(0)",
                "if sys.argv[1] != 'env':",
                "    raise SystemExit(2)",
                "if '--run' in sys.argv and any(",
                "    arg.endswith('ladon_elaborated_helper.lean') for arg in sys.argv",
                "):",
                "    payloads = json.loads(Path(",
                "        os.environ['LADON_BENCH_ELABORATED_PAYLOAD']",
                "    ).read_text(encoding='utf-8'))",
                "    module = sys.argv[-2]",
                "    print(json.dumps(payloads[module]))",
                "    raise SystemExit(0)",
                "if '--batch' not in sys.argv:",
                "    print('Lean (version 4.32.1, portable benchmark)')",
                "    raise SystemExit(0)",
                "log = Path(os.environ['LADON_BENCH_HELPER_LOG'])",
                "with log.open('a', encoding='utf-8') as stream:",
                "    stream.write('helper\\n')",
                "request = json.loads(Path(sys.argv[-1]).read_text(encoding='utf-8'))",
                "template = json.loads(Path(os.environ['LADON_BENCH_HELPER_PAYLOAD']).read_text(encoding='utf-8'))",
                "mode = os.environ.get('LADON_BENCH_FAKE_MODE', 'success')",
                "for index, row in enumerate(request['modules']):",
                "    payload = dict(template)",
                "    if row['module'] != 'Pkg.Surface.Deep':",
                "        payload = {**payload, 'header': {'imports': []}, 'commands': []}",
                "    print(json.dumps({",
                "        'frame': 'module',",
                "        'protocolVersion': request['protocolVersion'],",
                "        'requestIndex': row['requestIndex'],",
                "        'module': row['module'],",
                "        'file': row['file'],",
                "        'status': 'ok',",
                "        'payload': payload,",
                "    }, sort_keys=True), flush=True)",
                "    if mode == 'timeout' and index == 0:",
                "        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])",
                "        Path(os.environ['LADON_BENCH_CHILD_PID']).write_text(str(child.pid), encoding='utf-8')",
                "        time.sleep(60)",
                "print(json.dumps({",
                "    'frame': 'summary',",
                "    'protocolVersion': request['protocolVersion'],",
                "    'helperVersion': 'ladon-parser-helper-v2',",
                "    'leanVersion': 'portable-fake-lean-v1',",
                "    'requested': len(request['modules']),",
                "    'completed': len(request['modules']),",
                "    'failed': 0,",
                "}, sort_keys=True))",
                "",
            ]
        ),
        encoding="utf-8",
    )
    lake.chmod(lake.stat().st_mode | stat.S_IXUSR)
    environment["PATH"] = str(fake_bin) + os.pathsep + environment.get("PATH", "")
    environment["LADON_BENCH_HELPER_LOG"] = str(helper_log)
    environment["LADON_BENCH_HELPER_PAYLOAD"] = str(
        fixture / "fake-helper-payload.json"
    )
    environment["LADON_BENCH_ELABORATED_PAYLOAD"] = str(
        fixture / "fake-elaborated-payloads.json"
    )


def run_case(
    context: CaseContext,
    analyzer: Path,
    budgets: Mapping[str, Any],
    validate_report: ReportValidator,
) -> dict[str, Any]:
    """Run cold, equivalent, warm, and text representations for one case."""

    cold_payload, cold = run_json_representation(
        context,
        analyzer,
        cache_name="cache-a",
        output_name="cold.json",
    )
    cold_launches = helper_launch_count(context.helper_log)
    equivalent_payload, equivalent = run_json_representation(
        context,
        analyzer,
        cache_name="cache-b",
        output_name="equivalent.json",
    )
    equivalent_launches = helper_launch_count(context.helper_log) - cold_launches
    warm_payload, warm = run_json_representation(
        context,
        analyzer,
        cache_name="cache-a",
        output_name="warm.json",
    )
    warm_launches = (
        helper_launch_count(context.helper_log)
        - cold_launches
        - equivalent_launches
    )
    for payload in (cold_payload, equivalent_payload, warm_payload):
        validate_report(payload)
    text, text_process = run_text_representation(context, analyzer)
    labels = list(context.case.get("labels", []))
    oracle_results = evaluate_oracles(
        cold_payload,
        [oracle_with_fixture(label, context.case) for label in labels],
    )
    stability = stability_metrics(
        cold_payload,
        equivalent_payload,
        text,
        context,
        budgets,
    )
    resources = resource_metrics(
        cold,
        warm,
        text_process,
        cold_launches,
        warm_launches,
        budgets,
        context.case,
    )
    correctness = correctness_metrics(labels, oracle_results, cold_payload)
    passed = (
        all(row.passed for row in oracle_results)
        and stability["passed"]
        and resources["passed"]
    )
    return {
        "id": context.case["id"],
        "command": list(context.case["command"]),
        "reportVersion": context.case["reportVersion"],
        "correctness": correctness,
        "coverage": coverage_metrics(labels, oracle_results),
        "runtime": resources["runtime"],
        "memory": resources["memory"],
        "cache": resources["cache"],
        "process": resources["process"],
        "stability": stability,
        "passed": passed,
    }


def run_json_representation(
    context: CaseContext,
    analyzer: Path,
    *,
    cache_name: str,
    output_name: str,
) -> tuple[dict[str, Any], MeasuredProcess]:
    """Run one canonical JSON representation and parse its report."""

    output = context.root / output_name
    command = expand_command(
        context.case["command"],
        analyzer,
        context.fixture,
        context.root / cache_name,
        output,
    )
    measured = run_measured(
        command,
        cwd=context.root,
        environment=context.environment,
        timeout_seconds=PROCESS_DEADLINE_SECONDS,
    )
    require_success(context.case, measured)
    return json.loads(output.read_text(encoding="utf-8")), measured


def run_text_representation(
    context: CaseContext,
    analyzer: Path,
) -> tuple[str, MeasuredProcess]:
    """Run the same ordinary command with its documented text representation."""

    output = context.root / "report.txt"
    command = expand_command(
        context.case["command"],
        analyzer,
        context.fixture,
        context.root / "cache-text",
        output,
    )
    command = replace_option(command, "--format", "text")
    measured = run_measured(
        command,
        cwd=context.root,
        environment=context.environment,
        timeout_seconds=PROCESS_DEADLINE_SECONDS,
    )
    require_success(context.case, measured)
    return output.read_text(encoding="utf-8"), measured


def require_success(case: Mapping[str, Any], measured: MeasuredProcess) -> None:
    """Raise one concise error for a failed installed product command."""

    if measured.returncode == 0 and not measured.timed_out:
        return
    detail = measured.stderr.strip() or measured.stdout.strip()
    raise BenchmarkFailure(
        f"{case['id']}: installed ladon failed ({measured.returncode}): {detail}"
    )


def expand_command(
    command: Sequence[Any],
    analyzer: Path,
    fixture: Path,
    cache: Path,
    output: Path,
) -> list[str]:
    """Expand only documented harness path placeholders."""

    replacements = {
        "ladon": str(analyzer),
        "{fixture}": str(fixture),
        "{cache}": str(cache),
        "{output}": str(output),
    }
    return [replacements.get(str(token), str(token)) for token in command]


def replace_option(command: Sequence[str], option: str, value: str) -> list[str]:
    """Replace one required option value without changing analysis controls."""

    replaced = list(command)
    index = replaced.index(option)
    replaced[index + 1] = value
    return replaced


def oracle_with_fixture(
    label: Mapping[str, Any],
    case: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach stable case identity to one manifest oracle."""

    return {
        **dict(label["oracle"]),
        "fixture": case["id"],
    }


def correctness_metrics(
    labels: Sequence[Mapping[str, Any]],
    results: Sequence[Any],
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Return per-kind confusion metrics and missing-import split rows."""

    return {
        "byKind": classification_metrics(
            labels,
            [result.passed for result in results],
        ),
        "missingInternalRecall": known_case_recall(
            expected_internal_imports(labels),
            observed_internal_imports(payload),
        ),
        "externalAbsentFalsePositives": absent_import_false_positives(
            labels,
            results,
        ),
        "oracles": [result.to_json() for result in results],
    }


def expected_internal_imports(labels: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return reviewed positive internal-missing targets."""

    return [
        str(label["oracle"]["targetModule"])
        for label in labels
        if label["oracle"].get("signal") == "missing_internal_import"
        and label.get("expectedOutcome") == "present"
    ]


def observed_internal_imports(payload: Mapping[str, Any]) -> list[str]:
    """Return reported internal-missing targets."""

    return [
        str(row.get("targetModule"))
        for row in payload.get("module_dag", {}).get("missing_internal_imports", [])
    ]


def absent_import_false_positives(
    labels: Sequence[Mapping[str, Any]],
    results: Sequence[Any],
) -> int:
    """Count failed intentional-absence import oracles."""

    return sum(
        1
        for label, result in zip(labels, results, strict=True)
        if label["oracle"].get("signal") == "missing_internal_import"
        and label.get("expectedOutcome") == "absent"
        and not result.passed
    )


def coverage_metrics(
    labels: Sequence[Mapping[str, Any]],
    results: Sequence[Any],
) -> dict[str, Any]:
    """Return labeled extraction coverage without mixing correctness kinds."""

    selected = [
        (label, result)
        for label, result in zip(labels, results, strict=True)
        if label.get("metricFamily") == "coverage"
    ]
    expected = len(selected)
    hits = sum(result.passed for _label, result in selected)
    return {
        "expectedCount": expected,
        "hitCount": hits,
        "coverage": round(hits / expected, 6) if expected else None,
    }


def stability_metrics(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
    text: str,
    context: CaseContext,
    budgets: Mapping[str, Any],
) -> dict[str, Any]:
    """Return normalized determinism, semantic parity, and byte sizes."""

    first_bytes = canonical_json_bytes(first, normalize_timings=True)
    second_bytes = canonical_json_bytes(second, normalize_timings=True)
    parity = semantic_parity(first, text)
    json_size = len(first_bytes)
    text_size = len(text.encode("utf-8"))
    sizes_passed = (
        json_size <= int(budgets["jsonBytes"])
        and text_size <= int(budgets["textBytes"])
    )
    return {
        "schemaValid": True,
        "normalizedBytesEqual": first_bytes == second_bytes,
        "jsonBytes": json_size,
        "jsonBudgetBytes": budgets["jsonBytes"],
        "textBytes": text_size,
        "textBudgetBytes": budgets["textBytes"],
        "sizeBudgetsPassed": sizes_passed,
        "semanticParity": parity,
        "passed": first_bytes == second_bytes
        and parity["passed"]
        and sizes_passed,
        "budgetContext": context.case["reportVersion"],
    }


def resource_metrics(
    cold: MeasuredProcess,
    warm: MeasuredProcess,
    text: MeasuredProcess,
    cold_launches: int,
    warm_launches: int,
    budgets: Mapping[str, Any],
    case: Mapping[str, Any],
) -> dict[str, Any]:
    """Return runtime, memory, cache, and process families separately."""

    peak = max(
        value
        for value in (cold.peak_rss_mib, warm.peak_rss_mib, text.peak_rss_mib, 0.0)
        if value is not None
    )
    runtime = {
        "coldWallSeconds": round(cold.wall_seconds, 6),
        "warmWallSeconds": round(warm.wall_seconds, 6),
        "coldBudgetSeconds": budgets["coldWallSeconds"],
        "warmBudgetSeconds": budgets["warmWallSeconds"],
    }
    memory = {
        "peakRssMiB": peak if peak else None,
        "budgetMiB": budgets["peakRssMiB"],
        "supported": cold.peak_rss_mib is not None,
    }
    cache = cache_metrics(case, cold_launches, warm_launches)
    process = {
        "coldDescendantCount": cold.descendant_count,
        "helperLaunchesCold": cold_launches,
        "helperLaunchesWarm": warm_launches,
        "helperLaunchBudget": budgets["inventoryHelperLaunches"],
    }
    passed = (
        cold.wall_seconds <= float(budgets["coldWallSeconds"])
        and warm.wall_seconds <= float(budgets["warmWallSeconds"])
        and (not memory["supported"] or peak <= float(budgets["peakRssMiB"]))
        and cold_launches <= int(budgets["inventoryHelperLaunches"])
        and (case.get("setup") != "fake_lake" or warm_launches == 0)
    )
    return {
        "runtime": runtime,
        "memory": memory,
        "cache": cache,
        "process": process,
        "passed": passed,
    }


def cache_metrics(
    case: Mapping[str, Any],
    cold_launches: int,
    warm_launches: int,
) -> dict[str, Any]:
    """Return explicit cache applicability and launch-derived hit evidence."""

    if case.get("setup") != "fake_lake":
        return {
            "applicable": False,
            "reason": "text backend has no Lean helper cache",
        }
    return {
        "applicable": True,
        "coldHelperLaunches": cold_launches,
        "warmHelperLaunches": warm_launches,
        "warmHit": cold_launches > 0 and warm_launches == 0,
    }


def helper_launch_count(path: Path) -> int:
    """Return durable helper-launch rows from the fake-Lake boundary."""

    if not path.is_file():
        return 0
    return len(path.read_text(encoding="utf-8").splitlines())


def summarize_metric_families(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Return compact family summaries without a composite quality score."""

    return {
        "correctness": correctness_summary(cases),
        "coverage": coverage_summary(cases),
        "runtime": runtime_summary(cases),
        "memory": memory_summary(cases),
        "cache": cache_summary(cases),
        "process": process_summary(cases),
        "stability": stability_summary(cases),
    }


def correctness_summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Return aggregate failed-oracle count."""

    return {
        "failedOracleCount": sum(
            not row["passed"]
            for case in cases
            for row in case["correctness"]["oracles"]
        )
    }


def coverage_summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Return aggregate coverage counts."""

    return {
        "expectedCount": sum(case["coverage"]["expectedCount"] for case in cases),
        "hitCount": sum(case["coverage"]["hitCount"] for case in cases),
    }


def runtime_summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    """Return maximum cold and warm wall times."""

    return {
        "maxColdWallSeconds": max(case["runtime"]["coldWallSeconds"] for case in cases),
        "maxWarmWallSeconds": max(case["runtime"]["warmWallSeconds"] for case in cases),
    }


def memory_summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    """Return maximum supported peak RSS."""

    return {
        "maxPeakRssMiB": max(
            (case["memory"]["peakRssMiB"] or 0.0)
            for case in cases
        )
    }


def cache_summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Return cache applicability and warm-hit counts."""

    return {
        "applicableCaseCount": sum(case["cache"]["applicable"] for case in cases),
        "warmHitCount": sum(bool(case["cache"].get("warmHit")) for case in cases),
    }


def process_summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Return the largest helper-launch batch."""

    return {
        "maxHelperLaunches": max(
            case["process"]["helperLaunchesCold"]
            for case in cases
        )
    }


def stability_summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Return failed stability-case count."""

    return {
        "failedCaseCount": sum(not case["stability"]["passed"] for case in cases)
    }
