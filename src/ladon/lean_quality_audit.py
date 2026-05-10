#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from .bifr_paper_theorem_qc_lib import check_manifest, load_manifest

TOOL_VERSION = "0.1.0"
DECL_RE = re.compile(
    r"^\s*(?:@[^\n]+\n\s*)*(def|theorem|lemma|structure|class|abbrev|instance|inductive)\s+([A-Za-z0-9_'.]+)",
    re.MULTILINE,
)
IMPORT_RE = re.compile(r"^import\s+([A-Za-z0-9_.]+)\s*$", re.MULTILINE)
DOC_MODULE_RE = re.compile(r"`([A-Z][A-Za-z0-9_.]*)`")
DOC_FILE_RE = re.compile(r"([A-Za-z0-9_./-]+\.lean)")
WARNING_RE = re.compile(r"warning:\s+([^:]+\.lean):(\d+):(\d+):\s+(.*)")

SEVERITY_ORDER = {"info": 0, "warn": 1, "review": 2}
CONFIDENCE_ORDER = {"heuristic": 0, "deterministic": 1}


@dataclass(frozen=True)
class Declaration:
    kind: str
    name: str


@dataclass
class ModuleInfo:
    module: str
    path: str
    imports: list[str]
    declarations: list[Declaration]
    fan_in: int = 0
    fan_out: int = 0


@dataclass
class Finding:
    id: str
    category: str
    severity: str
    confidence: str
    title: str
    summary: str
    files: list[str] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    remediation: str = ""


@dataclass
class ReportMetadata:
    tool_version: str
    generated_at_utc: str
    repo_root: str
    scope: list[str]
    docs: list[str]
    theorem_status_manifests: list[str]
    build_mode: str
    build_command: list[str] | None


@dataclass
class Report:
    metadata: ReportMetadata
    findings: list[Finding]
    summary: dict


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Internal Lean quality audit report generator")
    parser.add_argument("--root", default=".", help="Repository root to analyze")
    parser.add_argument(
        "--scope",
        action="append",
        default=[],
        help="Repo-relative directory to scan for Lean files. Repeatable. Defaults to Mf.",
    )
    parser.add_argument(
        "--doc-file",
        action="append",
        default=[],
        help="Repo-relative documentation file to audit. Repeatable.",
    )
    parser.add_argument("--build-log", help="Existing build log to parse instead of running a build")
    parser.add_argument(
        "--build-command",
        nargs="+",
        help="Build command to run for lint/build warning aggregation. Defaults to `lake build <scope>`.",
    )
    parser.add_argument("--skip-build", action="store_true", help="Skip build warning aggregation")
    parser.add_argument("--output-json", help="Path to write machine-readable report JSON")
    parser.add_argument("--output-text", help="Path to write human-readable summary")
    parser.add_argument("--generated-at-utc", help="Override report timestamp for deterministic tests")
    parser.add_argument(
        "--theorem-status-manifest",
        action="append",
        default=[],
        help="Repo-relative theorem-status manifest to check for theorem-surface QC findings.",
    )
    return parser.parse_args(argv)


def discover_lean_files(root: Path, scopes: Sequence[str]) -> list[Path]:
    files: list[Path] = []
    for scope in scopes:
        scope_path = root / scope
        if not scope_path.exists():
            continue
        files.extend(sorted(scope_path.rglob("*.lean")))
    return sorted(set(files))


def module_name(root: Path, file_path: Path) -> str:
    rel = file_path.relative_to(root)
    return ".".join(rel.with_suffix("").parts)


def parse_module(root: Path, file_path: Path) -> ModuleInfo:
    text = file_path.read_text(encoding="utf-8")
    imports = IMPORT_RE.findall(text)
    declarations = [Declaration(kind=m.group(1), name=m.group(2)) for m in DECL_RE.finditer(text)]
    return ModuleInfo(
        module=module_name(root, file_path),
        path=str(file_path.relative_to(root)),
        imports=imports,
        declarations=declarations,
    )


