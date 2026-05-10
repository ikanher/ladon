#!/usr/bin/env python3
from __future__ import annotations

import json
import fnmatch
import re
import subprocess
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("docs/mf-paper-traceability/bifr-paper-theorem-status.json")
DECL_RE = re.compile(
    r"^\s*(?:@[^\n]+\n\s*)*(def|theorem|lemma|structure|class|abbrev|instance|inductive)\s+([A-Za-z0-9_'.]+)",
    re.MULTILINE,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def module_to_path(root: Path, module: str) -> Path:
    return root / (module.replace(".", "/") + ".lean")


def parse_declaration_names(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return {match.group(2) for match in DECL_RE.finditer(text)}


def _change_tasks_complete(tasks_path: Path) -> tuple[bool, list[str]]:
    if not tasks_path.exists():
        return False, [f"missing_tasks={tasks_path.name}"]
    text = tasks_path.read_text(encoding="utf-8")
    remaining = text.count("- [ ]")
    if remaining:
        return False, [f"incomplete_tasks={remaining}"]
    return True, ["tasks_complete=true"]


def _archived_change_complete(archived_dir: Path) -> tuple[bool, list[str]]:
    evidence: list[str] = [f"archive_dir={archived_dir.name}"]
    required = [".openspec.yaml", "proposal.md", "design.md", "tasks.md"]
    missing_required = [name for name in required if not (archived_dir / name).exists()]
    if missing_required:
        evidence.extend([f"missing_file={name}" for name in missing_required])
        return False, evidence
    spec_files = list((archived_dir / "specs").rglob("spec.md")) if (archived_dir / "specs").exists() else []
    if not spec_files:
        evidence.append("missing_specs=true")
        return False, evidence
    tasks_complete, task_evidence = _change_tasks_complete(archived_dir / "tasks.md")
    evidence.extend(task_evidence)
    return tasks_complete, evidence


def _openspec_change_complete(root: Path, change: str) -> tuple[bool, list[str]]:
    proc = subprocess.run(
        ["openspec", "status", "--change", change, "--json"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return False, [f"openspec_status_failed={change}"]
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return False, [f"openspec_status_unparseable={change}"]
    evidence = [f"isComplete={payload.get('isComplete')}"]
    artifacts = payload.get("artifacts", [])
    if any(artifact.get("status") != "done" for artifact in artifacts):
        evidence.extend(
            [f"artifact:{artifact.get('id')}={artifact.get('status')}" for artifact in artifacts]
        )
        return False, evidence
    return bool(payload.get("isComplete")), evidence


def resolve_change_provenance_state(root: Path, change: str) -> dict[str, Any]:
    active_dir = root / "openspec" / "changes" / change
    if active_dir.exists():
        complete, evidence = _openspec_change_complete(root, change)
        return {
            "change": change,
            "state": "active-complete" if complete else "active-in-progress",
            "path": str(active_dir.relative_to(root)),
            "complete": complete,
            "evidence": evidence,
        }

    archive_root = root / "openspec" / "changes" / "archive"
    archived_candidates = sorted(archive_root.glob(f"*-{change}"))
    for archived_dir in reversed(archived_candidates):
        complete, evidence = _archived_change_complete(archived_dir)
        if complete:
            return {
                "change": change,
                "state": "archived-complete",
                "path": str(archived_dir.relative_to(root)),
                "complete": True,
                "evidence": evidence,
            }
    if archived_candidates:
        archived_dir = archived_candidates[-1]
        complete, evidence = _archived_change_complete(archived_dir)
        return {
            "change": change,
            "state": "archived-incomplete",
            "path": str(archived_dir.relative_to(root)),
            "complete": complete,
            "evidence": evidence,
        }
    return {
        "change": change,
        "state": "missing",
        "path": None,
        "complete": False,
        "evidence": ["change_missing=true"],
    }


def theorem_line_provenance_states(root: Path, line: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        resolve_change_provenance_state(root, change)
        for change in line.get("required_provenance_changes", line.get("required_openspec_changes", []))
    ]


def _severity(level: str) -> str:
    return level if level in {"info", "warn", "review"} else "review"


def _openspec_list(root: Path) -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["openspec", "list", "--json"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    return payload.get("changes", [])


def _git_dirty_paths(root: Path) -> list[str] | None:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    dirty: list[str] = []
    for raw_line in proc.stdout.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        path_part = line[3:]
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1]
        dirty.append(path_part)
    return dirty


def _path_allowlisted(path: str, allowlist: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in allowlist)


def _probe_payload(root: Path, probe_refs: list[str]) -> tuple[dict[str, Any] | None, list[str]]:
    for ref in probe_refs:
        candidate = root / ref
        if candidate.suffix == ".json" and candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8")), [f"probe_json={ref}"]
            except json.JSONDecodeError:
                return None, [f"probe_json_unparseable={ref}"]
    return None, ["probe_json_missing"]


def _probe_assertions_findings(
    *,
    root: Path,
    line: dict[str, Any],
    line_files: list[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    review_gate = line.get("review_gate", {})
    probe_contract = review_gate.get("adversarial_probe_contract", {})
    probe_refs = probe_contract.get("evidence_refs", [])
    payload, evidence = _probe_payload(root, probe_refs)
    if payload is None:
        findings.append(
            {
                "category": "theorem_surface_qc",
                "severity": "review",
                "title": f"Missing adversarial probe payload for {line['id']}",
                "summary": "The BIFR theorem QC manifest requires a JSON probe payload, but it is missing or unreadable.",
                "files": line_files,
                "evidence": evidence,
            }
        )
        return findings

    assertions = probe_contract.get("semantic_assertions", {})
    summary = payload.get("summary", {})
    results = payload.get("results", {})
    failures: list[str] = []

    for key, expected in assertions.get("summary_equal", {}).items():
        actual = summary.get(key)
        if actual != expected:
            failures.append(f"summary_equal:{key}={actual!r} expected {expected!r}")

    for key, minimum in assertions.get("summary_min", {}).items():
        actual = summary.get(key)
        if actual is None or actual < minimum:
            failures.append(f"summary_min:{key}={actual!r} < {minimum!r}")

    for result_key, minimum in assertions.get("result_last_min", {}).items():
        rows = results.get(result_key, [])
        actual = rows[-1]["paper_error_over_scale"] if rows else None
        if actual is None or actual < minimum:
            failures.append(f"result_last_min:{result_key}={actual!r} < {minimum!r}")

    if failures:
        findings.append(
            {
                "category": "theorem_surface_qc",
                "severity": "review",
                "title": f"Semantic adversarial-probe assertions failed for {line['id']}",
                "summary": "The BIFR obstruction-family probe exists, but the configured semantic assertions do not hold.",
                "files": line_files,
                "evidence": [*evidence, *failures],
            }
        )
    return findings


def check_manifest(
    root: Path,
    manifest: dict[str, Any],
    *,
    enforce_review_blockers: bool = True,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    status_vocab = set(manifest.get("status_vocabulary", []))
    promotion_states = list(manifest.get("promotion_states", []))
    state_index = {state: idx for idx, state in enumerate(promotion_states)}

    if not manifest.get("theorem_lines"):
        findings.append(
            {
                "category": "theorem_surface_qc",
                "severity": "review",
                "title": "Missing theorem-line entries",
                "summary": "The BIFR theorem QC manifest has no theorem_lines entries.",
                "files": [str(DEFAULT_MANIFEST)],
                "evidence": ["theorem_lines_empty"],
            }
        )
        return findings

    for line in manifest["theorem_lines"]:
        line_id = line["id"]
        line_files = [str(DEFAULT_MANIFEST)]
        for field in ("small_branch_status", "large_branch_status", "successor_surface_status"):
            status = line.get(field)
            if status not in status_vocab:
                findings.append(
                    {
                        "category": "theorem_surface_qc",
                        "severity": "review",
                        "title": f"Unknown theorem status in {line_id}",
                        "summary": f"{field}={status!r} is not in the declared BIFR status vocabulary.",
                        "files": line_files,
                        "evidence": [f"field={field}", f"value={status!r}"],
                    }
                )

        review_gate = line.get("review_gate", {})
        promotion_state = review_gate.get("promotion_state")
        if promotion_state not in state_index:
            findings.append(
                {
                    "category": "theorem_surface_qc",
                    "severity": "review",
                    "title": f"Unknown promotion state in {line_id}",
                    "summary": f"promotion_state={promotion_state!r} is not in the declared promotion ladder.",
                    "files": line_files,
                    "evidence": [f"promotion_state={promotion_state!r}"],
                }
            )
        elif review_gate.get("review_ready") and promotion_state != "review_ready":
            findings.append(
                {
                    "category": "theorem_surface_qc",
                    "severity": "review",
                    "title": f"Review-ready flag mismatch in {line_id}",
                    "summary": "review_ready=true requires promotion_state=review_ready.",
                    "files": line_files,
                    "evidence": [f"promotion_state={promotion_state}"],
                }
            )

        probe_contract = review_gate.get("adversarial_probe_contract", {})
        if review_gate.get("review_ready") and (
            not probe_contract.get("satisfied") or not probe_contract.get("evidence_refs")
        ):
            findings.append(
                {
                    "category": "theorem_surface_qc",
                    "severity": "review",
                    "title": f"Missing adversarial probe evidence in {line_id}",
                    "summary": "review_ready promotion is blocked because the adversarial probe contract is not satisfied.",
                    "files": line_files,
                    "evidence": ["probe_contract_unsatisfied"],
                }
            )
        if enforce_review_blockers and probe_contract.get("satisfied"):
            findings.extend(
                _probe_assertions_findings(root=root, line=line, line_files=line_files)
            )

        if enforce_review_blockers:
            superseded = set(line.get("superseded_openspec_changes", []))
            if superseded:
                active_changes = [
                    change["name"]
                    for change in _openspec_list(root)
                    if change.get("name") in superseded and change.get("status") == "in-progress"
                ]
                if active_changes:
                    findings.append(
                        {
                            "category": "theorem_surface_qc",
                            "severity": "review",
                            "title": f"Superseded theorem-route changes still active for {line_id}",
                            "summary": "Strict BIFR review is blocked while superseded pre-reset large-branch changes remain in progress.",
                            "files": line_files,
                            "evidence": [f"stale_change={change}" for change in sorted(active_changes)],
                        }
                    )

            worktree_policy = line.get("worktree_policy", {})
            if worktree_policy:
                dirty_paths = _git_dirty_paths(root)
                if dirty_paths is None:
                    findings.append(
                        {
                            "category": "theorem_surface_qc",
                            "severity": "review",
                            "title": f"Unable to inspect git worktree for {line_id}",
                            "summary": "Strict BIFR review requires dirty-worktree inspection, but `git status --porcelain` failed.",
                            "files": line_files,
                            "evidence": ["git_status_failed"],
                        }
                    )
                else:
                    allowlist = worktree_policy.get("allowed_dirty_paths", [])
                    blocked = [
                        path for path in dirty_paths if not _path_allowlisted(path, allowlist)
                    ]
                    if blocked:
                        limit = worktree_policy.get("max_reported_blockers", 20)
                        findings.append(
                            {
                                "category": "theorem_surface_qc",
                                "severity": "review",
                                "title": f"Dirty worktree blocks strict review for {line_id}",
                                "summary": "Strict BIFR review requires a clean or allowlisted checkout; unallowlisted dirty paths are present.",
                                "files": line_files,
                                "evidence": [
                                    f"dirty_count={len(blocked)}",
                                    *[f"dirty_path={path}" for path in blocked[:limit]],
                                ],
                            }
                        )

        for module in (
            line.get("canonical_lean_owners", [])
            + line.get("support_lean_owners", [])
            + line.get("historical_lean_owners", [])
            + [line.get("blocking_obstruction_owner"), line.get("reset_owner")]
        ):
            if not module:
                continue
            module_path = module_to_path(root, module)
            if not module_path.exists():
                findings.append(
                    {
                        "category": "theorem_surface_qc",
                        "severity": "review",
                        "title": f"Missing Lean owner for {line_id}",
                        "summary": f"Configured Lean module {module} does not exist at the expected path.",
                        "files": [str(module_path.relative_to(root))],
                        "evidence": [f"module={module}"],
                    }
                )
                continue
            required_declarations = line.get("required_lean_declarations", {}).get(module, [])
            if required_declarations:
                declarations = parse_declaration_names(module_path)
                missing = [
                    name for name in required_declarations if name not in declarations
                ]
                if missing:
                    findings.append(
                        {
                            "category": "theorem_surface_qc",
                            "severity": "review",
                            "title": f"Missing required Lean declarations for {line_id}",
                            "summary": f"{module} is missing required theorem-surface declaration names.",
                            "files": [str(module_path.relative_to(root))],
                            "evidence": [f"missing_declaration={name}" for name in missing],
                        }
                    )

        for change in line.get("required_openspec_changes", []):
            raise AssertionError("required_openspec_changes is deprecated; use required_provenance_changes")

        for state in theorem_line_provenance_states(root, line):
            if state["state"] in {"active-complete", "archived-complete"}:
                continue
            title = (
                f"Missing required provenance change for {line_id}"
                if state["state"] == "missing"
                else f"Incomplete required provenance change for {line_id}"
            )
            summary = (
                f"Configured required provenance change {state['change']} is missing."
                if state["state"] == "missing"
                else f"Configured required provenance change {state['change']} is not complete."
            )
            files = [state["path"]] if state["path"] else line_files
            findings.append(
                {
                    "category": "theorem_surface_qc",
                    "severity": "review",
                    "title": title,
                    "summary": summary,
                    "files": files,
                    "evidence": [f"change={state['change']}", f"change_state={state['state']}", *state["evidence"]],
                }
            )

        for doc_expectation in line.get("consistency_targets", {}).get("docs", []):
            doc_path = root / doc_expectation["path"]
            if not doc_path.exists():
                findings.append(
                    {
                        "category": "theorem_surface_qc",
                        "severity": "review",
                        "title": f"Missing QC target file for {line_id}",
                        "summary": f"Configured QC target {doc_expectation['path']} does not exist.",
                        "files": [doc_expectation["path"]],
                        "evidence": ["target_missing"],
                    }
                )
                continue
            text = doc_path.read_text(encoding="utf-8")
            missing = [s for s in doc_expectation.get("required_substrings", []) if s not in text]
            if missing:
                findings.append(
                    {
                        "category": "theorem_surface_qc",
                        "severity": _severity(doc_expectation.get("severity", "review")),
                        "title": f"QC narrative drift in {doc_expectation['path']}",
                        "summary": f"{doc_expectation['path']} is missing required BIFR QC gate phrases for {line_id}.",
                        "files": [doc_expectation["path"]],
                        "evidence": [f"missing={value}" for value in missing],
                    }
                )
    return findings
