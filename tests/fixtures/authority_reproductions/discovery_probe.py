"""Reproduce three historical discovery defects using an installed Ladon only.

Run with the chosen environment's Python and ``-I`` from outside a checkout.
The index fixture is lexical. The separate explanation row declares synthetic
rendered evidence so the probe can test lookup/comparison without running Lean.
Exit 0 means the requested behavior was observed, 1 means a behavior mismatch,
and 2 means setup or capture failed; setup failures never count as reproductions.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

TIMEOUT_SECONDS = 30
CAPTURE_BYTE_LIMIT = 1024 * 1024
HISTORICAL = "historical-defect-observed"
REPAIRED = "repaired-behavior-observed"
UNEXPECTED = "unexpected-behavior"


class ProbeSetupError(RuntimeError):
    """An operation required to establish a controlled fixture did not succeed."""


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def run(output: Path, name: str, arguments: list[str]) -> dict[str, Any]:
    """Capture one finite-deadline ordinary CLI process in the chosen runtime."""
    command = [sys.executable, "-I", "-m", "ladon.entrypoint", "proof-search", *arguments]
    environment = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME"):
        environment.pop(key, None)
    stdout, stderr = output / f"{name}.stdout", output / f"{name}.stderr"
    try:
        with stdout.open("wb") as out, stderr.open("wb") as err:
            completed = subprocess.run(
                command, cwd=output, env=environment, stdout=out, stderr=err,
                timeout=TIMEOUT_SECONDS, check=False,
            )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ProbeSetupError(f"{name}: CLI launch or deadline failed") from error
    record = {
        "id": name, "argv": command, "cwd": str(output), "exitCode": completed.returncode,
        "environmentRemoved": ["PYTHONPATH", "PYTHONHOME"],
        "timeoutSeconds": TIMEOUT_SECONDS,
        "stdout": stdout.name, "stderr": stderr.name,
        "stdoutDigest": digest(stdout), "stderrDigest": digest(stderr),
    }
    save(output / f"{name}.command.json", record)
    if max(stdout.stat().st_size, stderr.stat().st_size) > CAPTURE_BYTE_LIMIT:
        raise ProbeSetupError(f"{name}: captured output exceeded the byte limit")
    return record


def payload(output: Path, record: dict[str, Any]) -> dict[str, Any]:
    if record["exitCode"] != 0:
        raise ProbeSetupError(f"{record['id']}: fixture operation did not succeed")
    value = json.loads((output / record["stdout"]).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProbeSetupError(f"{record['id']}: CLI did not return a JSON object")
    return value


def select_type_command(output: Path) -> tuple[str, dict[str, Any]]:
    modern = run(output, "type-text-help", ["search", "type-text", "--help"])
    if modern["exitCode"] == 0:
        return "type-text", {"selected": "type-text", "retiredCommand": "type"}
    old = run(output, "historical-type-help", ["search", "type", "--help"])
    if old["exitCode"] != 0:
        raise ProbeSetupError("neither historical nor repaired type-search CLI is available")
    return "type", {
        "selected": "type", "replacementCommand": "type-text",
        "replacementUnavailableExitCode": modern["exitCode"],
    }


def create_explanation_database(path: Path) -> None:
    """Use a declared synthetic row, without pretending to have run Lean."""
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE declarations("
            "id TEXT,name TEXT,candidate_name TEXT,type_text TEXT,type_text_bytes INTEGER,"
            "type_text_truncated INTEGER,type_status TEXT,authority TEXT,module TEXT,"
            "path TEXT,line INTEGER,namespace TEXT,package TEXT,rendered_type TEXT,"
            "conclusion_text TEXT)"
        )
        connection.execute(
            "INSERT INTO declarations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("synthetic-proof", "Demo.proof", "Demo.proof", "True", 4, 0,
             "lean-rendered", "lean_environment", "Demo", "Demo.lean", 1,
             "Demo", "project", "True", "True"),
        )


def explanation_probe(output: Path, repository: Path) -> dict[str, Any]:
    database = output / "explanation.sqlite"
    create_explanation_database(database)
    record = run(output, "explain-name-versus-type", [
        "explain", "--repo-root", str(repository), "--index", str(database),
        "--goal", "True", "--candidate", "Demo.proof", "--module", "Demo",
        "--freshness", "stored", "--format", "json",
    ])
    result = payload(output, record)
    conclusion = result.get("normalization", {}).get("peeledConclusion")
    evidence = result.get("candidateEvidence", {})
    if evidence.get("typeText") != "True":
        raise ProbeSetupError("explanation fixture did not resolve its synthetic type evidence")
    observed = UNEXPECTED
    if conclusion == "Demo.proof" and result.get("classification") == "not-applicable":
        observed = HISTORICAL
    if conclusion == "True" and result.get("classification") == "exact-rendered-conclusion":
        observed = REPAIRED
    return {
        "id": "explain-compares-declaration-name-instead-of-indexed-type",
        "observation": observed, "commandRecord": "explain-name-versus-type.command.json",
        "candidate": "Demo.proof", "storedType": "True", "peeledConclusion": conclusion,
        "classification": result.get("classification"),
        "routeAccepted": result.get("routeCard", {}).get("accepted"),
        "fixtureAuthority": "Synthetic SQLite evidence row; no Lean execution.",
        "databaseDigest": digest(database),
    }


def build_index(output: Path, repository: Path) -> list[str]:
    common = [
        "--repo-root", str(repository), "--index", str(output / "index.sqlite"),
        "--format", "json",
    ]
    built = payload(output, run(output, "index-build", ["index", "build", *common]))
    if built.get("status") != "complete":
        raise ProbeSetupError("lexical fixture index was not completed")
    return common


def names(result: dict[str, Any]) -> list[str]:
    rows = result.get("results")
    if not isinstance(rows, list):
        raise ProbeSetupError("type query omitted its candidate result array")
    return [str(row["candidateName"]) for row in rows]


def scope_probe(output: Path, command: str, common: list[str]) -> dict[str, Any]:
    arguments = ["search", command, "--pattern", "Nat", "--freshness", "stored", *common]
    repository = payload(output, run(output, "type-repository-control", [
        *arguments, "--scope", "repository",
    ]))
    expected = ["value"]
    if names(repository) != expected:
        raise ProbeSetupError("repository control must expose the one lexical project declaration")
    external = payload(output, run(output, "type-external-scope", [
        *arguments, "--scope", "external",
    ]))
    selected = names(external)
    observed = HISTORICAL if selected == expected else REPAIRED if selected == [] else UNEXPECTED
    return {
        "id": "type-text-scope-is-ignored", "observation": observed,
        "commandRecord": "type-external-scope.command.json",
        "requestedScope": "external", "fixtureOwnership": "project-only lexical module",
        "repositoryControlCandidates": expected, "externalCandidates": selected,
        "scopeEvidence": external.get("coverage", {}).get("scope"),
    }


def freshness_probe(
    output: Path, repository: Path, command: str, common: list[str],
) -> dict[str, Any]:
    before = payload(output, run(output, "index-status-before", ["index", "status", *common]))
    if before.get("freshness") != "fresh":
        raise ProbeSetupError("fixture generation was not fresh before source editing")
    source = repository / "Main.lean"
    before_digest = digest(source)
    source.write_text("def value : Nat := 2\n", encoding="utf-8")
    after_digest = digest(source)
    after = payload(output, run(output, "index-status-after", ["index", "status", *common]))
    if not str(after.get("freshness", "")).startswith("stale") or before_digest == after_digest:
        raise ProbeSetupError("index status failed to establish controlled source drift")
    record = run(output, "type-verify-after-edit", [
        "search", command, "--pattern", "Nat", "--scope", "repository",
        "--freshness", "verify", *common,
    ])
    observation, detail = classify_freshness(output, record)
    return {
        "id": "verified-freshness-is-echoed-not-established", "observation": observation,
        "commandRecord": "type-verify-after-edit.command.json",
        "requestedFreshness": "verify", "beforeStatus": before["freshness"],
        "afterStatus": after["freshness"], "sourceBeforeDigest": before_digest,
        "sourceAfterDigest": after_digest, "queryExitCode": record["exitCode"], **detail,
    }


def classify_freshness(output: Path, record: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if record["exitCode"] == 0:
        result = payload(output, record)
        echoed = result.get("query", {}).get("freshness")
        observed = (HISTORICAL if echoed == "verify" and names(result) == ["value"]
                    and not result.get("freshnessEvidence") else UNEXPECTED)
        return observed, {"echoedFreshness": echoed, "returnedCandidates": names(result),
                          "freshnessEvidence": result.get("freshnessEvidence")}
    error = json.loads((output / record["stderr"]).read_text(encoding="utf-8"))
    diagnostic = error.get("diagnostic", {})
    rejected_stale = "stale" in str(diagnostic.get("message", "")).lower()
    no_stdout = not (output / record["stdout"]).read_bytes()
    return (REPAIRED if rejected_stale and no_stdout else UNEXPECTED), {
        "diagnosticCode": diagnostic.get("code"), "diagnosticMessage": diagnostic.get("message"),
    }


def run_probes(output: Path) -> dict[str, Any]:
    import ladon

    repository = output / "repository"
    repository.mkdir()
    (repository / "Main.lean").write_text("def value : Nat := 1\n", encoding="utf-8")
    (repository / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    command, migration = select_type_command(output)
    explanation = explanation_probe(output, repository)
    common = build_index(output, repository)
    scope = scope_probe(output, command, common)
    freshness = freshness_probe(output, repository, command, common)
    return {
        "schemaVersion": 1, "status": "completed", "probe": "discovery-correctness",
        "pythonExecutable": sys.executable, "pythonVersion": sys.version.split()[0],
        "packagePath": str(Path(ladon.__file__).resolve().parent),
        "packageVersion": importlib.metadata.version("ladon"),
        "probeDigest": digest(Path(__file__)), "commandMigration": migration,
        "leanExecuted": False, "observations": [explanation, scope, freshness],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expect", choices=("historical", "current", "either"), default="either")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    try:
        output.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        print(json.dumps({"status": "setup-failed", "reason": str(error)[:1000]}))
        return 2
    try:
        summary = run_probes(output)
    except (ProbeSetupError, OSError, ValueError, TypeError, KeyError, AttributeError,
            sqlite3.Error, ImportError) as error:
        summary = {"schemaVersion": 1, "status": "setup-failed", "errorType": type(error).__name__,
                   "reason": str(error)[:1000], "observations": []}
        save(output / "summary.json", summary)
        print(json.dumps(summary))
        return 2
    expected = {"historical": {HISTORICAL}, "current": {REPAIRED},
                "either": {HISTORICAL, REPAIRED}}[args.expect]
    summary["expectation"] = args.expect
    summary["expectationMet"] = all(row["observation"] in expected for row in summary["observations"])
    save(output / "summary.json", summary)
    save(output / "capture-inventory.json", {
        "schemaVersion": 1, "files": {
            str(path.relative_to(output)): digest(path)
            for path in sorted(output.rglob("*")) if path.is_file()
        },
    })
    print(json.dumps({"status": summary["status"], "expectationMet": summary["expectationMet"],
                      "observations": [row["observation"] for row in summary["observations"]],
                      "summaryPath": str(output / "summary.json")}))
    return 0 if summary["expectationMet"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