def categorize_warning(message: str) -> str:
    lowered = message.lower()
    if "unused simp argument" in lowered:
        return "unused_simp_argument"
    if "unused variable" in lowered:
        return "unused_variable"
    if "try 'simp' instead of 'simpa'" in lowered:
        return "unnecessary_simpa"
    if "flexible tactic" in lowered:
        return "flexible_tactic"
    if "100 character limit" in lowered:
        return "style_long_line"
    if "unreachable tactic" in lowered or "tactic does nothing" in lowered:
        return "unreachable_tactic"
    return "build_warning"


def load_build_lines(root: Path, args: argparse.Namespace) -> tuple[str, list[str], list[str]]:
    if args.skip_build:
        return "skipped", [], []
    if args.build_log:
        build_path = (root / args.build_log).resolve() if not Path(args.build_log).is_absolute() else Path(args.build_log)
        return "build_log", [str(build_path)], build_path.read_text(encoding="utf-8").splitlines()
    command = args.build_command or ["lake", "build", *(args.scope or ["Mf"])]
    proc = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    lines = (proc.stdout + "\n" + proc.stderr).splitlines()
    return "command", command, lines


def parse_build_warnings(root: Path, lines: Iterable[str]) -> dict[str, Counter]:
    by_file: dict[str, Counter] = defaultdict(Counter)
    for line in lines:
        match = WARNING_RE.search(line)
        if not match:
            continue
        raw_path, _lineno, _col, message = match.groups()
        normalized = raw_path.replace("\\", "/")
        try:
            rel = str(Path(normalized).relative_to(root)) if Path(normalized).is_absolute() else normalized
        except ValueError:
            rel = normalized
        by_file[rel][categorize_warning(message)] += 1
        by_file[rel]["total"] += 1
    return by_file


def normalize_doc_path(root: Path, raw_path: str) -> str | None:
    path = Path(raw_path)
    if path.is_absolute():
        try:
            return str(path.relative_to(root))
        except ValueError:
            return None
    if "/" not in raw_path and "\\" not in raw_path:
        return None
    return raw_path


def parse_doc_mentions(root: Path, doc_files: Sequence[str], known_module_basenames: set[str]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    referenced_modules: dict[str, set[str]] = {}
    referenced_paths: dict[str, set[str]] = {}
    for doc in doc_files:
        doc_path = root / doc
        if not doc_path.exists():
            referenced_modules[doc] = set()
            referenced_paths[doc] = set()
            continue
        text = doc_path.read_text(encoding="utf-8")
        module_mentions = {m for m in DOC_MODULE_RE.findall(text) if m in known_module_basenames}
        path_mentions = {
            normalized
            for normalized in (normalize_doc_path(root, raw) for raw in DOC_FILE_RE.findall(text))
            if normalized
        }
        referenced_modules[doc] = module_mentions
        referenced_paths[doc] = path_mentions
    return referenced_modules, referenced_paths


def remediation_for(category: str) -> str:
    remediations = {
        "import_hotspot": "Inspect whether the module is acting as an overloaded owner or accidental façade; consider splitting owner vs bridge surfaces.",
        "documentation_drift": "Update the reviewer-facing docs or remove stale references so the documented owner graph matches the codebase.",
        "lint_hotspot": "Tighten the module's lint baseline before larger refactors so later architecture work is less noisy and brittle.",
        "transit_import_surface": "Prefer importing authoritative owners directly and thin or remove the convenience surface if it no longer adds real discovery value.",
        "mixed_responsibility_module": "Review whether the module should be split into core, bridge, or application layers so ownership is easier to understand.",
    }
    return remediations.get(category, "Review the evidence and align the module with the intended owner graph.")


def generate_findings(
    modules: dict[str, ModuleInfo],
    build_warnings: dict[str, Counter],
    doc_files: Sequence[str],
    doc_module_mentions: dict[str, set[str]],
    doc_path_mentions: dict[str, set[str]],
    *,
    existing_doc_files: set[str],
) -> list[Finding]:
    findings: list[Finding] = []
    counter = 1

    def add_finding(category: str, severity: str, confidence: str, title: str, summary: str, *, files: list[str] | None = None, modules_list: list[str] | None = None, evidence: list[str] | None = None) -> None:
        nonlocal counter
        findings.append(
            Finding(
                id=f"F{counter:04d}",
                category=category,
                severity=severity,
                confidence=confidence,
                title=title,
                summary=summary,
                files=sorted(files or []),
                modules=sorted(modules_list or []),
                evidence=evidence or [],
                remediation=remediation_for(category),
            )
        )
        counter += 1

    for info in sorted(modules.values(), key=lambda m: (-m.fan_in, m.module)):
        if info.fan_in >= 3:
            add_finding(
                "import_hotspot",
                "review" if info.fan_in >= 5 else "info",
                "deterministic",
                f"High fan-in import hotspot: {info.module}",
                f"{info.module} is imported by {info.fan_in} modules, making it a likely architectural hotspot.",
                files=[info.path],
                modules_list=[info.module],
                evidence=[f"fan_in={info.fan_in}", f"fan_out={info.fan_out}", f"declarations={len(info.declarations)}"],
            )

    known_paths = {info.path for info in modules.values()}
    known_basenames = {Path(info.path).name for info in modules.values()}
    for doc in doc_files:
        missing_paths = sorted(path for path in doc_path_mentions.get(doc, set()) if Path(path).name in known_basenames and path not in known_paths)
        if missing_paths:
            add_finding(
                "documentation_drift",
                "warn",
                "deterministic",
                f"Documentation path drift in {doc}",
                f"{doc} references Lean files that do not exist at the documented path.",
                files=[doc],
                evidence=[f"missing_path={path}" for path in missing_paths],
            )
        elif doc not in existing_doc_files:
            add_finding(
                "documentation_drift",
                "review",
                "deterministic",
                f"Missing documentation audit target: {doc}",
                f"Configured doc file {doc} does not exist, so public-surface consistency could not be checked.",
                files=[doc],
                evidence=["doc_file_missing"],
            )

    for path, counts in sorted(build_warnings.items(), key=lambda item: (-item[1]["total"], item[0])):
        total = counts["total"]
        if total >= 1:
            top_category, top_count = max(((k, v) for k, v in counts.items() if k != "total"), key=lambda kv: kv[1])
            add_finding(
                "lint_hotspot",
                "warn" if total >= 3 else "info",
                "deterministic",
                f"Lean lint hotspot: {path}",
                f"{path} emitted {total} build/lint warnings, led by {top_category} ({top_count}).",
                files=[path],
                modules_list=[module_name_from_path(path)],
                evidence=[f"{kind}={count}" for kind, count in sorted(counts.items()) if kind != "total"],
            )

    for info in sorted(modules.values(), key=lambda m: (-m.fan_in, m.module)):
        if info.fan_in >= 2 and len(info.declarations) <= 3 and len(info.imports) >= 1:
            add_finding(
                "transit_import_surface",
                "review",
                "heuristic",
                f"Likely transit-import surface: {info.module}",
                f"{info.module} has fan-in {info.fan_in} but only {len(info.declarations)} top-level declarations, which suggests it may be imported mainly for convenience.",
                files=[info.path],
                modules_list=[info.module],
                evidence=[f"fan_in={info.fan_in}", f"declarations={len(info.declarations)}", f"imports={len(info.imports)}"],
            )
        decl_kinds = {decl.kind for decl in info.declarations}
        if len(info.declarations) >= 8 and len(decl_kinds) >= 4 and info.fan_out >= 3:
            add_finding(
                "mixed_responsibility_module",
                "review",
                "heuristic",
                f"Likely mixed-responsibility module: {info.module}",
                f"{info.module} combines many declaration kinds and imports, which is a common sign of blended architectural roles.",
                files=[info.path],
                modules_list=[info.module],
                evidence=[f"declarations={len(info.declarations)}", f"declaration_kinds={sorted(decl_kinds)}", f"fan_out={info.fan_out}"],
            )

    findings.sort(key=lambda f: (-SEVERITY_ORDER[f.severity], -CONFIDENCE_ORDER[f.confidence], f.category, f.id))
    return findings


def module_name_from_path(path: str) -> str:
    return ".".join(Path(path).with_suffix("").parts)


def summarize_findings(findings: list[Finding]) -> dict:
    by_category = Counter(f.category for f in findings)
    by_severity = Counter(f.severity for f in findings)
    hotspots = Counter()
    for finding in findings:
        for path in finding.files:
            hotspots[path] += 1
    top_hotspots = [{"path": path, "finding_count": count} for path, count in hotspots.most_common(10)]
    return {
        "total_findings": len(findings),
        "by_category": dict(sorted(by_category.items())),
        "by_severity": dict(sorted(by_severity.items())),
        "top_hotspots": top_hotspots,
    }


def theorem_line_structural_summaries(
    theorem_status_manifests: Sequence[str],
    root: Path,
    findings: list[Finding],
) -> list[dict]:
    summaries: list[dict] = []
    structural_categories = {
        "import_hotspot",
        "documentation_drift",
        "lint_hotspot",
        "transit_import_surface",
        "mixed_responsibility_module",
    }
    for manifest_arg in theorem_status_manifests:
        manifest_path = Path(manifest_arg)
        if not manifest_path.is_absolute():
            manifest_path = root / manifest_arg
        manifest = load_manifest(manifest_path)
        for line in manifest.get("theorem_lines", []):
            scope_files = set(line.get("theorem_local_structural_policy", {}).get("owner_files", []))
            scoped = [
                finding
                for finding in findings
                if finding.category in structural_categories
                and any(path in scope_files for path in finding.files)
            ]
            by_severity = Counter(f.severity for f in scoped)
            by_category = Counter(f.category for f in scoped)
            summaries.append(
                {
                    "line_id": line["id"],
                    "owner_files": sorted(scope_files),
                    "total_findings": len(scoped),
                    "by_severity": dict(sorted(by_severity.items())),
                    "by_category": dict(sorted(by_category.items())),
                }
            )
    return summaries


def render_text(report: Report) -> str:
    lines = []
    meta = report.metadata
    lines.append("Lean Quality Audit")
    lines.append(f"Version: {meta.tool_version}")
    lines.append(f"Root: {meta.repo_root}")
    lines.append(f"Scope: {', '.join(meta.scope)}")
    lines.append(f"Build mode: {meta.build_mode}")
    lines.append("")
    lines.append("Summary")
    lines.append(f"- total findings: {report.summary['total_findings']}")
    for severity, count in report.summary["by_severity"].items():
        lines.append(f"- {severity}: {count}")
    lines.append("")
    lines.append("Categories")
    for category, count in report.summary["by_category"].items():
        lines.append(f"- {category}: {count}")
    lines.append("")
    if report.summary["top_hotspots"]:
        lines.append("Hotspots")
        for hotspot in report.summary["top_hotspots"][:5]:
            lines.append(f"- {hotspot['path']}: {hotspot['finding_count']} findings")
        lines.append("")
    theorem_summaries = report.summary.get("theorem_line_structural_summaries", [])
    if theorem_summaries:
        lines.append("Theorem-Line Structural Summaries")
        for item in theorem_summaries:
            sev = item.get("by_severity", {})
            lines.append(
                f"- {item['line_id']}: total={item['total_findings']}, "
                f"review={sev.get('review', 0)}, warn={sev.get('warn', 0)}, info={sev.get('info', 0)}"
            )
        lines.append("")
    lines.append("Findings")
    for finding in report.findings:
        lines.append(f"- [{finding.severity}/{finding.confidence}] {finding.title}")
        lines.append(f"  category: {finding.category}")
        if finding.files:
            lines.append(f"  files: {', '.join(finding.files)}")
        if finding.modules:
            lines.append(f"  modules: {', '.join(finding.modules)}")
        lines.append(f"  summary: {finding.summary}")
        if finding.evidence:
            lines.append(f"  evidence: {'; '.join(finding.evidence)}")
        lines.append(f"  remediation: {finding.remediation}")
    return "\n".join(lines) + "\n"


def build_report(args: argparse.Namespace) -> Report:
    root = Path(args.root).resolve()
    scopes = args.scope or ["Mf"]
    doc_files = args.doc_file or [
        "docs/mf-paper-traceability/lean-runtime-crosswalk.md",
        "docs/LEAN-THEOREM-QUEUE.md",
    ]

    lean_files = discover_lean_files(root, scopes)
    modules = {info.module: info for info in (parse_module(root, path) for path in lean_files)}
    reverse_imports: dict[str, set[str]] = defaultdict(set)
    for info in modules.values():
        info.fan_out = len(info.imports)
        for imported in info.imports:
            reverse_imports[imported].add(info.module)
    for info in modules.values():
        info.fan_in = len(reverse_imports.get(info.module, set()))

    build_mode, build_command, build_lines = load_build_lines(root, args)
    build_warnings = parse_build_warnings(root, build_lines)

    known_basenames = {Path(info.path).stem for info in modules.values()}
    doc_module_mentions, doc_path_mentions = parse_doc_mentions(root, doc_files, known_basenames)

    existing_doc_files = {doc for doc in doc_files if (root / doc).exists()}
    findings = generate_findings(
        modules,
        build_warnings,
        doc_files,
        doc_module_mentions,
        doc_path_mentions,
        existing_doc_files=existing_doc_files,
    )
    for manifest_arg in args.theorem_status_manifest:
        manifest_path = Path(manifest_arg)
        if not manifest_path.is_absolute():
            manifest_path = root / manifest_path
        manifest = load_manifest(manifest_path)
        for index, finding in enumerate(check_manifest(root, manifest), start=1):
            findings.append(
                Finding(
                    id=f"tqc-{index:03d}",
                    category=finding["category"],
                    severity=finding["severity"],
                    confidence="deterministic",
                    title=finding["title"],
                    summary=finding["summary"],
                    files=sorted(finding.get("files", [])),
                    evidence=finding.get("evidence", []),
                    remediation=remediation_for(finding["category"]),
                )
            )
    summary = summarize_findings(findings)
    summary["theorem_line_structural_summaries"] = theorem_line_structural_summaries(
        args.theorem_status_manifest,
        root,
        findings,
    )
    metadata = ReportMetadata(
        tool_version=TOOL_VERSION,
        generated_at_utc=args.generated_at_utc
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        repo_root=str(root),
        scope=list(scopes),
        docs=list(doc_files),
        theorem_status_manifests=list(args.theorem_status_manifest),
        build_mode=build_mode,
        build_command=build_command,
    )
    return Report(metadata=metadata, findings=findings, summary=summary)


def write_outputs(report: Report, args: argparse.Namespace) -> None:
    json_payload = asdict(report)
    text_payload = render_text(report)
    if args.output_json:
        output_json = Path(args.output_json)
        if not output_json.is_absolute():
            output_json = Path(args.root) / output_json
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(json_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps(json_payload, indent=2, sort_keys=True))
    if args.output_text:
        output_text = Path(args.output_text)
        if not output_text.is_absolute():
            output_text = Path(args.root) / output_text
        output_text.parent.mkdir(parents=True, exist_ok=True)
        output_text.write_text(text_payload, encoding="utf-8")
    else:
        print(text_payload, file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = build_report(args)
    write_outputs(report, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
