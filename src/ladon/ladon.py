#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR

from . import lean_quality_audit as audit

TOOL_VERSION = "0.1.0"
REPORT_VERSION = "1"
STRONG_ROOT_POLICIES = {"explicit"}
GENERATED_MODULE_MARKERS = (".Generated", ".Auto", ".Gen")
DEFAULT_DOC_CANDIDATES = (
    "docs/mf-paper-traceability/lean-runtime-crosswalk.md",
    "docs/LEAN-THEOREM-QUEUE.md",
)
DEFAULT_LEAN_PARSER_HELPER = Path(
    str(resources.files("ladon").joinpath("lean", "ladon_parser_helper.lean"))
)
SIMP_LIKE_RE = re.compile(r"\b(?:simp|simpa|simp_all)\b")
BROAD_SIMP_RE = re.compile(r"\b(?:simp|simpa|simp_all)\b(?:\s*\[[^\]]*\])?\s+at\b")
RW_RE = re.compile(r"\brw\b")
BY_CASES_RE = re.compile(r"\bby_cases\b")
HAVE_RE = re.compile(r"\bhave\b")
CALC_RE = re.compile(r"(^|\n)\s*calc\b")
CALC_STEP_RE = re.compile(r"(^|\n)\s*(?:_|\S.*?)\s*=\s*.*")
STRUCTURE_DECL_RE = re.compile(r"^\s*structure\s+([A-Za-z0-9_'.]+)", re.MULTILINE)
STRUCTURE_FIELD_RE = re.compile(r"^\s{2,}([A-Za-z_][A-Za-z0-9_']*)\s*:", re.MULTILINE)
STRUCTURE_FIELD_LINE_RE = re.compile(r"^(?P<indent>\s{2,})(?P<name>[A-Za-z_][A-Za-z0-9_']*)\s*:\s*(?P<type>.*)$")
DECL_START_RE = re.compile(
    r"^\s*(?:@[^\n]+\n\s*)*(?:def|theorem|lemma|structure|class|abbrev|instance|inductive)\s+",
    re.MULTILINE,
)
REPEATED_SEMANTIC_EXPR_RE = re.compile(
    r"\b[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)+\s*(?:[-+*/])\s*\d+\b"
)
CERTIFICATE_STRUCTURE_RE = re.compile(
    r"(?:Certificate|Confidence|Imported|Selected|Grid|Witness|Artifact|Verifier|Bound)",
    re.IGNORECASE,
)
CERTIFICATE_FIELD_RE = re.compile(
    r"(?:imported|HighConfidence|highConfidence|_valid\b|Valid\b|_le_target\b|sound|certified|upper.*target|confidence|witness|artifact|evidence|runtime|proof)",
    re.IGNORECASE,
)
PROP_SHAPE_RE = re.compile(r"(?:\bProp\b|≤|≥|→|↔|∀|∃|∈|:=\s*by|\s=\s|<|>)")
PYTHON_WITNESS_RE = re.compile(
    r"(?:witness|checker|validate|validation|certificate|artifact|alpha[_-]?ledger|candidate[_-]?rmse)",
    re.IGNORECASE,
)
THEOREM_SURFACE_RE = re.compile(
    r"(?:[A-Za-z0-9_./-]+\.lean|[A-Z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_']+)+|openspec/(?:changes|specs)/|(?i:Lean/OpenSpec|OpenSpec\s+(?:change|spec|umbrella)|theorem surface|theorem-facing|Requirement:))",
)
PYTHON_WITNESS_BOUNDARY_RE = re.compile(
    r"LADON-WITNESS-SCOPE\s*:\s*(?:diagnostic-only|debug-only|debugging-only|exploratory-only|test-only)",
    re.IGNORECASE,
)
WITNESS_PATH_RE = re.compile(r"witnesses/[A-Za-z0-9_./-]+")
CERTIFICATE_BOUNDARY_CATEGORIES = {
    "imported_certificate_seam",
    "prop_field_certificate_assumption",
    "python_witness_without_theorem_surface",
    "json_witness_without_theorem_surface",
    "json_witness_missing_lean_owner",
    "runtime_artifact_contract_gap",
    "exported_surface_unverified",
    "source_export_mismatch",
    "source_export_mismatch_stale_build_suspected",
}
CLOSURE_EXPLOSION_MODULE_THRESHOLD = 64
CLOSURE_EXPLOSION_DECLARATION_THRESHOLD = 1000
CLOSURE_EXPLOSION_DIRECT_IMPORT_THRESHOLD = 3
REFERENCE_GRAPH_RESOLUTION_WARN_RATIO = 0.35
PROOF_HOLE_RE = re.compile(r"\b(?:sorry|admit|axiom|unsafe)\b")
LOCAL_SCRIPT_RE = re.compile(
    r"(?:diagnose|audit|certify|check|validate|verify|summarize|probe|replay)",
    re.IGNORECASE,
)
LADON_SCAN_IGNORED_DIRS = {
    ".git",
    ".lake",
    "__pycache__",
    "temp",
    "logs",
    "vendor",
    "opacus",
    "dpdl",
    "jax_privacy",
    "src",
}


@dataclass
class LadonMetadata:
    tool_name: str
    tool_version: str
    report_version: str
    generated_at_utc: str
    repo_root: str
    analysis_root: str
    analysis_root_module: str
    analysis_closure_files: list[str]
    analysis_closure_modules: list[str]
    docs: list[str]
    build_mode: str
    build_command: list[str] | None
    warning_build_mode: str
    warning_build_command: list[str] | None
    extraction_build_verified: bool
    export_surface_verification: str
    export_surface_command: list[str] | None
    export_surface_checked_declarations: int
    export_surface_missing_declarations: int
    extraction_backend: str
    extraction_provenance: str
    extraction_policy: str
    extraction_is_degraded: bool
    extraction_coverage: dict[str, int]
    git_head_sha: str | None
    git_is_dirty: bool | None
    git_status_tracked_count: int | None
    git_status_untracked_count: int | None
    repo_inventory_root: str
    repo_inventory_files: list[str]
    repo_inventory_modules: list[str]
    reachability_root_policy: str
    reachability_policy_strength: str
    reachability_requested_root_modules: list[str]
    reachability_requested_root_prefixes: list[str]
    reachability_resolved_roots: list[str]
    reachability_exclusion_policy: str
    reachability_requested_excluded_modules: list[str]
    reachability_requested_excluded_prefixes: list[str]
    reachability_resolved_exclusions: list[str]


@dataclass
class DeclarationMetric:
    name: str
    full_name: str
    kind: str
    module: str
    path: str
    line: int
    line_span: int
    name_length: int
    extraction_backend: str
    extraction_provenance: str
    position_source: str
    position_is_precise: bool
    body_root_kind: str | None = None
    body_tree_node_count: int | None = None
    body_tree_max_depth: int | None = None
    body_tree_branching_node_count: int | None = None
    body_tree_leaf_count: int | None = None
    body_tree_atom_count: int | None = None
    body_tree_ident_count: int | None = None
    body_uses_by: bool | None = None
    body_uses_calc: bool | None = None
    body_uses_have: bool | None = None
    body_uses_let: bool | None = None
    body_uses_match: bool | None = None
    parser_decision_node_count: int | None = None
    parser_decision_complexity: int | None = None
    parser_decision_nesting_complexity: int | None = None
    parser_decision_rank: str | None = None
    source_slice_line_count: int | None = None
    fragility_simp_like_count: int = 0
    fragility_broad_simp_sites: int = 0
    fragility_rw_count: int = 0
    fragility_by_cases_count: int = 0
    fragility_calc_step_count: int = 0
    fragility_have_count: int = 0
    fragility_score: int = 0
    fragility_signal_family_count: int = 0
    fragility_calibrated_score: int = 0
    fragility_calibrated_band: str = "none"
    reference_candidates: list[str] = field(default_factory=list)
    resolved_reference_count: int = 0
    unresolved_reference_candidate_count: int = 0
    reference_graph_in_degree: int = 0
    reference_graph_out_degree: int = 0


@dataclass
class ExtractionCoverage:
    module_count: int
    declaration_count: int
    missing_positions: int
    omitted_declarations: int


@dataclass
class ExtractionResult:
    backend: str
    provenance: str
    policy: str
    is_degraded: bool
    coverage: ExtractionCoverage
    modules: dict[str, audit.ModuleInfo]
    declaration_metrics: list[DeclarationMetric]
    analysis_root_file: str
    analysis_root_module: str
    analysis_closure_files: list[str]
    analysis_closure_modules: list[str]


@dataclass
class ParsedModuleExtraction:
    module_name: str
    module_info: audit.ModuleInfo
    declaration_metrics: list[DeclarationMetric]
    missing_positions: int
    omitted_declarations: int


@dataclass
class InventorySelection:
    root: str
    files: list[str]
    modules: dict[str, audit.ModuleInfo]


@dataclass
class LadonFinding:
    id: str
    category: str
    severity: str
    confidence: str
    title: str
    summary: str
    files: list[str]
    modules: list[str]
    declarations: list[str]
    scope: str
    evidence: list[str]
    remediation: str


@dataclass
class ReachabilityAnalysis:
    findings: list[LadonFinding]
    module_deadness: dict[str, dict[str, float]]
    deadness_summary: dict[str, Any]


@dataclass
class OwnerHealthAssessment:
    by_module: dict[str, dict[str, Any]]
    findings: list[LadonFinding]
    summary: dict[str, Any]


DECISION_KIND_TOKENS: dict[str, int] = {
    "if": 1,
    "ite": 1,
    "dite": 1,
    "unless": 1,
    "guard": 1,
    "while": 1,
    "for": 1,
    "doif": 1,
}

CONCENTRATION_LINE_THRESHOLD = 12
CONCENTRATION_IMPORT_THRESHOLD = 2
CONCENTRATION_DECL_THRESHOLD = 4
CONCENTRATION_DEF_LIKE_THRESHOLD = 3
CONCENTRATION_DENSITY_THRESHOLD = 18.0
CONCENTRATION_FAN_OUT_THRESHOLD = 6
CONCENTRATION_LARGE_LINE_THRESHOLD = 400
CONCENTRATION_LARGE_DECL_THRESHOLD = 60
CONCENTRATION_DENSE_SMALL_DECL_THRESHOLD = 10
CONCENTRATION_THEOREM_LIKE_RATIO_CEILING = 0.35
CONCENTRATION_SCORE_THRESHOLD = 5
NEAR_DUPLICATE_STRUCTURE_MIN_FIELDS = 6
NEAR_DUPLICATE_STRUCTURE_MIN_SIMILARITY = 0.8
OWNER_ROLE_MIX_MIN_LINE_COUNT = 500
OWNER_ROLE_MIX_MIN_DECLARATIONS = 20
OWNER_ROLE_MIX_MIN_ROLE_FAMILIES = 3
OWNER_ROLE_MIX_MIN_ROLE_HITS = 8
REPEATED_SEMANTIC_EXPR_THRESHOLD = 5
HEALTHY_OWNER_MIN_FAN_IN = 3
HEALTHY_OWNER_MIN_DECLARATIONS = 2
HEALTHY_OWNER_MAX_IMPORTS = 2
HEALTHY_OWNER_MAX_FAN_OUT = 2
HEALTHY_OWNER_MAX_LINE_COUNT = 220
HEALTHY_OWNER_MAX_DECLARATIONS = 16
HEALTHY_OWNER_MAX_DECL_KIND_COUNT = 2
UMBRELLA_OWNER_MIN_FAN_IN = 3
UMBRELLA_OWNER_MIN_IMPORTS = 3
UMBRELLA_OWNER_MIN_FAN_OUT = 3
UMBRELLA_OWNER_MIN_DECLARATIONS = 8
UMBRELLA_OWNER_MIN_DECL_KIND_COUNT = 4
GENERIC_OWNER_TOKENS = {
    "core",
    "bridge",
    "runtime",
    "interface",
    "semantics",
    "gaussian",
}
FAMILY_RESIDUE_IGNORED_TOKENS = {
    "basic",
    "capped",
    "coeff",
    "coeffs",
    "col",
    "cols",
    "comp",
    "density",
    "norm",
    "output",
    "row",
    "rows",
    "std",
    "trace",
    "value",
}
TOKEN_SPLIT_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z]|[0-9]|$)|[A-Z]?[a-z]+|[0-9]+")
FAMILY_RESIDUE_MIN_DECLARATIONS = 8
FAMILY_RESIDUE_MIN_FOREIGN_DECLS = 5
FAMILY_RESIDUE_MIN_RATIO = 0.30
FAMILY_RESIDUE_MIN_FAN_IN = 4
DECLARATION_LEVEL_DEADNESS_MAX_PER_MODULE = 3
DEAD_COMPONENT_PRIORITY_PROMOTION_SCORE = 5
DEAD_COMPONENT_SMALL_SIZE = 3
DEAD_COMPONENT_MEDIUM_SIZE = 8


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ladon: Lean-native code-quality analyzer")
    parser.add_argument("--repo-root", default=".", help="Repository root to analyze")
    parser.add_argument(
        "--root",
        help="Analysis DAG root. Accepts a repo-relative Lean file path or module name. If omitted, ladon requires a uniquely inferable top-level root.",
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
        help="Build command to run for lint/build warning aggregation. Defaults to `lake build`.",
    )
    parser.add_argument("--skip-build", action="store_true", help="Skip build warning aggregation")
    parser.add_argument("--output-json", help="Path to write machine-readable report JSON")
    parser.add_argument("--output-text", help="Path to write human-readable summary")
    parser.add_argument("--generated-at-utc", help="Override report timestamp for deterministic tests")
    parser.add_argument(
        "--diff-base",
        help="Optional git ref/commit for packet-review mode. When set, Ladon reports changed files and changed/new root declarations since this base.",
    )
    parser.add_argument(
        "--packet-dir",
        help=(
            "Optional extracted review-packet directory. When set, Ladon reads "
            "data/source-map.json and runtime JSON claim boundaries to audit "
            "packet theorem-target wiring."
        ),
    )
    parser.add_argument(
        "--lean-parser-helper",
        default=str(DEFAULT_LEAN_PARSER_HELPER),
        help="Path to the Lean parser-helper script run via `lake env lean --run`.",
    )
    parser.add_argument(
        "--verify-export-surface",
        action="store_true",
        help="Import the analysis root and #check root declarations reported by source extraction.",
    )
    parser.add_argument(
        "--certificate-artifact",
        action="append",
        default=[],
        help="Runtime certificate JSON artifact to lint against a known route contract. Repeatable.",
    )
    parser.add_argument(
        "--certificate-artifact-route",
        default="auto",
        choices=["auto", "envelope-is-selected-grid"],
        help="Route contract to use for --certificate-artifact linting.",
    )
    parser.add_argument(
        "--certificate-artifact-rmse-rtol",
        type=float,
        default=1e-6,
        help="Relative tolerance for candidate RMSE consistency checks in certificate artifacts.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=max(1, min(8, os.cpu_count() or 1)),
        help="Maximum parallel parser-helper worker processes. Defaults to a bounded CPU count.",
    )
    parser.add_argument(
        "--reachability-root-policy",
        choices=["explicit", "documented", "fanin-zero", "combined-heuristic", "repo-default"],
        default="repo-default",
        help="Root-selection policy for reachability analysis.",
    )
    parser.add_argument(
        "--reach-root-module",
        action="append",
        default=[],
        help="Module root for reachability analysis. Repeatable. Used directly by the explicit root policy.",
    )
    parser.add_argument(
        "--reach-root-prefix",
        action="append",
        default=[],
        help="Module prefix root for reachability analysis. Repeatable. Used by the explicit root policy.",
    )
    parser.add_argument(
        "--reachability-exclusion-policy",
        choices=["none", "generated", "repo-default"],
        default="repo-default",
        help="Exclusion-policy profile for reachability analysis.",
    )
    parser.add_argument(
        "--exclude-module",
        action="append",
        default=[],
        help="Module to exclude from reachability findings. Repeatable.",
    )
    parser.add_argument(
        "--exclude-module-prefix",
        action="append",
        default=[],
        help="Module prefix to exclude from reachability findings. Repeatable.",
    )
    return parser.parse_args(argv)


def repo_relative_path(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def module_path_candidates(root: Path, raw_root: str) -> list[Path]:
    candidates: list[Path] = []
    module_candidate = root / Path(*raw_root.split(".")).with_suffix(".lean")
    if module_candidate not in candidates:
        candidates.append(module_candidate)
    repo_style_candidate = root / Path(raw_root).with_suffix(".lean")
    if repo_style_candidate not in candidates:
        candidates.append(repo_style_candidate)
    return candidates


def infer_default_analysis_root_file(root: Path) -> Path:
    top_level_files = sorted(
        path for path in root.glob("*.lean") if path.is_file()
    )
    if len(top_level_files) == 1:
        return top_level_files[0].resolve()
    if not top_level_files:
        raise RuntimeError(
            f"Analysis-root resolution failed: no top-level Lean root could be inferred under {root}; pass --root explicitly."
        )
    raise RuntimeError(
        f"Analysis-root resolution failed: multiple top-level Lean roots exist under {root}; pass --root explicitly."
    )


def resolve_analysis_root_file(root: Path, raw_root: str | None) -> Path:
    if not raw_root:
        return infer_default_analysis_root_file(root)
    candidates: list[Path] = []
    raw_path = Path(raw_root)
    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        direct = root / raw_path
        candidates.append(direct)
        if raw_path.suffix != ".lean":
            direct_lean = direct.with_suffix(".lean")
            if direct_lean not in candidates:
                candidates.append(direct_lean)
        for candidate in module_path_candidates(root, raw_root):
            if candidate not in candidates:
                candidates.append(candidate)
    existing = [candidate.resolve() for candidate in candidates if candidate.exists() and candidate.is_file()]
    if not existing:
        raise RuntimeError(
            f"Analysis-root resolution failed: could not resolve {raw_root!r} to a Lean file under {root}."
        )
    selected = existing[0]
    try:
        selected.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(
            f"Analysis-root resolution failed: {selected} is outside the configured repository root {root}."
        ) from exc
    if selected.suffix != ".lean":
        raise RuntimeError(f"Analysis-root resolution failed: {selected} is not a Lean source file.")
    return selected


def module_file_for_import(root: Path, module_name: str) -> Path | None:
    candidate = root / Path(*module_name.split(".")).with_suffix(".lean")
    return candidate if candidate.exists() and candidate.is_file() else None


def default_doc_files(root: Path) -> list[str]:
    return [doc for doc in DEFAULT_DOC_CANDIDATES if (root / doc).exists()]


def inventory_root_from_analysis_root(analysis_root_file: str, analysis_root_module: str) -> str:
    file_parts = Path(analysis_root_file).parts
    if len(file_parts) > 1:
        return file_parts[0]
    return analysis_root_module.split(".")[0]


def discover_repo_inventory(root: Path, analysis_root_file: str, analysis_root_module: str) -> InventorySelection:
    inventory_root = inventory_root_from_analysis_root(analysis_root_file, analysis_root_module)
    files: list[Path] = []
    top_file = root / f"{inventory_root}.lean"
    if top_file.exists() and top_file.is_file():
        files.append(top_file)
    top_dir = root / inventory_root
    if top_dir.exists() and top_dir.is_dir():
        files.extend(sorted(top_dir.rglob("*.lean")))
    seen: set[Path] = set()
    unique_files: list[Path] = []
    for file_path in files:
        if file_path not in seen:
            seen.add(file_path)
            unique_files.append(file_path)
    modules = {audit.module_name(root, file_path): audit.parse_module(root, file_path) for file_path in unique_files}
    return InventorySelection(
        root=inventory_root,
        files=[repo_relative_path(root, file_path) for file_path in unique_files],
        modules=dict(sorted(modules.items())),
    )


def assign_fan_counts(modules: dict[str, audit.ModuleInfo]) -> dict[str, set[str]]:
    reverse_imports: dict[str, set[str]] = {}
    for info in modules.values():
        info.fan_out = len(info.imports)
        for imported in info.imports:
            reverse_imports.setdefault(imported, set()).add(info.module)
    for info in modules.values():
        info.fan_in = len(reverse_imports.get(info.module, set()))
    return reverse_imports


def expand_module_prefixes(modules: dict[str, audit.ModuleInfo], prefixes: Sequence[str]) -> list[str]:
    expanded: set[str] = set()
    for prefix in prefixes:
        for module in modules:
            if module == prefix or module.startswith(f"{prefix}."):
                expanded.add(module)
    return sorted(expanded)


def normalize_decl_kind(kind: str) -> str:
    normalized = kind.strip().lower().replace(" ", "_")
    mapping = {
        "definition": "def",
        "theorem": "theorem",
        "lemma": "lemma",
        "abbreviation": "abbrev",
        "abbrev": "abbrev",
        "instance": "instance",
        "structure": "structure",
        "class": "class",
        "inductive": "inductive",
    }
    return mapping.get(normalized, normalized)


def ensure_lean_project(root: Path) -> None:
    if (root / "lean-toolchain").exists() and ((root / "lakefile.lean").exists() or (root / "lakefile.toml").exists()):
        return
    raise RuntimeError(
        f"Lean-native extraction failed: {root} is not a Lean project root; expected lean-toolchain and lakefile."
    )


def ensure_lean_build(root: Path) -> None:
    command = ["lake", "build"]
    proc = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Lean-native extraction failed: could not build Lean project at {root}: "
            f"{(proc.stderr or proc.stdout).strip()}"
        )


def load_build_lines_for_ladon(root: Path, args: argparse.Namespace) -> tuple[str, list[str], list[str]]:
    if args.skip_build:
        return "skipped", [], []
    if args.build_log:
        build_path = (root / args.build_log).resolve() if not Path(args.build_log).is_absolute() else Path(args.build_log)
        return "build_log", [str(build_path)], build_path.read_text(encoding="utf-8").splitlines()
    command = args.build_command or ["lake", "build"]
    proc = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    lines = (proc.stdout + "\n" + proc.stderr).splitlines()
    return "command", command, lines


def extract_module_with_parser_helper(root: Path, helper_path: Path, file_path: Path) -> ParsedModuleExtraction:
    rel_path = str(file_path.relative_to(root))
    module_name = audit.module_name(root, file_path)
    proc = subprocess.run(
        [
            "lake",
            "env",
            "lean",
            "--run",
            str(helper_path),
            "--",
            rel_path,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Lean-native extraction failed: parser-helper failed for {rel_path}: "
            f"{(proc.stderr or proc.stdout).strip()}"
        )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Lean-native extraction failed: parser-helper emitted invalid JSON for {rel_path} ({exc})."
        ) from exc

    module_decls: list[audit.Declaration] = []
    declaration_metrics: list[DeclarationMetric] = []
    missing_positions = 0
    omitted_declarations = 0

    for command in payload["commands"]:
        if not command.get("isDeclarationLike"):
            continue
        decl_name = command.get("declarationName")
        decl_kind = command.get("declarationKind")
        decl_range = command.get("range")
        if not decl_name or not decl_kind:
            omitted_declarations += 1
            continue
        if decl_range is None:
            missing_positions += 1
            continue
        start = decl_range["start"]
        finish = decl_range["finish"]
        kind = normalize_decl_kind(decl_kind)
        line = start["line"]
        line_span = max(1, finish["line"] - start["line"] + 1)
        body_metrics = compute_body_tree_metrics(command.get("bodyTree"))
        module_decls.append(audit.Declaration(kind=kind, name=decl_name))
        declaration_metrics.append(
            DeclarationMetric(
                name=decl_name,
                full_name=command.get("declarationFullName") or decl_name,
                kind=kind,
                module=module_name,
                path=rel_path,
                line=line,
                line_span=line_span,
                name_length=len(decl_name),
                extraction_backend="lean-parser-helper",
                extraction_provenance="lean-native-parser",
                position_source="parser-range",
                position_is_precise=True,
                reference_candidates=list(command.get("referenceCandidates") or []),
                **body_metrics,
            )
        )

    module_info = audit.ModuleInfo(
        module=module_name,
        path=rel_path,
        imports=[entry["module"] for entry in payload["header"]["imports"]],
        declarations=module_decls,
    )
    return ParsedModuleExtraction(
        module_name=module_name,
        module_info=module_info,
        declaration_metrics=declaration_metrics,
        missing_positions=missing_positions,
        omitted_declarations=omitted_declarations,
    )


def walk_body_tree(node: dict[str, Any], depth: int = 1) -> dict[str, Any]:
    children = node.get("children", [])
    child_results = [walk_body_tree(child, depth + 1) for child in children]
    lowered_kind = str(node.get("kind", "")).lower()
    node_count = 1 + sum(child["node_count"] for child in child_results)
    max_depth = max([depth, *(child["max_depth"] for child in child_results)])
    leaf_count = 1 if not children else sum(child["leaf_count"] for child in child_results)
    atom_count = (1 if node.get("category") == "atom" else 0) + sum(child["atom_count"] for child in child_results)
    ident_count = (1 if node.get("category") == "ident" else 0) + sum(child["ident_count"] for child in child_results)
    branching_node_count = (1 if len(children) > 1 else 0) + sum(
        child["branching_node_count"] for child in child_results
    )
    return {
        "node_count": node_count,
        "max_depth": max_depth,
        "leaf_count": leaf_count,
        "atom_count": atom_count,
        "ident_count": ident_count,
        "branching_node_count": branching_node_count,
        "uses_by": ".bytactic" in lowered_kind,
        "uses_calc": ".calc" in lowered_kind,
        "uses_have": ".have" in lowered_kind,
        "uses_let": ".let" in lowered_kind,
        "uses_match": ".match" in lowered_kind,
        "children": child_results,
    }


def parser_decision_rank(score: int) -> str:
    if score <= 5:
        return "A"
    if score <= 10:
        return "B"
    if score <= 20:
        return "C"
    if score <= 30:
        return "D"
    if score <= 40:
        return "E"
    return "F"


def parser_decision_delta(node: dict[str, Any]) -> int:
    kind = str(node.get("kind", "")).lower()
    category = str(node.get("category", "")).lower()
    children = node.get("children", [])

    if kind.endswith(".match") or kind == "match":
        branch_count = count_descendant_kinds(node, ".matchAlt")
        return max(branch_count - 1, 0)

    if category == "atom":
        normalized = kind.strip("«»")
        if normalized in DECISION_KIND_TOKENS:
            return DECISION_KIND_TOKENS[normalized]

    if kind.endswith(".andthen") or kind.endswith(".orElse".lower()):
        return 1

    if kind.endswith(".try"):
        handler_count = sum(1 for child in children if "catch" in str(child.get("kind", "")).lower())
        return max(handler_count, 1)

    return 0


def count_descendant_kinds(node: dict[str, Any], suffix: str) -> int:
    total = 1 if str(node.get("kind", "")).endswith(suffix) else 0
    for child in node.get("children", []):
        total += count_descendant_kinds(child, suffix)
    return total


def compute_parser_decision_metrics(body_tree: dict[str, Any] | None) -> dict[str, Any]:
    if not body_tree:
        return {
            "parser_decision_node_count": None,
            "parser_decision_complexity": None,
            "parser_decision_nesting_complexity": None,
            "parser_decision_rank": None,
        }

    decision_count = 0
    raw_delta = 0
    nesting_total = 1  # baseline path, Radon-style

    def visit(node: dict[str, Any], decision_depth: int) -> None:
        nonlocal decision_count, raw_delta, nesting_total
        delta = parser_decision_delta(node)
        next_depth = decision_depth
        if delta > 0:
            decision_count += 1
            raw_delta += delta
            nesting_total += delta * (1 + decision_depth)
            next_depth = decision_depth + 1
        for child in node.get("children", []):
            visit(child, next_depth)

    visit(body_tree, 0)
    complexity = 1 + raw_delta
    return {
        "parser_decision_node_count": decision_count,
        "parser_decision_complexity": complexity,
        "parser_decision_nesting_complexity": nesting_total,
        "parser_decision_rank": parser_decision_rank(complexity),
    }


def compute_body_tree_metrics(body_tree: dict[str, Any] | None) -> dict[str, Any]:
    if not body_tree:
        return {
            "body_root_kind": None,
            "body_tree_node_count": None,
            "body_tree_max_depth": None,
            "body_tree_branching_node_count": None,
            "body_tree_leaf_count": None,
            "body_tree_atom_count": None,
            "body_tree_ident_count": None,
            "body_uses_by": None,
            "body_uses_calc": None,
            "body_uses_have": None,
            "body_uses_let": None,
            "body_uses_match": None,
            "parser_decision_node_count": None,
            "parser_decision_complexity": None,
            "parser_decision_nesting_complexity": None,
            "parser_decision_rank": None,
        }
    walked = walk_body_tree(body_tree)
    descendants = [walked, *flatten_body_tree_results(walked)]
    metrics = {
        "body_root_kind": body_tree.get("kind"),
        "body_tree_node_count": walked["node_count"],
        "body_tree_max_depth": walked["max_depth"],
        "body_tree_branching_node_count": walked["branching_node_count"],
        "body_tree_leaf_count": walked["leaf_count"],
        "body_tree_atom_count": walked["atom_count"],
        "body_tree_ident_count": walked["ident_count"],
        "body_uses_by": any(node["uses_by"] for node in descendants),
        "body_uses_calc": any(node["uses_calc"] for node in descendants),
        "body_uses_have": any(node["uses_have"] for node in descendants),
        "body_uses_let": any(node["uses_let"] for node in descendants),
        "body_uses_match": any(node["uses_match"] for node in descendants),
    }
    metrics.update(compute_parser_decision_metrics(body_tree))
    return metrics


def declaration_source_slices(root: Path, declaration_metrics: list[DeclarationMetric]) -> dict[str, str]:
    by_path: dict[str, list[DeclarationMetric]] = defaultdict(list)
    for metric in declaration_metrics:
        by_path[metric.path].append(metric)
    out: dict[str, str] = {}
    for rel_path, metrics in by_path.items():
        lines = (root / rel_path).read_text(encoding="utf-8").splitlines()
        for metric in metrics:
            start = max(0, metric.line - 1)
            finish = min(len(lines), start + metric.line_span)
            out[metric.full_name] = "\n".join(lines[start:finish]) + ("\n" if finish > start else "")
    return out


def compute_fragility_metrics(source_slice: str) -> dict[str, int]:
    simp_like_count = len(SIMP_LIKE_RE.findall(source_slice))
    broad_simp_sites = len(BROAD_SIMP_RE.findall(source_slice))
    rw_count = len(RW_RE.findall(source_slice))
    by_cases_count = len(BY_CASES_RE.findall(source_slice))
    have_count = len(HAVE_RE.findall(source_slice))
    calc_block_count = len(CALC_RE.findall(source_slice))
    calc_step_count = 0
    if calc_block_count:
        calc_step_count = max(0, len(CALC_STEP_RE.findall(source_slice)) - 1)
    score = 0
    if simp_like_count >= 3:
        score += 1
    score += broad_simp_sites * 3
    score += max(0, rw_count - 2)
    score += by_cases_count * 2
    score += max(0, calc_step_count - 2)
    score += max(0, have_count - 3)
    signal_family_count = sum(
        1
        for active in [
            broad_simp_sites > 0,
            simp_like_count >= 4,
            rw_count >= 4,
            by_cases_count >= 2,
            calc_step_count >= 6,
            have_count >= 5,
        ]
        if active
    )
    calibrated_score = signal_family_count * 2
    if score >= 8:
        calibrated_score += 1
    if rw_count >= 4 and have_count >= 4:
        calibrated_score += 1
    if calc_step_count >= 6 and have_count >= 4:
        calibrated_score += 1
    if broad_simp_sites > 0 and (rw_count >= 2 or have_count >= 3 or calc_step_count >= 3):
        calibrated_score += 1
    if len([line for line in source_slice.splitlines() if line.strip()]) >= 20 and signal_family_count >= 2:
        calibrated_score += 1
    if calibrated_score >= 7:
        calibrated_band = "high"
    elif calibrated_score >= 5:
        calibrated_band = "medium"
    elif calibrated_score >= 3:
        calibrated_band = "low"
    else:
        calibrated_band = "none"
    return {
        "source_slice_line_count": len([line for line in source_slice.splitlines() if line.strip()]),
        "fragility_simp_like_count": simp_like_count,
        "fragility_broad_simp_sites": broad_simp_sites,
        "fragility_rw_count": rw_count,
        "fragility_by_cases_count": by_cases_count,
        "fragility_calc_step_count": calc_step_count,
        "fragility_have_count": have_count,
        "fragility_score": score,
        "fragility_signal_family_count": signal_family_count,
        "fragility_calibrated_score": calibrated_score,
        "fragility_calibrated_band": calibrated_band,
    }


def flatten_body_tree_results(node: dict[str, Any]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for child in node["children"]:
        flattened.append(child)
        flattened.extend(flatten_body_tree_results(child))
    return flattened


def extract_with_parser_helper(root: Path, args: argparse.Namespace) -> ExtractionResult:
    ensure_lean_project(root)
    ensure_lean_build(root)
    helper_path = Path(args.lean_parser_helper).resolve()
    if not helper_path.exists():
        raise RuntimeError(
            f"Lean-native extraction failed: parser-helper script not found at {helper_path}."
        )

    analysis_root_file = resolve_analysis_root_file(root, args.root)
    modules: dict[str, audit.ModuleInfo] = {}
    declaration_metrics: list[DeclarationMetric] = []
    missing_positions = 0
    omitted_declarations = 0
    extracted_by_file: dict[Path, ParsedModuleExtraction] = {}
    max_workers = max(1, args.max_workers)
    queue: list[Path] = [analysis_root_file]
    enqueued: set[Path] = {analysis_root_file}
    analysis_order: list[Path] = []

    while queue:
        batch = queue[:max_workers]
        del queue[:max_workers]
        if len(batch) == 1 or max_workers == 1:
            batch_results = [extract_module_with_parser_helper(root, helper_path, batch[0])]
        else:
            with ThreadPoolExecutor(max_workers=min(max_workers, len(batch))) as executor:
                future_to_path = {
                    executor.submit(extract_module_with_parser_helper, root, helper_path, file_path): file_path
                    for file_path in batch
                }
                completed: dict[Path, ParsedModuleExtraction] = {}
                for future in as_completed(future_to_path):
                    file_path = future_to_path[future]
                    completed[file_path] = future.result()
                batch_results = [completed[file_path] for file_path in batch]

        for file_path, module_extraction in zip(batch, batch_results, strict=True):
            extracted_by_file[file_path] = module_extraction
            analysis_order.append(file_path)
            child_paths = sorted(
                {
                    child_path
                    for imported in module_extraction.module_info.imports
                    for child_path in [module_file_for_import(root, imported)]
                    if child_path is not None
                }
            )
            for child_path in child_paths:
                if child_path not in enqueued:
                    enqueued.add(child_path)
                    queue.append(child_path)

    for file_path in analysis_order:
        module_extraction = extracted_by_file[file_path]
        modules[module_extraction.module_name] = module_extraction.module_info
        declaration_metrics.extend(module_extraction.declaration_metrics)
        missing_positions += module_extraction.missing_positions
        omitted_declarations += module_extraction.omitted_declarations

    analysis_closure_files = [repo_relative_path(root, file_path) for file_path in analysis_order]
    analysis_closure_modules = [extracted_by_file[file_path].module_name for file_path in analysis_order]
    source_slices = declaration_source_slices(root, declaration_metrics)
    for metric in declaration_metrics:
        for key, value in compute_fragility_metrics(source_slices.get(metric.full_name, "")).items():
            setattr(metric, key, value)

    return ExtractionResult(
        backend="lean-parser-helper",
        provenance="lean-native-parser",
        policy="strict",
        is_degraded=False,
        coverage=ExtractionCoverage(
            module_count=len(modules),
            declaration_count=len(declaration_metrics),
            missing_positions=missing_positions,
            omitted_declarations=omitted_declarations,
        ),
        modules=modules,
        declaration_metrics=declaration_metrics,
        analysis_root_file=repo_relative_path(root, analysis_root_file),
        analysis_root_module=audit.module_name(root, analysis_root_file),
        analysis_closure_files=analysis_closure_files,
        analysis_closure_modules=analysis_closure_modules,
    )


def module_metrics(root: Path, modules: dict[str, audit.ModuleInfo], build_warnings: dict[str, Counter]) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {}
    for info in modules.values():
        file_path = root / info.path
        text = file_path.read_text(encoding="utf-8")
        line_count = text.count("\n") + (0 if text.endswith("\n") and text else 1)
        warning_total = int(build_warnings.get(info.path, Counter()).get("total", 0))
        kind_counts = Counter(decl.kind for decl in info.declarations)
        theorem_like = int(kind_counts.get("theorem", 0) + kind_counts.get("lemma", 0))
        def_like = int(sum(kind_counts.get(kind, 0) for kind in ["def", "abbrev", "instance"]))
        metrics[info.module] = {
            "path": info.path,
            "fan_in": info.fan_in,
            "fan_out": info.fan_out,
            "imports": sorted(info.imports),
            "import_count": len(info.imports),
            "declaration_count": len(info.declarations),
            "declaration_kinds": dict(sorted(kind_counts.items())),
            "theorem_like_count": theorem_like,
            "def_like_count": def_like,
            "line_count": line_count,
            "warning_count": warning_total,
            "warning_density_per_100_lines": round((warning_total / max(line_count, 1)) * 100, 2),
        }
    return dict(sorted(metrics.items()))


def select_reachability_roots(
    args: argparse.Namespace,
    modules: dict[str, audit.ModuleInfo],
    doc_module_mentions: dict[str, set[str]],
) -> list[str]:
    by_basename = {Path(info.path).stem: info.module for info in modules.values()}
    doc_roots = sorted(
        {
            by_basename[mention]
            for mentions in doc_module_mentions.values()
            for mention in mentions
            if mention in by_basename
        }
    )
    explicit_roots = sorted([m for m in args.reach_root_module if m in modules])
    explicit_prefix_roots = expand_module_prefixes(modules, args.reach_root_prefix)
    fanin_zero_roots = sorted(info.module for info in modules.values() if info.fan_in == 0)
    policy = args.reachability_root_policy
    if policy == "explicit":
        return sorted(set(explicit_roots) | set(explicit_prefix_roots))
    if policy == "documented":
        return doc_roots
    if policy == "fanin-zero":
        return fanin_zero_roots
    if policy in {"combined-heuristic", "repo-default"}:
        return sorted(set(doc_roots) | set(fanin_zero_roots))
    return []


def reachability_policy_strength(args: argparse.Namespace) -> str:
    return "strong" if args.reachability_root_policy in STRONG_ROOT_POLICIES else "weak"


def select_reachability_exclusions(
    args: argparse.Namespace,
    modules: dict[str, audit.ModuleInfo],
) -> set[str]:
    exclusions = set(args.exclude_module or [])
    exclusions.update(expand_module_prefixes(modules, args.exclude_module_prefix))
    if args.reachability_exclusion_policy in {"generated", "repo-default"}:
        for module in modules:
            if module.endswith("Generated") or any(marker in module for marker in GENERATED_MODULE_MARKERS):
                exclusions.add(module)
    return exclusions


def declaration_namespace(full_name: str) -> str:
    parts = full_name.split(".")
    return ".".join(parts[:-1]) if len(parts) > 1 else ""


def build_declaration_reference_graph(
    declaration_metrics: list[DeclarationMetric],
) -> dict[str, Any]:
    by_full_name = {metric.full_name: metric for metric in declaration_metrics}
    by_name: dict[str, list[DeclarationMetric]] = defaultdict(list)
    by_namespace_name: dict[tuple[str, str], list[DeclarationMetric]] = defaultdict(list)
    for metric in declaration_metrics:
        by_name[metric.name].append(metric)
        by_namespace_name[(declaration_namespace(metric.full_name), metric.name)].append(metric)

    edges: dict[str, set[str]] = {metric.full_name: set() for metric in declaration_metrics}
    unresolved_counts: Counter[str] = Counter()
    total_candidates = 0
    resolved_candidates = 0

    for metric in declaration_metrics:
        namespace = declaration_namespace(metric.full_name)
        for candidate in metric.reference_candidates:
            total_candidates += 1
            target: DeclarationMetric | None = None
            if candidate in by_full_name:
                target = by_full_name[candidate]
            elif "." not in candidate:
                namespace_matches = by_namespace_name.get((namespace, candidate), [])
                if len(namespace_matches) == 1:
                    target = namespace_matches[0]
                else:
                    short_matches = by_name.get(candidate, [])
                    if len(short_matches) == 1:
                        target = short_matches[0]
            if target is None:
                unresolved_counts[metric.full_name] += 1
                continue
            if target.full_name == metric.full_name:
                continue
            if target.full_name in edges[metric.full_name]:
                continue
            edges[metric.full_name].add(target.full_name)
            resolved_candidates += 1

    reverse_edges: dict[str, set[str]] = {metric.full_name: set() for metric in declaration_metrics}
    for source, targets in edges.items():
        for target in targets:
            reverse_edges[target].add(source)

    for metric in declaration_metrics:
        metric.resolved_reference_count = len(edges[metric.full_name])
        metric.unresolved_reference_candidate_count = unresolved_counts.get(metric.full_name, 0)
        metric.reference_graph_out_degree = len(edges[metric.full_name])
        metric.reference_graph_in_degree = len(reverse_edges[metric.full_name])

    return {
        "scope": "analysis_closure",
        "provenance": "lean-parser-helper-reference-candidates",
        "candidate_count": total_candidates,
        "resolved_edge_count": sum(len(targets) for targets in edges.values()),
        "resolved_candidate_count": resolved_candidates,
        "unresolved_candidate_count": sum(unresolved_counts.values()),
        "edges": {source: sorted(targets) for source, targets in edges.items()},
        "reverse_edges": {target: sorted(sources) for target, sources in reverse_edges.items()},
    }


def reachable_modules(modules: dict[str, audit.ModuleInfo], roots: list[str]) -> set[str]:
    seen: set[str] = set()
    stack = list(roots)
    while stack:
        module = stack.pop()
        if module in seen or module not in modules:
            continue
        seen.add(module)
        for imported in modules[module].imports:
            if imported in modules:
                stack.append(imported)
    return seen


def add_reachability_findings(
    *,
    modules: dict[str, audit.ModuleInfo],
    declaration_metrics: list[DeclarationMetric],
    declaration_graph: dict[str, Any],
    doc_module_mentions: dict[str, set[str]],
    args: argparse.Namespace,
    base_findings: list[LadonFinding],
) -> ReachabilityAnalysis:
    findings = list(base_findings)
    next_id = len(findings) + 1
    exclusions = select_reachability_exclusions(args, modules)
    roots = select_reachability_roots(args, modules, doc_module_mentions)
    policy_strength = reachability_policy_strength(args)
    reachable = reachable_modules(modules, roots)
    decls_by_module: dict[str, list[DeclarationMetric]] = {}
    for metric in declaration_metrics:
        decls_by_module.setdefault(metric.module, []).append(metric)
    declaration_root_modules = set(roots)
    for module in roots:
        if decls_by_module.get(module):
            continue
        for imported in modules.get(module, audit.ModuleInfo(module=module, path="", imports=[], declarations=[])).imports:
            if imported in reachable and imported in modules:
                declaration_root_modules.add(imported)
    decl_roots = {metric.full_name for metric in declaration_metrics if metric.module in declaration_root_modules}
    reachable_declarations = set(decl_roots)
    edge_map = declaration_graph["edges"]
    queue: deque[str] = deque(sorted(decl_roots))
    while queue:
        current = queue.popleft()
        for target in edge_map.get(current, []):
            if target in reachable_declarations:
                continue
            reachable_declarations.add(target)
            queue.append(target)

    module_deadness: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "dead_module_finding_count": 0.0,
            "warn_dead_module_finding_count": 0.0,
            "dead_declaration_count": 0.0,
            "dead_component_count": 0.0,
            "prioritized_dead_component_count": 0.0,
            "prioritized_dead_declaration_count": 0.0,
            "strong_dead_declaration_count": 0.0,
        }
    )

    def bump_module_deadness(
        module: str,
        *,
        severity: str,
        declaration_count: int = 0,
        component_count: int = 0,
        prioritized_component_count: int = 0,
        prioritized_declaration_count: int = 0,
        strong_decl_count: int = 0,
    ) -> None:
        module_deadness[module]["dead_module_finding_count"] += 1
        if severity == "warn":
            module_deadness[module]["warn_dead_module_finding_count"] += 1
        module_deadness[module]["dead_declaration_count"] += declaration_count
        module_deadness[module]["dead_component_count"] += component_count
        module_deadness[module]["prioritized_dead_component_count"] += prioritized_component_count
        module_deadness[module]["prioritized_dead_declaration_count"] += prioritized_declaration_count
        module_deadness[module]["strong_dead_declaration_count"] += strong_decl_count

    for module in sorted(modules):
        if module in exclusions:
            continue
        if roots and module not in reachable:
            decls = decls_by_module.get(module, [])
            confidence = "deterministic" if policy_strength == "strong" else "heuristic"
            severity = "warn" if policy_strength == "strong" else "review"
            title = (
                f"Declarations unreachable from configured roots: {module}"
                if policy_strength == "strong"
                else f"Declarations unreachable under weak root policy: {module}"
            )
            summary = (
                f"{module} is outside the configured module-import reachability closure, so its declarations are unreachable under the current graph model."
                if policy_strength == "strong"
                else f"{module} is outside the configured module-import reachability closure, but the active root policy is too weak to treat that as a deterministic dead-surface claim."
            )
            findings.append(
                LadonFinding(
                    id=f"L{next_id:04d}",
                    category="unreachable_declaration_surface",
                    severity=severity,
                    confidence=confidence,
                    title=title,
                    summary=summary,
                    files=[modules[module].path],
                    modules=[module],
                    declarations=[decl.name for decl in decls],
                    scope="analysis_closure",
                    evidence=[
                        f"root_policy={args.reachability_root_policy}",
                        f"policy_strength={policy_strength}",
                        f"roots={','.join(roots) if roots else '<none>'}",
                        f"imports={','.join(modules[module].imports) if modules[module].imports else '<none>'}",
                        f"declaration_count={len(decls)}",
                    ],
                    remediation=(
                        "Either add the module to the explicit reachability roots, exclude it intentionally, or confirm that the surface is truly dead."
                        if policy_strength == "strong"
                        else "Calibrate the root/exclusion policy before treating this as dead surface, or review it as an orphaned-surface suspicion."
                    ),
                )
            )
            bump_module_deadness(module, severity=severity, declaration_count=len(decls), component_count=1 if decls else 0)
            next_id += 1

    by_basename = {Path(info.path).stem for info in modules.values()}
    doc_mentions = {mention for mentions in doc_module_mentions.values() for mention in mentions if mention in by_basename}
    for module in sorted(modules):
        if module in exclusions or module in roots:
            continue
        info = modules[module]
        basename = Path(info.path).stem
        if info.fan_in == 0 and basename not in doc_mentions:
            decls = decls_by_module.get(module, [])
            findings.append(
                LadonFinding(
                    id=f"L{next_id:04d}",
                    category="orphaned_declaration_surface",
                    severity="review",
                    confidence="heuristic",
                    title=f"Likely orphaned declaration surface: {module}",
                    summary=f"{module} has no in-scope importers, is not a configured reachability root, and is not documented as a public surface.",
                    files=[info.path],
                    modules=[module],
                    declarations=[decl.name for decl in decls],
                    scope="analysis_closure",
                    evidence=[
                        f"fan_in={info.fan_in}",
                        f"root_modules={','.join(roots) if roots else '<none>'}",
                        f"documented_basename={basename in doc_mentions}",
                    ],
                    remediation="Review whether this module should be rooted, documented, excluded, or removed as dead surface.",
                )
            )
            bump_module_deadness(module, severity="review", declaration_count=len(decls), component_count=1 if decls else 0)
            next_id += 1

    dead_metrics_by_module: dict[str, list[DeclarationMetric]] = defaultdict(list)
    for metric in declaration_metrics:
        if metric.module in exclusions or metric.module in roots or metric.module not in reachable:
            continue
        if metric.full_name in reachable_declarations:
            continue
        dead_metrics_by_module[metric.module].append(metric)

    reverse_edge_map = declaration_graph["reverse_edges"]

    def dead_components(metrics: list[DeclarationMetric]) -> list[list[DeclarationMetric]]:
        by_name = {metric.full_name: metric for metric in metrics}
        remaining = set(by_name)
        components: list[list[DeclarationMetric]] = []
        while remaining:
            start = remaining.pop()
            stack = [start]
            component_names = {start}
            while stack:
                current = stack.pop()
                neighbors = set(edge_map.get(current, [])) | set(reverse_edge_map.get(current, []))
                for neighbor in neighbors:
                    if neighbor not in by_name or neighbor in component_names:
                        continue
                    component_names.add(neighbor)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                    stack.append(neighbor)
            components.append(sorted((by_name[name] for name in component_names), key=lambda item: (item.line, item.full_name)))
        components.sort(key=lambda items: (-len(items), items[0].full_name))
        return components

    aggregated_modules: list[dict[str, Any]] = []
    prioritized_components_summary: list[dict[str, Any]] = []
    suppressed_components_summary: list[dict[str, Any]] = []
    strong_declaration_findings = 0
    for module in sorted(dead_metrics_by_module):
        metrics = sorted(dead_metrics_by_module[module], key=lambda item: (item.line, item.full_name))
        components = dead_components(metrics)
        deterministic_metrics = [metric for metric in metrics if metric.unresolved_reference_candidate_count == 0]
        sample_declarations = [metric.name for metric in metrics[: min(5, len(metrics))]]
        largest_component_size = max((len(component) for component in components), default=0)
        prioritized_components = 0
        prioritized_declarations = 0

        def component_priority(component: list[DeclarationMetric]) -> tuple[int, int, int]:
            unresolved_total = sum(item.unresolved_reference_candidate_count for item in component)
            size = len(component)
            score = 0
            if unresolved_total == 0:
                score += 3
            if size <= DEAD_COMPONENT_SMALL_SIZE:
                score += 3
            elif size <= DEAD_COMPONENT_MEDIUM_SIZE:
                score += 1
            if any(item.reference_graph_in_degree > 0 for item in component):
                score += 1
            if any(item.kind in {"theorem", "lemma"} for item in component):
                score += 1
            return score, unresolved_total, size

        ranked_components: list[tuple[list[DeclarationMetric], int, int, int]] = []
        for component in components:
            score, unresolved_total, size = component_priority(component)
            ranked_components.append((component, score, unresolved_total, size))
        ranked_components.sort(
            key=lambda item: (
                item[1],
                -item[2],
                -item[3],
                item[0][0].full_name,
            ),
            reverse=True,
        )

        for index, (component, score, unresolved_total, size) in enumerate(ranked_components, start=1):
            component_sample = [item.name for item in component[: min(5, len(component))]]
            component_payload = {
                "scope": "analysis_closure",
                "module": module,
                "path": component[0].path,
                "priority_rank": index,
                "priority_score": score,
                "dead_declaration_count": size,
                "unresolved_reference_candidate_count": unresolved_total,
                "deterministic": unresolved_total == 0,
                "sample_declarations": component_sample,
            }
            if unresolved_total == 0 and score >= DEAD_COMPONENT_PRIORITY_PROMOTION_SCORE:
                findings.append(
                    LadonFinding(
                        id=f"L{next_id:04d}",
                        category="orphaned_declaration_surface",
                        severity="review",
                        confidence="deterministic" if unresolved_total == 0 else "heuristic",
                        title=f"Prioritized dead declaration component inside reachable module: {module}",
                        summary=(
                            f"{module} is reachable at the module-import level, but a ranked dead component with {size} declarations is not reached from the configured declaration roots."
                        ),
                        files=[component[0].path],
                        modules=[module],
                        declarations=component_sample,
                        scope="analysis_closure",
                        evidence=[
                            "graph_scope=analysis_closure",
                            f"graph_provenance={declaration_graph['provenance']}",
                            f"component_priority_score={score}",
                            f"component_rank={index}",
                            f"dead_declaration_count={size}",
                            f"unresolved_reference_candidate_count={unresolved_total}",
                            f"sample_declarations={','.join(component_sample)}",
                            f"root_modules={','.join(roots) if roots else '<none>'}",
                        ],
                        remediation="Review whether this dead component should be rooted, referenced from the intended public surface, or removed as residue.",
                    )
                )
                next_id += 1
                prioritized_components += 1
                prioritized_declarations += size
                prioritized_components_summary.append(component_payload)
            else:
                suppressed_components_summary.append(component_payload)

        if prioritized_components > 0:
            bump_module_deadness(
                module,
                severity="review",
                declaration_count=len(metrics),
                component_count=len(components),
                prioritized_component_count=prioritized_components,
                prioritized_declaration_count=prioritized_declarations,
                strong_decl_count=0,
            )

        if (
            policy_strength == "strong"
            and len(metrics) <= DECLARATION_LEVEL_DEADNESS_MAX_PER_MODULE
            and len(deterministic_metrics) == len(metrics)
        ):
            for metric in metrics:
                findings.append(
                    LadonFinding(
                        id=f"L{next_id:04d}",
                        category="dead_declaration_detail",
                        severity="review",
                        confidence="deterministic",
                        title=f"Strong dead declaration candidate: {metric.full_name}",
                        summary=(
                            f"{metric.full_name} is inside the reachable module closure, but no rooted declaration reaches it through the deterministic declaration graph."
                        ),
                        files=[metric.path],
                        modules=[metric.module],
                        declarations=[metric.name],
                        scope="analysis_closure",
                        evidence=[
                            "graph_scope=analysis_closure",
                            f"graph_provenance={declaration_graph['provenance']}",
                            f"reference_graph_in_degree={metric.reference_graph_in_degree}",
                            f"reference_graph_out_degree={metric.reference_graph_out_degree}",
                            f"unresolved_reference_candidates={metric.unresolved_reference_candidate_count}",
                            f"root_modules={','.join(roots) if roots else '<none>'}",
                        ],
                        remediation="Either reference the declaration from the rooted API surface or remove it if it is genuinely dead.",
                    )
                )
                next_id += 1
                strong_declaration_findings += 1
            module_deadness[module]["strong_dead_declaration_count"] += len(metrics)

        aggregated_modules.append(
            {
                "scope": "analysis_closure",
                "module": module,
                "path": metrics[0].path,
                "dead_declaration_count": len(metrics),
                "dead_component_count": len(components),
                "prioritized_dead_component_count": prioritized_components,
                "prioritized_dead_declaration_count": prioritized_declarations,
                "suppressed_dead_component_count": len(components) - prioritized_components,
                "largest_dead_component_size": largest_component_size,
                "sample_declarations": sample_declarations,
            }
        )

    aggregated_modules.sort(
        key=lambda item: (
            item["dead_declaration_count"],
            item["dead_component_count"],
            item["module"],
        ),
        reverse=True,
    )
    deadness_summary = {
        "scope": "analysis_closure",
        "aggregated_module_count": len(aggregated_modules),
        "aggregated_dead_declaration_count": sum(item["dead_declaration_count"] for item in aggregated_modules),
        "prioritized_dead_component_count": sum(item["prioritized_dead_component_count"] for item in aggregated_modules),
        "prioritized_dead_declaration_count": sum(item["prioritized_dead_declaration_count"] for item in aggregated_modules),
        "suppressed_dead_component_count": sum(item["suppressed_dead_component_count"] for item in aggregated_modules),
        "strong_dead_declaration_finding_count": strong_declaration_findings,
        "top_modules": aggregated_modules[:10],
        "top_components": prioritized_components_summary[:10],
        "suppressed_components": suppressed_components_summary[:10],
    }
    return ReachabilityAnalysis(
        findings=findings,
        module_deadness=dict(module_deadness),
        deadness_summary=deadness_summary,
    )


def add_decision_complexity_findings(
    declaration_metrics: list[DeclarationMetric],
    base_findings: list[LadonFinding],
) -> list[LadonFinding]:
    findings = list(base_findings)
    next_id = len(findings) + 1
    for metric in sorted(
        declaration_metrics,
        key=lambda item: (
            item.parser_decision_complexity or 0,
            item.parser_decision_nesting_complexity or 0,
            item.full_name,
        ),
        reverse=True,
    ):
        complexity = metric.parser_decision_complexity
        if complexity is None or complexity < 11:
            continue
        findings.append(
            LadonFinding(
                id=f"L{next_id:04d}",
                category="parser_surface_decision_hotspot",
                severity="review",
                confidence="heuristic",
                title=f"Parser-surface decision hotspot: {metric.full_name}",
                summary=(
                    f"{metric.full_name} has parser-surface decision complexity {complexity} "
                    f"and nesting-weighted complexity {metric.parser_decision_nesting_complexity}."
                ),
                files=[metric.path],
                modules=[metric.module],
                declarations=[metric.name],
                scope="analysis_closure",
                evidence=[
                    f"decision_complexity={complexity}",
                    f"nesting_complexity={metric.parser_decision_nesting_complexity}",
                    f"rank={metric.parser_decision_rank}",
                    f"kind={metric.kind}",
                ],
                remediation=(
                    "Review whether the declaration can be flattened, split, or rewritten so that parser-visible branching and nesting are easier to inspect."
                ),
            )
        )
        next_id += 1
    return findings


def is_fragility_hotspot(metric: DeclarationMetric) -> bool:
    if metric.fragility_broad_simp_sites >= 1 and metric.fragility_calibrated_score >= 4:
        return True
    if metric.fragility_signal_family_count >= 2 and metric.fragility_calibrated_score >= 5:
        return True
    return metric.fragility_signal_family_count >= 3 and metric.fragility_calibrated_score >= 4


def add_fragility_findings(
    declaration_metrics: list[DeclarationMetric],
    base_findings: list[LadonFinding],
) -> list[LadonFinding]:
    findings = list(base_findings)
    next_id = len(findings) + 1
    for metric in sorted(
        declaration_metrics,
        key=lambda m: (
            m.fragility_calibrated_score,
            m.fragility_signal_family_count,
            m.fragility_score,
            m.fragility_rw_count,
            m.fragility_have_count,
            m.fragility_calc_step_count,
            m.full_name,
        ),
        reverse=True,
    ):
        if not is_fragility_hotspot(metric):
            continue
        findings.append(
            LadonFinding(
                id=f"L{next_id:04d}",
                category="tactic_fragility_smell",
                severity="review",
                confidence="heuristic",
                title=f"Fragile proof-shape hotspot: {metric.full_name}",
                summary=(
                    f"{metric.full_name} shows parser-surface fragility patterns from rewrite, case-split, calc, or local-lemma structure."
                ),
                files=[metric.path],
                modules=[metric.module],
                declarations=[metric.name],
                scope="analysis_closure",
                evidence=[
                    f"fragility_score={metric.fragility_score}",
                    f"fragility_calibrated_score={metric.fragility_calibrated_score}",
                    f"fragility_signal_family_count={metric.fragility_signal_family_count}",
                    f"fragility_calibrated_band={metric.fragility_calibrated_band}",
                    f"simp_like_count={metric.fragility_simp_like_count}",
                    f"broad_simp_sites={metric.fragility_broad_simp_sites}",
                    f"rw_count={metric.fragility_rw_count}",
                    f"by_cases_count={metric.fragility_by_cases_count}",
                    f"calc_step_count={metric.fragility_calc_step_count}",
                    f"have_count={metric.fragility_have_count}",
                ],
                remediation=(
                    "Review whether the proof can be shortened, split into smaller lemmas, or made less rewrite-heavy and less dependent on broad tactic sites."
                ),
            )
        )
        next_id += 1
    return findings


def to_ladon_findings(base_findings: list[audit.Finding], *, scope: str) -> list[LadonFinding]:
    return [
        LadonFinding(
            id=f.id,
            category=f.category,
            severity=f.severity,
            confidence=f.confidence,
            title=f.title,
            summary=f.summary,
            files=list(f.files),
            modules=list(f.modules),
            declarations=[],
            scope=scope,
            evidence=list(f.evidence),
            remediation=f.remediation,
        )
        for f in base_findings
    ]


def summarize_findings(findings: list[LadonFinding], *, scope: str) -> dict[str, Any]:
    by_category = Counter(f.category for f in findings)
    by_severity = Counter(f.severity for f in findings)
    hotspots = Counter()
    for finding in findings:
        for path in finding.files:
            hotspots[path] += 1
    return {
        "scope": scope,
        "total_findings": len(findings),
        "by_category": dict(sorted(by_category.items())),
        "by_severity": dict(sorted(by_severity.items())),
        "top_hotspots": [
            {"scope": scope, "path": path, "finding_count": count}
            for path, count in hotspots.most_common(10)
        ],
    }


def structure_field_blocks(source_slice: str) -> list[dict[str, str]]:
    lines = source_slice.splitlines()
    starts: list[tuple[int, re.Match[str]]] = []
    for index, line in enumerate(lines):
        match = STRUCTURE_FIELD_LINE_RE.match(line)
        if match:
            starts.append((index, match))
    out: list[dict[str, str]] = []
    for offset, (index, match) in enumerate(starts):
        next_index = starts[offset + 1][0] if offset + 1 < len(starts) else len(lines)
        block_lines = lines[index:next_index]
        type_lines = [match.group("type").strip()]
        type_lines.extend(line.strip() for line in block_lines[1:])
        type_snippet = " ".join(part for part in type_lines if part)
        out.append(
            {
                "name": match.group("name"),
                "type": type_snippet,
                "line": str(index + 1),
            }
        )
    return out


def is_certificate_shaped_structure(metric: DeclarationMetric, source_slice: str) -> bool:
    if CERTIFICATE_STRUCTURE_RE.search(metric.full_name):
        return True
    if "certificate" in source_slice.lower() or "high-confidence" in source_slice.lower():
        return True
    return False


def is_prop_like_field(field_type: str) -> bool:
    return bool(PROP_SHAPE_RE.search(field_type))


def add_certificate_boundary_findings(
    *,
    root: Path,
    declaration_metrics: list[DeclarationMetric],
    base_findings: list[LadonFinding],
) -> list[LadonFinding]:
    findings = list(base_findings)
    next_id = len(findings) + 1
    source_slices = declaration_source_slices(root, declaration_metrics)
    for metric in declaration_metrics:
        if metric.kind != "structure":
            continue
        source_slice = source_slices.get(metric.full_name, "")
        if not is_certificate_shaped_structure(metric, source_slice):
            continue
        for field_info in structure_field_blocks(source_slice):
            field_name = field_info["name"]
            field_type = field_info["type"]
            if CERTIFICATE_FIELD_RE.search(field_name):
                findings.append(
                    LadonFinding(
                        id=f"L{next_id:04d}",
                        category="imported_certificate_seam",
                        severity="review",
                        confidence="heuristic",
                        title=f"Imported/assumed certificate seam: {metric.full_name}.{field_name}",
                        summary=(
                            f"{metric.full_name}.{field_name} appears to encode an imported or assumed certificate fact. "
                            "Lean can consume this field, but Ladon cannot verify that runtime evidence earns it."
                        ),
                        files=[metric.path],
                        modules=[metric.module],
                        declarations=[metric.name],
                        scope="analysis_closure",
                        evidence=[
                            f"structure={metric.full_name}",
                            f"field={field_name}",
                            f"field_type={field_type[:240] if field_type else '<empty>'}",
                            "boundary_kind=conditional_certificate_seam",
                        ],
                        remediation=(
                            "Ensure a Lean theorem, OpenSpec contract, or accepted imported-runtime seam explains how this field is supplied."
                        ),
                    )
                )
                next_id += 1
            if CERTIFICATE_FIELD_RE.search(field_name) and is_prop_like_field(field_type):
                findings.append(
                    LadonFinding(
                        id=f"L{next_id:04d}",
                        category="prop_field_certificate_assumption",
                        severity="review",
                        confidence="heuristic",
                        title=f"Prop-valued certificate assumption: {metric.full_name}.{field_name}",
                        summary=(
                            f"{metric.full_name}.{field_name} is a proposition-shaped certificate field. "
                            "It is a hypothesis of the certificate boundary, not evidence constructed by Ladon."
                        ),
                        files=[metric.path],
                        modules=[metric.module],
                        declarations=[metric.name],
                        scope="analysis_closure",
                        evidence=[
                            f"structure={metric.full_name}",
                            f"field={field_name}",
                            f"field_type={field_type[:240] if field_type else '<empty>'}",
                            "boundary_kind=prop_hypothesis",
                        ],
                        remediation=(
                            "Check that downstream proof notes or runtime artifact validators explicitly discharge this hypothesis."
                        ),
                    )
                )
                next_id += 1
    return findings


def verify_source_surface_directly(
    root: Path,
    extraction: ExtractionResult,
    root_decls: Sequence[DeclarationMetric],
) -> dict[str, Any]:
    source_path = root / extraction.analysis_root_file
    checks = [f"#check {metric.full_name}" for metric in root_decls]
    source_text = source_path.read_text(encoding="utf-8")
    with tempfile.NamedTemporaryFile("w", suffix=".lean", encoding="utf-8", delete=False) as handle:
        handle.write(source_text)
        if source_text and not source_text.endswith("\n"):
            handle.write("\n")
        handle.write("\n")
        handle.write("\n".join(checks))
        handle.write("\n")
        temp_path = Path(handle.name)
    command = ["lake", "env", "lean", str(temp_path)]
    try:
        proc = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    finally:
        try:
            temp_path.unlink()
        except OSError:
            pass
    return {
        "status": "passed" if proc.returncode == 0 else "failed",
        "command": command,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
    }


def verify_export_surface(
    *,
    root: Path,
    extraction: ExtractionResult,
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[LadonFinding]]:
    root_decls = [
        metric
        for metric in extraction.declaration_metrics
        if metric.module == extraction.analysis_root_module and metric.kind != "instance"
    ]
    if not args.verify_export_surface:
        return (
            {
                "status": "skipped",
                "command": None,
                "checked_declaration_count": 0,
                "missing_declaration_count": 0,
                "missing_declarations": [],
                "stdout": "",
                "stderr": "",
            },
            [],
        )
    if not root_decls:
        return (
            {
                "status": "passed",
                "command": None,
                "checked_declaration_count": 0,
                "missing_declaration_count": 0,
                "missing_declarations": [],
                "stdout": "",
                "stderr": "",
            },
            [],
        )
    lean_lines = [f"import {extraction.analysis_root_module}", ""]
    for metric in root_decls:
        lean_lines.append(f"#check {metric.full_name}")
    with tempfile.NamedTemporaryFile("w", suffix=".lean", encoding="utf-8", delete=False) as handle:
        handle.write("\n".join(lean_lines) + "\n")
        temp_path = Path(handle.name)
    command = ["lake", "env", "lean", str(temp_path)]
    try:
        proc = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    finally:
        try:
            temp_path.unlink()
        except OSError:
            pass
    combined_output = proc.stdout + "\n" + proc.stderr
    missing = [
        metric.full_name
        for metric in root_decls
        if (
            f"Unknown identifier `{metric.full_name}`" in combined_output
            or f"Unknown constant `{metric.full_name}`" in combined_output
        )
    ]
    if proc.returncode != 0 and not missing:
        missing = [metric.full_name for metric in root_decls]
    status = "passed" if proc.returncode == 0 and not missing else "failed"
    source_check = verify_source_surface_directly(root, extraction, root_decls) if missing else None
    stale_build_suspected = bool(source_check and source_check["status"] == "passed")
    findings: list[LadonFinding] = []
    for index, full_name in enumerate(missing, start=1):
        metric = next((item for item in root_decls if item.full_name == full_name), None)
        category = (
            "source_export_mismatch_stale_build_suspected"
            if stale_build_suspected
            else "source_export_mismatch"
        )
        title = (
            f"Probable stale export artifact: {full_name}"
            if stale_build_suspected
            else f"Source declaration is not exported: {full_name}"
        )
        summary = (
            f"{full_name} is checkable when Ladon appends #check commands to the source file, "
            f"but is not exposed by importing {extraction.analysis_root_module}. "
            "That pattern usually means the module's compiled export artifact is stale."
            if stale_build_suspected
            else f"{full_name} was parsed from source under the analysis root, but Lean did not expose it when importing {extraction.analysis_root_module}."
        )
        evidence = [
            f"analysis_root_module={extraction.analysis_root_module}",
            f"export_check_status={status}",
            f"command={' '.join(command)}",
        ]
        if source_check:
            evidence.extend(
                [
                    f"source_check_status={source_check['status']}",
                    f"source_check_command={' '.join(source_check['command']) if source_check['command'] else '<none>'}",
                ]
            )
        remediation = (
            f"Run `lake build {extraction.analysis_root_module}` and rerun ladon; if the mismatch remains, inspect private/non-exported declarations."
            if stale_build_suspected
            else "Run a real Lean build and check whether parser-qualified source names match elaborated exported constants."
        )
        findings.append(
            LadonFinding(
                id=f"L{index:04d}",
                category=category,
                severity="review",
                confidence="heuristic" if stale_build_suspected else "deterministic",
                title=title,
                summary=summary,
                files=[metric.path if metric else extraction.analysis_root_file],
                modules=[metric.module if metric else extraction.analysis_root_module],
                declarations=[metric.name if metric else full_name.split(".")[-1]],
                scope="analysis_closure",
                evidence=evidence,
                remediation=remediation,
            )
        )
    return (
        {
            "status": status,
            "command": command,
            "checked_declaration_count": len(root_decls),
            "missing_declaration_count": len(missing),
            "missing_declarations": missing,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
            "source_check_status": None if source_check is None else source_check["status"],
            "source_check_command": None if source_check is None else source_check["command"],
            "stale_build_artifact_suspected": stale_build_suspected,
        },
        findings,
    )


def add_closure_explosion_findings(
    *,
    extraction: ExtractionResult,
    modules: dict[str, audit.ModuleInfo],
    declaration_metrics: list[DeclarationMetric],
    base_findings: list[LadonFinding],
    module_threshold: int = CLOSURE_EXPLOSION_MODULE_THRESHOLD,
    declaration_threshold: int = CLOSURE_EXPLOSION_DECLARATION_THRESHOLD,
    direct_import_threshold: int = CLOSURE_EXPLOSION_DIRECT_IMPORT_THRESHOLD,
) -> list[LadonFinding]:
    findings = list(base_findings)
    module_count = len(extraction.analysis_closure_modules)
    declaration_count = len(declaration_metrics)
    root_info = modules.get(extraction.analysis_root_module)
    direct_import_count = len(root_info.imports) if root_info else 0
    is_leaf_style_root = "/" in extraction.analysis_root_file
    if not is_leaf_style_root:
        return findings
    if module_count < module_threshold and declaration_count < declaration_threshold:
        return findings
    sampled_children = [
        module
        for module in extraction.analysis_closure_modules
        if module != extraction.analysis_root_module
    ][:12]
    import_impacts = direct_import_closure_impacts(
        extraction=extraction,
        modules=modules,
        declaration_metrics=declaration_metrics,
    )["top_imports"]
    top_import_evidence = [
        f"{item['import']}:modules={item['module_count']}:decls={item['declaration_count']}"
        for item in import_impacts[:5]
    ]
    findings.append(
        LadonFinding(
            id=f"L{len(findings) + 1:04d}",
            category="analysis_closure_explosion",
            severity="review",
            confidence="heuristic",
            title=f"Analysis closure is broad for leaf owner: {extraction.analysis_root_module}",
            summary=(
                f"{extraction.analysis_root_module} is a leaf-style analysis root, but its import closure contains "
                f"{module_count} modules and {declaration_count} declarations."
            ),
            files=[extraction.analysis_root_file],
            modules=[extraction.analysis_root_module],
            declarations=[],
            scope="analysis_closure",
            evidence=[
                f"module_count={module_count}",
                f"declaration_count={declaration_count}",
                f"direct_import_count={direct_import_count}",
                f"module_threshold={module_threshold}",
                f"declaration_threshold={declaration_threshold}",
                f"direct_import_threshold={direct_import_threshold}",
                f"sampled_import_closure={','.join(sampled_children)}",
                f"direct_import_impacts={';'.join(top_import_evidence) if top_import_evidence else '<none>'}",
            ],
            remediation=(
                "Inspect whether the owner is importing a broad theorem stack directly; consider splitting a narrow witness facade from the heavy proof/program owner."
            ),
        )
    )
    return findings


def likely_python_witness_file(path: Path, text: str) -> bool:
    lower_name = path.name.lower()
    if any(token in lower_name for token in ["witness", "checker", "validate", "verify", "certificate"]):
        return bool(PYTHON_WITNESS_RE.search(text))
    return "certificate" in text.lower() and "json" in text.lower() and bool(PYTHON_WITNESS_RE.search(text))


def python_witness_has_explicit_boundary(path: Path, root: Path, text: str) -> bool:
    rel_parts = path.relative_to(root).parts
    if rel_parts and rel_parts[0] == "tests" and path.name.startswith("test_"):
        return True
    return bool(THEOREM_SURFACE_RE.search(text) or PYTHON_WITNESS_BOUNDARY_RE.search(text))


def scan_python_witnesses(root: Path, base_findings: list[LadonFinding]) -> list[LadonFinding]:
    findings = list(base_findings)
    next_id = len(findings) + 1
    candidate_dirs = [root / "scripts", root / "local-scripts", root / "tests"]
    for directory in candidate_dirs:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*.py")):
            rel_path = repo_relative_path(root, path)
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if not likely_python_witness_file(path, text):
                continue
            if python_witness_has_explicit_boundary(path, root, text):
                continue
            findings.append(
                LadonFinding(
                    id=f"L{next_id:04d}",
                    category="python_witness_without_theorem_surface",
                    severity="review",
                    confidence="heuristic",
                    title=f"Python witness lacks theorem-surface reference: {rel_path}",
                    summary=(
                        f"{rel_path} looks like a witness/checker for runtime certificate artifacts, but Ladon did not find a Lean/OpenSpec theorem-surface reference in the file."
                    ),
                    files=[rel_path],
                    modules=[],
                    declarations=[],
                    scope="repo_inventory",
                    evidence=[
                        "scanner=python_witness_ordering",
                        "expected_reference=Mf/*.lean or openspec capability/theorem surface",
                    ],
                    remediation=(
                        "Document which Lean/OpenSpec theorem-facing contract this witness checks, or mark it as debugging-only."
                    ),
                )
            )
            next_id += 1
    return findings


def looks_like_json_witness_artifact(path: Path, root: Path, data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    rel_parts = path.relative_to(root).parts
    if len(rel_parts) >= 3 and rel_parts[0] == "witnesses" and "artifacts" in rel_parts:
        return True
    return any(key in data for key in ["artifactKind", "witnessKind", "claimBoundary", "leanOwner", "theoremOrClaim"])


def collect_theorem_surface_strings(value: Any, parent_key: str = "") -> list[str]:
    collected: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            next_key = f"{parent_key}.{key}" if parent_key else str(key)
            if isinstance(child, str) and any(token in key_lower for token in ["lean", "theorem", "owner", "openspec"]):
                collected.append(child)
            collected.extend(collect_theorem_surface_strings(child, next_key))
    elif isinstance(value, list):
        for child in value:
            collected.extend(collect_theorem_surface_strings(child, parent_key))
    return collected


def lean_owner_paths(value: Any) -> list[str]:
    owners: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            if isinstance(child, str) and key_lower in {"leanowner", "lean_owner", "leanownerpath", "lean_owner_path"}:
                owners.append(child)
            owners.extend(lean_owner_paths(child))
    elif isinstance(value, list):
        for child in value:
            owners.extend(lean_owner_paths(child))
    return owners


def scan_json_witness_artifacts(root: Path, base_findings: list[LadonFinding]) -> list[LadonFinding]:
    findings = list(base_findings)
    next_id = len(findings) + 1
    artifact_paths = sorted((root / "witnesses").glob("**/artifacts/*.json")) if (root / "witnesses").exists() else []
    for artifact_path in artifact_paths:
        rel_path = repo_relative_path(root, artifact_path)
        try:
            data = load_json_artifact(artifact_path)
        except (OSError, json.JSONDecodeError):
            continue
        if not looks_like_json_witness_artifact(artifact_path, root, data):
            continue
        surface_strings = collect_theorem_surface_strings(data)
        if not any(THEOREM_SURFACE_RE.search(item) for item in surface_strings):
            findings.append(
                LadonFinding(
                    id=f"L{next_id:04d}",
                    category="json_witness_without_theorem_surface",
                    severity="review",
                    confidence="heuristic",
                    title=f"JSON witness lacks theorem-surface metadata: {rel_path}",
                    summary=(
                        f"{rel_path} looks like a Python/JSON witness artifact, but Ladon did not find Lean/OpenSpec owner or theorem metadata."
                    ),
                    files=[rel_path],
                    modules=[],
                    declarations=[],
                    scope="repo_inventory",
                    evidence=[
                        "scanner=json_witness_artifact_metadata",
                        "expected_reference=leanOwner, lean_theorem, theorem owner, or openspec change/spec path",
                    ],
                    remediation="Add explicit Lean/OpenSpec owner metadata to the witness artifact, or keep it outside witnesses/**/artifacts.",
                )
            )
            next_id += 1
            continue
        for owner in lean_owner_paths(data):
            if owner.endswith(".lean") and not (root / owner).exists():
                findings.append(
                    LadonFinding(
                        id=f"L{next_id:04d}",
                        category="json_witness_missing_lean_owner",
                        severity="review",
                        confidence="deterministic",
                        title=f"JSON witness references missing Lean owner: {rel_path}",
                        summary=f"{rel_path} declares Lean owner {owner}, but that file does not exist in the repository.",
                        files=[rel_path],
                        modules=[],
                        declarations=[],
                        scope="repo_inventory",
                        evidence=[f"leanOwner={owner}", "scanner=json_witness_artifact_metadata"],
                        remediation="Fix the artifact metadata or restore the referenced Lean owner file.",
                    )
                )
                next_id += 1
    return findings


def load_json_artifact(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


PACKET_TEXT_SUFFIXES = {".lean", ".md", ".txt", ".json", ".yaml", ".yml", ".py", ".csv", ".toml", ".tex"}
PACKET_EXACT_TARGET_RE = re.compile(
    r"(?:exact[-\s]?(?:finite|adjacent|objective|sensitivity|cap)|finite[-\s]?factor|reconstructed\s+factor|exactFactor|bifrFactorC)",
    re.IGNORECASE,
)
PACKET_ANALYTIC_TARGET_RE = re.compile(
    r"(?:analytic\s+BISR|BISR|square[-\s]?root|sqrt|bifrAnalyticFactorC)",
    re.IGNORECASE,
)


def resolve_packet_dir(root: Path, raw_packet_dir: str | None) -> Path | None:
    if not raw_packet_dir:
        return None
    packet_dir = Path(raw_packet_dir)
    if not packet_dir.is_absolute():
        packet_dir = root / packet_dir
    if packet_dir.exists() and not any(
        (packet_dir / rel).exists() for rel in ("data/source-map.json", "source-map.json")
    ):
        nested = [
            child
            for child in packet_dir.iterdir()
            if child.is_dir()
            and any((child / rel).exists() for rel in ("data/source-map.json", "source-map.json"))
        ]
        if len(nested) == 1:
            return nested[0]
    return packet_dir


def packet_source_map_entries(packet_dir: Path) -> list[dict[str, Any]]:
    for rel in ("data/source-map.json", "source-map.json"):
        path = packet_dir / rel
        if not path.exists():
            continue
        try:
            data = load_json_artifact(path)
        except (OSError, json.JSONDecodeError):
            return []
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        entries = data.get("entries") if isinstance(data, dict) else None
        if entries is None and isinstance(data, dict):
            entries = data.get("sources")
        if isinstance(entries, list):
            return [entry for entry in entries if isinstance(entry, dict)]
        if isinstance(data, dict):
            mapped_entries = packet_source_map_mapping_entries(data)
            if mapped_entries:
                return mapped_entries
    return []


def packet_source_map_mapping_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for archive_path, value in data.items():
        if not packet_path_looks_like_source_entry(archive_path):
            continue
        entry: dict[str, Any] = {"archivePath": archive_path}
        if isinstance(value, str):
            entry["repositoryPath"] = value
        elif isinstance(value, dict):
            entry.update(value)
            entry.setdefault("archivePath", archive_path)
        elif value is not None:
            continue
        entry.setdefault(
            "role",
            "validated JSON" if archive_path.endswith(".json") else "source file",
        )
        entries.append(entry)
    return entries


def packet_path_looks_like_source_entry(path: str) -> bool:
    if not isinstance(path, str) or not path:
        return False
    if path in {"README.md", "REVIEW_DELTA.md"}:
        return True
    if path.startswith(("data/", "docs/", "lean/", "Mf/", "witnesses/", "openspec/")):
        return True
    suffix = Path(path).suffix
    return "/" in path and suffix in PACKET_TEXT_SUFFIXES


def packet_entry_archive_path(entry: dict[str, Any]) -> str:
    for key in ("archivePath", "path", "packetPath", "sourcePath"):
        value = entry.get(key)
        if isinstance(value, str):
            return value
    return ""


def packet_entry_repo_path(entry: dict[str, Any]) -> str:
    for key in ("repoPath", "repositoryPath"):
        value = entry.get(key)
        if isinstance(value, str):
            return value
    return ""


def packet_entry_role(entry: dict[str, Any]) -> str:
    value = entry.get("role")
    return value if isinstance(value, str) else ""


def packet_role_is_authority(role: str) -> bool:
    normalized = role.strip().lower()
    return normalized == "authority" or normalized.startswith("authority:")


def packet_role_is_background(role: str) -> bool:
    normalized = role.strip().lower()
    return "background" in normalized or normalized in {"supporting", "context"}


def packet_role_is_runtime(role: str) -> bool:
    return "runtime" in role.strip().lower()


def packet_manifest_entry_points(packet_dir: Path) -> set[str]:
    path = packet_dir / "data" / "packet-manifest.json"
    if not path.exists():
        return set()
    try:
        data = load_json_artifact(path)
    except (OSError, json.JSONDecodeError):
        return set()
    entry_points = data.get("entryPoints") if isinstance(data, dict) else None
    if not isinstance(entry_points, list):
        return set()
    return {item for item in entry_points if isinstance(item, str)}


def packet_path_is_runtime_json(archive_path: str) -> bool:
    return archive_path.startswith("data/runtime/") and archive_path.endswith(".json")


def packet_entry_point_is_authority(archive_path: str, repo_path: str) -> bool:
    if archive_path.endswith(".lean") or repo_path.endswith(".lean"):
        return True
    if archive_path.startswith("openspec/") or repo_path.startswith("openspec/"):
        return True
    if archive_path.startswith("docs/") or repo_path.startswith("docs/"):
        return archive_path.endswith(".md") or repo_path.endswith(".md")
    return False


def packet_generic_source_role_is_background(archive_path: str, repo_path: str) -> bool:
    return (
        archive_path.endswith(".lean")
        or repo_path.endswith(".lean")
        or archive_path.startswith("docs/")
        or repo_path.startswith("docs/")
        or archive_path.startswith("openspec/")
        or repo_path.startswith("openspec/")
    )


def normalize_packet_source_map_entries(packet_dir: Path, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entry_points = packet_manifest_entry_points(packet_dir)
    normalized: list[dict[str, Any]] = []
    for entry in entries:
        item = dict(entry)
        role = packet_entry_role(item)
        archive_path = packet_entry_archive_path(item)
        repo_path = packet_entry_repo_path(item)
        role_normalized = role.strip().lower()
        inferred_role = role
        if archive_path in entry_points:
            if packet_path_is_runtime_json(archive_path):
                inferred_role = "runtime-diagnostic"
            elif packet_entry_point_is_authority(archive_path, repo_path):
                inferred_role = "authority"
        elif packet_path_is_runtime_json(archive_path):
            inferred_role = "background-runtime-diagnostic"
        elif role_normalized in {"source file", "validated json"}:
            if packet_generic_source_role_is_background(archive_path, repo_path):
                inferred_role = "background"
        if inferred_role != role:
            item["originalRole"] = role
            item["role"] = inferred_role
        normalized.append(item)
    return normalized


def packet_path_for_entry(packet_dir: Path, entry: dict[str, Any]) -> Path:
    archive_path = packet_entry_archive_path(entry)
    return packet_dir / archive_path if archive_path else packet_dir


def read_packet_path_text(path: Path, max_files: int = 32) -> str:
    if path.is_file() and path.suffix in PACKET_TEXT_SUFFIXES:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
    if not path.is_dir():
        return ""
    chunks: list[str] = []
    for child in sorted(path.rglob("*")):
        if len(chunks) >= max_files:
            break
        if child.is_file() and child.suffix in PACKET_TEXT_SUFFIXES:
            try:
                chunks.append(child.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
    return "\n".join(chunks)


def classify_packet_target(text: str) -> set[str]:
    targets: set[str] = set()
    if PACKET_EXACT_TARGET_RE.search(text):
        targets.add("exact_finite_factor")
    if PACKET_ANALYTIC_TARGET_RE.search(text):
        targets.add("analytic_bisr")
    return targets


def packet_runtime_artifact_entries(packet_dir: Path, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for entry in entries:
        role = packet_entry_role(entry)
        archive_path = packet_entry_archive_path(entry)
        if packet_role_is_runtime(role) and archive_path.endswith(".json"):
            role_normalized = role.strip().lower()
            items.append(
                {
                    "path": packet_dir / archive_path,
                    "role": role,
                    "listed_in_source_map": True,
                    "primary": role_normalized == "runtime-diagnostic"
                    or role_normalized.startswith("runtime:"),
                }
            )
    if items:
        return sorted(items, key=lambda item: str(item["path"]))
    runtime_root = packet_dir / "data" / "runtime"
    if runtime_root.exists():
        for path in sorted(runtime_root.rglob("*.json")):
            if path.is_file():
                items.append(
                    {
                        "path": path,
                        "role": "runtime-diagnostic",
                        "listed_in_source_map": False,
                        "primary": True,
                    }
                )
    return items


def packet_claim_boundary(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    value = data.get("claimBoundary")
    if isinstance(value, str):
        return value
    for key, child in data.items():
        if str(key).lower() == "claimboundary" and isinstance(child, str):
            return child
    return ""


def packet_role_target_summary(packet_dir: Path, entries: list[dict[str, Any]]) -> dict[str, Any]:
    role_counts = Counter(packet_entry_role(entry) or "<missing>" for entry in entries)
    authority_entries: list[dict[str, Any]] = []
    background_entries: list[dict[str, Any]] = []
    for entry in entries:
        role = packet_entry_role(entry)
        path_text = " ".join([packet_entry_archive_path(entry), packet_entry_repo_path(entry)])
        text = path_text + "\n" + read_packet_path_text(packet_path_for_entry(packet_dir, entry))
        targets = sorted(classify_packet_target(text))
        item = {
            "role": role,
            "archive_path": packet_entry_archive_path(entry),
            "repo_path": packet_entry_repo_path(entry),
            "targets": targets,
        }
        if packet_role_is_authority(role):
            authority_entries.append(item)
        elif packet_role_is_background(role):
            background_entries.append(item)
    return {
        "role_counts": dict(sorted(role_counts.items())),
        "authority_entries": authority_entries,
        "background_entries": background_entries,
        "authority_targets": sorted({target for entry in authority_entries for target in entry["targets"]}),
        "background_targets": sorted({target for entry in background_entries for target in entry["targets"]}),
    }


def packet_repo_drift_details(root: Path, packet_dir: Path, entry: dict[str, Any]) -> list[str]:
    archive_path = packet_entry_archive_path(entry)
    repo_path = packet_entry_repo_path(entry)
    if not archive_path or not repo_path:
        return []
    packet_path = packet_dir / archive_path
    live_path = root / repo_path
    if not packet_path.exists() or not live_path.exists():
        return []
    if packet_path.is_file() and live_path.is_file():
        try:
            return ["file_content_differs"] if packet_path.read_bytes() != live_path.read_bytes() else []
        except OSError:
            return []
    if not packet_path.is_dir() or not live_path.is_dir():
        return ["path_kind_differs"]
    details: list[str] = []
    for packet_child in sorted(packet_path.rglob("*")):
        if len(details) >= 8:
            details.append("additional_differences_truncated")
            break
        if not packet_child.is_file() or packet_child.suffix not in PACKET_TEXT_SUFFIXES:
            continue
        rel_child = packet_child.relative_to(packet_path)
        live_child = live_path / rel_child
        if not live_child.exists():
            details.append(f"missing_live_file={rel_child}")
            continue
        if not live_child.is_file():
            details.append(f"path_kind_differs={rel_child}")
            continue
        try:
            if packet_child.read_bytes() != live_child.read_bytes():
                details.append(f"file_content_differs={rel_child}")
        except OSError:
            continue
    return details


def analyze_packet_review(root: Path, args: argparse.Namespace) -> tuple[dict[str, Any], list[LadonFinding]]:
    packet_dir = resolve_packet_dir(root, args.packet_dir)
    if packet_dir is None:
        return {"status": "unavailable"}, []
    rel_packet_dir = str(packet_dir)
    findings: list[LadonFinding] = []
    next_id = 1
    if not packet_dir.exists():
        findings.append(
            LadonFinding(
                id=f"P{next_id:04d}",
                category="packet_dir_missing",
                severity="review",
                confidence="deterministic",
                title="Packet directory does not exist",
                summary=f"Requested packet directory {packet_dir} could not be read.",
                files=[rel_packet_dir],
                modules=[],
                declarations=[],
                scope="packet_review",
                evidence=[f"packet_dir={packet_dir}"],
                remediation="Extract the review packet first or pass the correct --packet-dir path.",
            )
        )
        return {"status": "failed", "packet_dir": rel_packet_dir}, findings

    entries = normalize_packet_source_map_entries(packet_dir, packet_source_map_entries(packet_dir))
    source_map_status = "present" if entries else "missing"
    if not entries:
        findings.append(
            LadonFinding(
                id=f"P{next_id:04d}",
                category="packet_source_map_missing",
                severity="review",
                confidence="deterministic",
                title="Packet source map missing",
                summary="Packet audit cannot connect runtime artifacts to theorem owners without data/source-map.json.",
                files=[rel_packet_dir],
                modules=[],
                declarations=[],
                scope="packet_review",
                evidence=["expected=data/source-map.json"],
                remediation="Add data/source-map.json with role-tagged authority, background, runtime, and witness entries.",
            )
        )
        next_id += 1
    packet_repo_drift_count = 0
    for entry in entries:
        drift_details = packet_repo_drift_details(root, packet_dir, entry)
        if not drift_details:
            continue
        archive_path = packet_entry_archive_path(entry)
        repo_path = packet_entry_repo_path(entry)
        packet_repo_drift_count += 1
        findings.append(
            LadonFinding(
                id=f"P{next_id:04d}",
                category="packet_source_repo_drift",
                severity="review",
                confidence="deterministic",
                title=f"Packet source differs from live repo: {archive_path}",
                summary=(
                    "A source-map entry exists both in the extracted packet and the live repository, "
                    "but the contents differ. Packet-local validation may not reflect the current repo state."
                ),
                files=[archive_path, repo_path],
                modules=[],
                declarations=[],
                scope="packet_review",
                evidence=[
                    f"role={packet_entry_role(entry) or '<missing>'}",
                    f"archivePath={archive_path}",
                    f"repoPath={repo_path}",
                    *drift_details[:8],
                ],
                remediation=(
                    "Regenerate the packet from the current repo state, or explicitly mark it as a historical/staged packet."
                ),
            )
        )
        next_id += 1

    role_summary = packet_role_target_summary(packet_dir, entries)
    runtime_entries = packet_runtime_artifact_entries(packet_dir, entries)
    runtime_items: list[dict[str, Any]] = []
    runtime_targets: set[str] = set()
    for runtime_entry in runtime_entries:
        runtime_path = runtime_entry["path"]
        rel_path = str(runtime_path.relative_to(packet_dir)) if runtime_path.is_relative_to(packet_dir) else str(runtime_path)
        try:
            data = load_json_artifact(runtime_path)
        except (OSError, json.JSONDecodeError):
            continue
        boundary = packet_claim_boundary(data)
        targets = classify_packet_target(boundary + "\n" + json.dumps(data.get("artifactKind", "")) + "\n" + json.dumps(data.get("witnessKind", ""))) if isinstance(data, dict) else set()
        runtime_targets.update(targets)
        runtime_items.append(
            {
                "path": rel_path,
                "role": runtime_entry["role"],
                "listed_in_source_map": runtime_entry["listed_in_source_map"],
                "primary": runtime_entry["primary"],
                "claim_boundary": boundary,
                "targets": sorted(targets),
            }
        )
        if not boundary:
            findings.append(
                LadonFinding(
                    id=f"P{next_id:04d}",
                    category="packet_runtime_missing_claim_boundary",
                    severity="review",
                    confidence="deterministic",
                    title=f"Runtime artifact lacks claim boundary: {rel_path}",
                    summary="Runtime artifacts in review packets should state whether they are proof evidence, diagnostics, or theorem-target hints.",
                    files=[rel_path],
                    modules=[],
                    declarations=[],
                    scope="packet_review",
                    evidence=["field=claimBoundary"],
                    remediation="Add claimBoundary to the runtime JSON artifact.",
                )
            )
            next_id += 1

    authority_targets = set(role_summary["authority_targets"])
    background_targets = set(role_summary["background_targets"])
    packet_surface_targets = authority_targets | background_targets
    for item in runtime_items:
        if (
            item["primary"]
            and item["claim_boundary"]
            and not item["targets"]
            and len(packet_surface_targets) > 1
        ):
            findings.append(
                LadonFinding(
                    id=f"P{next_id:04d}",
                    category="packet_runtime_target_boundary_ambiguous",
                    severity="review",
                    confidence="heuristic",
                    title=f"Runtime artifact claim boundary is target-ambiguous: {item['path']}",
                    summary=(
                        "The packet contains multiple theorem-target families, but this runtime artifact's claimBoundary "
                        "does not say which one it supports."
                    ),
                    files=[item["path"]],
                    modules=[],
                    declarations=[],
                    scope="packet_review",
                    evidence=[
                        f"claimBoundary={item['claim_boundary']}",
                        f"packet_surface_targets={sorted(packet_surface_targets)}",
                    ],
                    remediation=(
                        "Make the runtime artifact claimBoundary name the theorem target explicitly, for example exact finite-factor "
                        "diagnostic vs analytic/BISR square-root diagnostic."
                    ),
                )
            )
            next_id += 1
    exact_runtime = "exact_finite_factor" in runtime_targets
    analytic_runtime = "analytic_bisr" in runtime_targets
    exact_authority = "exact_finite_factor" in authority_targets
    analytic_authority = "analytic_bisr" in authority_targets
    analytic_background = "analytic_bisr" in background_targets

    if exact_runtime and not exact_authority:
        findings.append(
            LadonFinding(
                id=f"P{next_id:04d}",
                category="packet_runtime_authority_target_mismatch",
                severity="review",
                confidence="heuristic",
                title="Exact finite-factor runtime artifact lacks exact-factor authority owner",
                summary=(
                    "A runtime artifact claims an exact finite-factor/reconstructed-factor target, "
                    "but the packet source map does not mark an exact-factor Lean/doc/OpenSpec surface as authority."
                ),
                files=[item["path"] for item in runtime_items if "exact_finite_factor" in item["targets"]],
                modules=[],
                declarations=[],
                scope="packet_review",
                evidence=[
                    f"runtime_targets={sorted(runtime_targets)}",
                    f"authority_targets={sorted(authority_targets)}",
                    f"background_targets={sorted(background_targets)}",
                ],
                remediation=(
                    "Mark the exact finite-factor owner as role=authority and demote analytic/BISR comparison surfaces to background/supporting, "
                    "or change the runtime artifact claim boundary."
                ),
            )
        )
        next_id += 1
    if analytic_runtime and not analytic_authority:
        findings.append(
            LadonFinding(
                id=f"P{next_id:04d}",
                category="packet_runtime_authority_target_mismatch",
                severity="review",
                confidence="heuristic",
                title="Analytic/BISR runtime artifact lacks analytic authority owner",
                summary=(
                    "A runtime artifact claims an analytic/BISR/square-root target, "
                    "but the packet source map does not mark an analytic owner as authority."
                ),
                files=[item["path"] for item in runtime_items if "analytic_bisr" in item["targets"]],
                modules=[],
                declarations=[],
                scope="packet_review",
                evidence=[
                    f"runtime_targets={sorted(runtime_targets)}",
                    f"authority_targets={sorted(authority_targets)}",
                    f"background_targets={sorted(background_targets)}",
                ],
                remediation="Mark the analytic theorem owner as role=authority or correct the runtime claim boundary.",
            )
        )
        next_id += 1

    if exact_runtime and exact_authority and analytic_background:
        separation_status = "explicit_exact_authority_with_analytic_background"
    elif exact_runtime and exact_authority:
        separation_status = "explicit_exact_authority"
    elif exact_runtime and not exact_authority:
        separation_status = "mismatch_exact_runtime_without_exact_authority"
    elif (
        runtime_items
        and any(item["primary"] and not item["targets"] for item in runtime_items)
        and len(packet_surface_targets) > 1
    ):
        separation_status = "ambiguous_runtime_claim_boundary"
    elif runtime_targets:
        separation_status = "target_classified"
    else:
        separation_status = "unclassified_runtime_target"

    summary = {
        "status": "audited",
        "packet_dir": rel_packet_dir,
        "source_map_status": source_map_status,
        "source_map_entry_count": len(entries),
        "runtime_artifact_count": len(runtime_items),
        "role_counts": role_summary["role_counts"],
        "authority_targets": sorted(authority_targets),
        "background_targets": sorted(background_targets),
        "runtime_targets": sorted(runtime_targets),
        "target_separation_status": separation_status,
        "packet_repo_drift_count": packet_repo_drift_count,
        "runtime_artifacts": runtime_items[:20],
        "authority_entries": role_summary["authority_entries"][:20],
        "background_entries": role_summary["background_entries"][:20],
        "finding_count": len(findings),
    }
    return summary, findings


def iter_dicts(value: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(value, dict):
        out.append(value)
        for child in value.values():
            out.extend(iter_dicts(child))
    elif isinstance(value, list):
        for child in value:
            out.extend(iter_dicts(child))
    return out


def first_present(mapping: dict[str, Any], names: Sequence[str]) -> Any:
    for name in names:
        if name in mapping and mapping[name] is not None:
            return mapping[name]
    return None


def as_finite_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def add_artifact_gap(
    findings: list[LadonFinding],
    *,
    finding_id: int,
    path: str,
    title: str,
    summary: str,
    evidence: list[str],
) -> int:
    findings.append(
        LadonFinding(
            id=f"L{finding_id:04d}",
            category="runtime_artifact_contract_gap",
            severity="review",
            confidence="deterministic",
            title=title,
            summary=summary,
            files=[path],
            modules=[],
            declarations=[],
            scope="repo_inventory",
            evidence=evidence,
            remediation="Regenerate or repair the runtime artifact so it matches the Lean selected-grid certificate contract.",
        )
    )
    return finding_id + 1


def lint_envelope_is_artifact(
    *,
    root: Path,
    artifact_path: Path,
    rtol: float,
    base_findings: list[LadonFinding],
) -> list[LadonFinding]:
    findings = list(base_findings)
    next_id = len(findings) + 1
    rel_path = str(artifact_path if artifact_path.is_absolute() else artifact_path)
    data = load_json_artifact(artifact_path)
    if not isinstance(data, dict):
        next_id = add_artifact_gap(
            findings,
            finding_id=next_id,
            path=rel_path,
            title="Certificate artifact is not a JSON object",
            summary="Envelope-IS selected-grid artifacts must be top-level JSON objects.",
            evidence=["route=envelope-is-selected-grid"],
        )
        return findings

    required_global = {
        "target_delta": ["target_delta"],
        "confidence_alpha_total": ["confidence_alpha_total", "global_confidence_alpha_total"],
        "actual_alpha_spent": ["actual_alpha_spent"],
    }
    for label, names in required_global.items():
        if first_present(data, names) is None:
            next_id = add_artifact_gap(
                findings,
                finding_id=next_id,
                path=rel_path,
                title=f"Envelope-IS artifact missing global field: {label}",
                summary=f"The artifact does not expose required global field {label}.",
                evidence=[f"accepted_names={','.join(names)}", "route=envelope-is-selected-grid"],
            )
    spent = as_finite_float(first_present(data, ["actual_alpha_spent"]))
    total = as_finite_float(first_present(data, ["confidence_alpha_total", "global_confidence_alpha_total"]))
    if spent is not None and total is not None and spent > total + max(1e-18, abs(total) * 1e-12):
        next_id = add_artifact_gap(
            findings,
            finding_id=next_id,
            path=rel_path,
            title="Envelope-IS artifact alpha spent exceeds global alpha",
            summary="The artifact reports actual alpha spending larger than the global alpha budget.",
            evidence=[f"actual_alpha_spent={spent}", f"confidence_alpha_total={total}"],
        )

    candidate_like = [
        item
        for item in iter_dicts(data)
        if any(key in item for key in ["candidate_sigma", "candidate_rmse", "sigma_factor", "selected_sigma", "selected_rmse"])
    ]
    for index, item in enumerate(candidate_like):
        candidate_sigma = first_present(item, ["candidate_sigma", "selected_sigma", "sigma"])
        candidate_rmse = first_present(item, ["candidate_rmse", "selected_rmse", "rmse"])
        upper = first_present(item, ["upper_two_sided", "two_sided_upper_bound", "selected_upper_two_sided", "upperTwoSided"])
        if candidate_sigma is None:
            next_id = add_artifact_gap(
                findings,
                finding_id=next_id,
                path=rel_path,
                title=f"Envelope-IS candidate missing candidate sigma at index {index}",
                summary="A candidate-like artifact row lacks candidate sigma.",
                evidence=[f"candidate_index={index}", f"keys={','.join(sorted(item.keys())[:20])}"],
            )
        if candidate_rmse is None:
            next_id = add_artifact_gap(
                findings,
                finding_id=next_id,
                path=rel_path,
                title=f"Envelope-IS candidate missing candidate RMSE at index {index}",
                summary="A candidate-like artifact row lacks candidate-level RMSE.",
                evidence=[f"candidate_index={index}", f"keys={','.join(sorted(item.keys())[:20])}"],
            )
        if upper is None and any(key in item for key in ["certified", "selected", "is_selected", "status"]):
            next_id = add_artifact_gap(
                findings,
                finding_id=next_id,
                path=rel_path,
                title=f"Envelope-IS certified/selected row missing two-sided upper at index {index}",
                summary="A selected or certified row should expose the two-sided upper bound used by the Lean facade.",
                evidence=[f"candidate_index={index}", f"keys={','.join(sorted(item.keys())[:20])}"],
            )
        source_rmse = as_finite_float(first_present(item, ["source_rmse"]))
        source_sigma = as_finite_float(first_present(item, ["source_sigma"]))
        sigma_factor = as_finite_float(first_present(item, ["sigma_factor"]))
        cand_sigma = as_finite_float(candidate_sigma)
        cand_rmse = as_finite_float(candidate_rmse)
        if source_rmse is not None and cand_rmse is not None:
            expected_values: list[tuple[str, float]] = []
            if sigma_factor is not None:
                expected_values.append(("source_rmse*sigma_factor", source_rmse * sigma_factor))
            if source_sigma not in (None, 0.0) and cand_sigma is not None:
                expected_values.append(("source_rmse*candidate_sigma/source_sigma", source_rmse * cand_sigma / source_sigma))
            for label, expected in expected_values:
                if not math.isfinite(expected):
                    continue
                tolerance = max(abs(expected), 1.0) * float(rtol)
                if abs(cand_rmse - expected) > tolerance:
                    next_id = add_artifact_gap(
                        findings,
                        finding_id=next_id,
                        path=rel_path,
                        title=f"Envelope-IS candidate RMSE inconsistent at index {index}",
                        summary="Candidate RMSE is inconsistent with source RMSE and sigma inflation metadata.",
                        evidence=[
                            f"candidate_index={index}",
                            f"check={label}",
                            f"candidate_rmse={cand_rmse}",
                            f"expected_rmse={expected}",
                            f"rtol={rtol}",
                        ],
                    )
                    break
    return findings


def lint_certificate_artifacts(root: Path, args: argparse.Namespace, base_findings: list[LadonFinding]) -> list[LadonFinding]:
    findings = list(base_findings)
    for raw_path in args.certificate_artifact:
        artifact_path = Path(raw_path)
        if not artifact_path.is_absolute():
            artifact_path = root / artifact_path
        if not artifact_path.exists():
            add_artifact_gap(
                findings,
                finding_id=len(findings) + 1,
                path=str(artifact_path),
                title="Certificate artifact path does not exist",
                summary="A requested certificate artifact could not be read.",
                evidence=[f"path={artifact_path}"],
            )
            continue
        route = args.certificate_artifact_route
        if route == "auto":
            route = "envelope-is-selected-grid"
        if route == "envelope-is-selected-grid":
            findings = lint_envelope_is_artifact(
                root=root,
                artifact_path=artifact_path,
                rtol=float(args.certificate_artifact_rmse_rtol),
                base_findings=findings,
            )
    return findings


def summarize_certificate_boundary(findings: list[LadonFinding], export_surface: dict[str, Any]) -> dict[str, Any]:
    boundary_findings = [finding for finding in findings if finding.category in CERTIFICATE_BOUNDARY_CATEGORIES]
    by_category = Counter(finding.category for finding in boundary_findings)
    by_scope = Counter(finding.scope for finding in boundary_findings)
    return {
        "total_findings": len(boundary_findings),
        "by_category": dict(sorted(by_category.items())),
        "by_scope": dict(sorted(by_scope.items())),
        "export_surface_verification": {
            "status": export_surface.get("status", "skipped"),
            "checked_declaration_count": export_surface.get("checked_declaration_count", 0),
            "missing_declaration_count": export_surface.get("missing_declaration_count", 0),
            "missing_declarations": export_surface.get("missing_declarations", []),
        },
        "top_findings": [
            {
                "category": finding.category,
                "title": finding.title,
                "files": finding.files,
                "modules": finding.modules,
                "declarations": finding.declarations,
            }
            for finding in boundary_findings[:10]
        ],
    }


def summarize_decision_hotspots(declaration_metrics: list[DeclarationMetric]) -> dict[str, Any]:
    decls = [
        metric
        for metric in declaration_metrics
        if metric.parser_decision_complexity is not None and (metric.parser_decision_complexity or 0) > 1
    ]
    top_declarations = sorted(
        decls,
        key=lambda metric: (
            metric.parser_decision_complexity or 0,
            metric.parser_decision_nesting_complexity or 0,
            metric.full_name,
        ),
        reverse=True,
    )[:10]
    file_scores: Counter[str] = Counter()
    for metric in decls:
        file_scores[metric.path] += (metric.parser_decision_complexity or 1) - 1
    top_files = file_scores.most_common(10)
    rank_counts = Counter(metric.parser_decision_rank for metric in decls if metric.parser_decision_rank)
    return {
        "scope": "analysis_closure",
        "top_declarations": [
            {
                "scope": "analysis_closure",
                "full_name": metric.full_name,
                "path": metric.path,
                "line": metric.line,
                "kind": metric.kind,
                "decision_complexity": metric.parser_decision_complexity,
                "nesting_complexity": metric.parser_decision_nesting_complexity,
                "rank": metric.parser_decision_rank,
            }
            for metric in top_declarations
        ],
        "top_files": [
            {"scope": "analysis_closure", "path": path, "decision_complexity_sum": score}
            for path, score in top_files
        ],
        "rank_counts": dict(sorted(rank_counts.items())),
    }


def summarize_reference_graph(declaration_graph: dict[str, Any]) -> dict[str, Any]:
    candidate_count = declaration_graph["candidate_count"]
    resolved_candidate_count = declaration_graph["resolved_candidate_count"]
    resolution_ratio = (
        resolved_candidate_count / candidate_count
        if candidate_count
        else 1.0
    )
    return {
        "scope": "analysis_closure",
        "provenance": declaration_graph["provenance"],
        "candidate_count": candidate_count,
        "resolved_edge_count": declaration_graph["resolved_edge_count"],
        "resolved_candidate_count": resolved_candidate_count,
        "unresolved_candidate_count": declaration_graph["unresolved_candidate_count"],
        "resolution_ratio": round(resolution_ratio, 4),
        "confidence_limiter": resolution_ratio < REFERENCE_GRAPH_RESOLUTION_WARN_RATIO,
    }


def summarize_module_dag(
    modules: dict[str, audit.ModuleInfo],
    resolved_roots: Sequence[str],
    analysis_root_module: str,
) -> dict[str, Any]:
    module_names = sorted(modules)
    edges: dict[str, list[str]] = {
        module: sorted(imported for imported in info.imports if imported in modules)
        for module, info in modules.items()
    }
    reverse_edges: dict[str, list[str]] = {module: [] for module in module_names}
    for source, targets in edges.items():
        for target in targets:
            reverse_edges[target].append(source)
    for targets in reverse_edges.values():
        targets.sort()

    components = tarjan_scc(module_names, edges)
    cyclic_components = [
        component
        for component in components
        if len(component) > 1 or any(module in edges.get(module, []) for module in component)
    ]
    cyclic_components.sort(key=lambda component: (len(component), component[0]), reverse=True)

    indegree = {module: 0 for module in module_names}
    for targets in edges.values():
        for target in targets:
            indegree[target] += 1
    queue: deque[str] = deque(sorted(module for module, count in indegree.items() if count == 0))
    indegree_work = dict(indegree)
    topo: list[str] = []
    while queue:
        module = queue.popleft()
        topo.append(module)
        for target in edges.get(module, []):
            indegree_work[target] -= 1
            if indegree_work[target] == 0:
                queue.append(target)
    acyclic = len(topo) == len(module_names)
    ranks: dict[str, int] = {}
    if acyclic:
        for module in topo:
            rank = ranks.setdefault(module, 0)
            for target in edges.get(module, []):
                ranks[target] = max(ranks.get(target, 0), rank + 1)
    layer_names: dict[int, list[str]] = defaultdict(list)
    for module, rank in ranks.items():
        layer_names[rank].append(module)
    for names in layer_names.values():
        names.sort()
    layer_widths = [
        {"rank": rank, "width": len(names), "sample_modules": names[:12]}
        for rank, names in sorted(layer_names.items())
    ]
    widest_layers = sorted(layer_widths, key=lambda item: (item["width"], -item["rank"]), reverse=True)[:10]
    chosen_roots = sorted(module for module in (set(resolved_roots) or {analysis_root_module}) if module in modules)
    reachable = reachable_modules(modules, chosen_roots)
    not_reachable = sorted(module for module in modules if module not in reachable)
    root_like_modules = sorted(module for module in module_names if not reverse_edges.get(module))
    facade_modules = sorted(
        module
        for module, info in modules.items()
        if info.imports and not info.declarations
    )
    return {
        "scope": "repo_inventory",
        "method": "repo_wide_module_import_dag",
        "module_count": len(module_names),
        "edge_count": sum(len(targets) for targets in edges.values()),
        "acyclic": acyclic,
        "scc_count": len(components),
        "cyclic_component_count": len(cyclic_components),
        "largest_cyclic_component_size": len(cyclic_components[0]) if cyclic_components else 0,
        "top_cyclic_components": [
            {"size": len(component), "sample_modules": component[:12]}
            for component in cyclic_components[:10]
        ],
        "max_rank": max(ranks.values(), default=0),
        "topological_layer_count": len(layer_widths),
        "layer_widths": layer_widths[:80],
        "widest_layers": widest_layers,
        "top_fan_in": [
            {
                "module": module,
                "path": modules[module].path,
                "fan_in": len(reverse_edges.get(module, [])),
                "sample_importers": reverse_edges.get(module, [])[:12],
            }
            for module in sorted(
                module_names,
                key=lambda item: (len(reverse_edges.get(item, [])), item),
                reverse=True,
            )[:15]
        ],
        "top_fan_out": [
            {
                "module": module,
                "path": modules[module].path,
                "fan_out": len(edges.get(module, [])),
                "sample_imports": edges.get(module, [])[:12],
            }
            for module in sorted(
                module_names,
                key=lambda item: (len(edges.get(item, [])), item),
                reverse=True,
            )[:15]
        ],
        "root_like_modules": root_like_modules[:20],
        "root_like_module_count": len(root_like_modules),
        "facade_modules": facade_modules[:20],
        "facade_module_count": len(facade_modules),
        "chosen_roots": chosen_roots,
        "source_modules_not_reachable_from_chosen_roots": not_reachable[:50],
        "source_modules_not_reachable_from_chosen_roots_count": len(not_reachable),
        "edges": edges,
    }


def tarjan_scc(nodes: Sequence[str], edges: dict[str, list[str]]) -> list[list[str]]:
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indexes: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    components: list[list[str]] = []

    def strongconnect(node: str) -> None:
        nonlocal index
        indexes[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for target in edges.get(node, []):
            if target not in indexes:
                strongconnect(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indexes[target])

        if lowlinks[node] != indexes[node]:
            return
        component: list[str] = []
        while True:
            target = stack.pop()
            on_stack.remove(target)
            component.append(target)
            if target == node:
                break
        components.append(sorted(component))

    for node in sorted(nodes):
        if node not in indexes:
            strongconnect(node)
    return components


def summarize_graph_reasoning(
    *,
    declaration_metrics: list[DeclarationMetric],
    declaration_graph: dict[str, Any],
    root_modules: Sequence[str],
    analysis_root_module: str,
) -> dict[str, Any]:
    metrics_by_name = {metric.full_name: metric for metric in declaration_metrics}
    edges: dict[str, list[str]] = {
        name: [target for target in targets if target in metrics_by_name]
        for name, targets in declaration_graph.get("edges", {}).items()
        if name in metrics_by_name
    }
    for name in metrics_by_name:
        edges.setdefault(name, [])
    reverse_edges: dict[str, list[str]] = {
        name: [source for source in sources if source in metrics_by_name]
        for name, sources in declaration_graph.get("reverse_edges", {}).items()
        if name in metrics_by_name
    }
    for name in metrics_by_name:
        reverse_edges.setdefault(name, [])

    active_roots = set(root_modules) or {analysis_root_module}
    root_declarations = sorted(
        metric.full_name
        for metric in declaration_metrics
        if metric.module in active_roots or metric.module == analysis_root_module
    )
    distances: dict[str, int] = {}
    queue: deque[str] = deque()
    for name in root_declarations:
        distances[name] = 0
        queue.append(name)
    while queue:
        source = queue.popleft()
        next_distance = distances[source] + 1
        for target in edges.get(source, []):
            if target in distances:
                continue
            distances[target] = next_distance
            queue.append(target)

    reachable_names = set(distances)
    rank_counts = Counter(distances.values())
    components = tarjan_scc(sorted(metrics_by_name), edges)
    cyclic_components = [
        component
        for component in components
        if len(component) > 1 or any(name in edges.get(name, []) for name in component)
    ]
    cyclic_components.sort(key=lambda component: (len(component), component[0]), reverse=True)

    frontier = [
        name
        for name in reachable_names
        if not [target for target in edges.get(name, []) if target in reachable_names]
    ]
    frontier.sort(key=lambda name: (distances.get(name, 0), name), reverse=True)

    kernel_candidates: list[dict[str, Any]] = []
    for name in reachable_names:
        metric = metrics_by_name[name]
        reachable_consumers = [source for source in reverse_edges.get(name, []) if source in reachable_names]
        dependencies = [target for target in edges.get(name, []) if target in reachable_names]
        if not reachable_consumers:
            continue
        score = len(reachable_consumers) * 3 + max(0, 4 - len(dependencies)) + (1 if metric.kind in {"theorem", "lemma"} else 0)
        kernel_candidates.append(
            {
                "full_name": name,
                "module": metric.module,
                "kind": metric.kind,
                "depth_from_root": distances.get(name),
                "reachable_consumer_count": len(reachable_consumers),
                "reachable_dependency_count": len(dependencies),
                "reference_graph_in_degree": metric.reference_graph_in_degree,
                "reference_graph_out_degree": metric.reference_graph_out_degree,
                "score": score,
            }
        )
    kernel_candidates.sort(
        key=lambda item: (
            item["score"],
            item["reachable_consumer_count"],
            -item["reachable_dependency_count"],
            item["full_name"],
        ),
        reverse=True,
    )

    module_flows: Counter[tuple[str, str]] = Counter()
    for source, targets in edges.items():
        if source not in reachable_names:
            continue
        source_module = metrics_by_name[source].module
        for target in targets:
            if target not in reachable_names:
                continue
            target_module = metrics_by_name[target].module
            if source_module != target_module:
                module_flows[(source_module, target_module)] += 1
    top_module_flows = [
        {"source_module": source, "target_module": target, "edge_count": count}
        for (source, target), count in module_flows.most_common(10)
    ]

    top_cyclic_components = []
    for component in cyclic_components[:10]:
        modules = sorted({metrics_by_name[name].module for name in component})
        top_cyclic_components.append(
            {
                "size": len(component),
                "modules": modules,
                "sample_declarations": component[:12],
            }
        )

    ranked_dag_status = "available" if not cyclic_components and root_declarations else "requires_scc_condensation"
    if not root_declarations:
        ranked_dag_status = "unavailable_no_roots"
    dag_shape = summarize_dag_shape(
        metrics_by_name=metrics_by_name,
        edges=edges,
        reverse_edges=reverse_edges,
        root_declarations=root_declarations,
        reachable_names=reachable_names,
        cyclic_components=cyclic_components,
    )
    return {
        "scope": "analysis_closure",
        "method": "declaration_reference_graph_reasoning",
        "inspiration": [
            "Quux.Semantics.Propagation reachability fold",
            "Quux.Semantics.Recurrence ranked DAG law",
            "Quux proof-compression semantic-skeleton doctrine",
        ],
        "root_modules": sorted(active_roots),
        "root_declaration_count": len(root_declarations),
        "sample_root_declarations": root_declarations[:12],
        "reachable_declaration_count": len(reachable_names),
        "unreachable_declaration_count": max(0, len(metrics_by_name) - len(reachable_names)),
        "max_dependency_depth_from_root": max(distances.values(), default=0),
        "rank_counts": {str(rank): count for rank, count in sorted(rank_counts.items())},
        "frontier_leaf_count": len(frontier),
        "sample_frontier_leaves": frontier[:12],
        "scc_count": len(components),
        "cyclic_component_count": len(cyclic_components),
        "largest_cyclic_component_size": len(cyclic_components[0]) if cyclic_components else 0,
        "top_cyclic_components": top_cyclic_components,
        "ranked_dag_status": ranked_dag_status,
        "dag_shape": dag_shape,
        "semiring_reachability_status": "available" if root_declarations else "unavailable_no_roots",
        "cycle_decomposition_status": "needed" if cyclic_components else "not_needed",
        "kernel_candidate_count": len(kernel_candidates),
        "top_kernel_candidates": kernel_candidates[:10],
        "top_module_dependency_flows": top_module_flows,
    }


def summarize_dag_shape(
    *,
    metrics_by_name: dict[str, DeclarationMetric],
    edges: dict[str, list[str]],
    reverse_edges: dict[str, list[str]],
    root_declarations: Sequence[str],
    reachable_names: set[str],
    cyclic_components: list[list[str]],
) -> dict[str, Any]:
    if not root_declarations:
        return {"status": "unavailable_no_roots"}
    if cyclic_components:
        return {
            "status": "requires_scc_condensation",
            "cyclic_component_count": len(cyclic_components),
        }
    if not reachable_names:
        return {"status": "unavailable_empty_graph"}

    root_set = set(root_declarations)
    entrypoint_roots = sorted(
        name
        for name in root_declarations
        if not [source for source in reverse_edges.get(name, []) if source in root_set]
    )
    if not entrypoint_roots:
        entrypoint_roots = sorted(root_declarations)
    shape_reachable_names = reachable_from_entrypoints(
        entrypoint_roots=entrypoint_roots,
        edges=edges,
        allowed_names=reachable_names,
    )

    reachable_edges = [
        (source, target)
        for source in sorted(shape_reachable_names)
        for target in edges.get(source, [])
        if target in shape_reachable_names
    ]
    indegree = {name: 0 for name in shape_reachable_names}
    for _source, target in reachable_edges:
        indegree[target] += 1
    queue: deque[str] = deque(sorted(name for name, count in indegree.items() if count == 0))
    topological_order: list[str] = []
    indegree_work = dict(indegree)
    while queue:
        node = queue.popleft()
        topological_order.append(node)
        for target in sorted(target for target in edges.get(node, []) if target in shape_reachable_names):
            indegree_work[target] -= 1
            if indegree_work[target] == 0:
                queue.append(target)
    if len(topological_order) != len(shape_reachable_names):
        return {
            "status": "requires_scc_condensation",
            "topologically_sorted_count": len(topological_order),
            "reachable_declaration_count": len(shape_reachable_names),
        }

    entrypoint_root_set = set(entrypoint_roots)
    ranks = {name: 0 for name in shape_reachable_names if name in entrypoint_root_set or indegree[name] == 0}
    for node in topological_order:
        rank = ranks.setdefault(node, 0)
        for target in sorted(target for target in edges.get(node, []) if target in shape_reachable_names):
            ranks[target] = max(ranks.get(target, 0), rank + 1)

    layer_names: dict[int, list[str]] = defaultdict(list)
    for name, rank in ranks.items():
        layer_names[rank].append(name)
    for names in layer_names.values():
        names.sort()
    layer_widths = [
        {
            "rank": rank,
            "width": len(names),
            "sample_declarations": names[:8],
            "sample_modules": sorted({metrics_by_name[name].module for name in names})[:8],
        }
        for rank, names in sorted(layer_names.items())
    ]
    widest_layers = sorted(layer_widths, key=lambda item: (item["width"], -item["rank"]), reverse=True)[:5]
    max_rank = max(layer_names, default=0)
    bottleneck_layers: list[dict[str, Any]] = []
    for item in layer_widths:
        rank = item["rank"]
        width = item["width"]
        if rank == 0 or rank == max_rank or width == 0:
            continue
        prev_width = len(layer_names.get(rank - 1, []))
        next_width = len(layer_names.get(rank + 1, []))
        if width <= 2 and (prev_width >= 2 * width or next_width >= 2 * width):
            bottleneck_layers.append(
                {
                    **item,
                    "previous_width": prev_width,
                    "next_width": next_width,
                }
            )

    edge_direction_counts = Counter()
    for source, target in reachable_edges:
        if ranks[target] > ranks[source]:
            edge_direction_counts["forward"] += 1
        elif ranks[target] == ranks[source]:
            edge_direction_counts["same_rank"] += 1
        else:
            edge_direction_counts["backward"] += 1
    edge_direction_status = (
        "strictly_layered"
        if not edge_direction_counts["same_rank"] and not edge_direction_counts["backward"]
        else "has_cross_or_backward_edges"
    )
    frontier = sorted(
        [
            name
            for name in shape_reachable_names
            if not [target for target in edges.get(name, []) if target in shape_reachable_names]
        ],
        key=lambda name: (ranks.get(name, 0), name),
        reverse=True,
    )
    path_samples = [
        {
            "leaf": leaf,
            "rank": ranks.get(leaf, 0),
            "path": reconstruct_ranked_path_to_leaf(
                leaf=leaf,
                ranks=ranks,
                reverse_edges=reverse_edges,
                reachable_names=shape_reachable_names,
            ),
        }
        for leaf in frontier[:5]
    ]

    return {
        "status": "available",
        "entrypoint_declaration_count": len(entrypoint_roots),
        "sample_entrypoint_declarations": entrypoint_roots[:12],
        "shape_reachable_declaration_count": len(shape_reachable_names),
        "topological_layer_count": len(layer_widths),
        "max_rank": max_rank,
        "layer_widths": layer_widths[:40],
        "widest_layers": widest_layers,
        "bottleneck_layers": bottleneck_layers[:10],
        "edge_direction_status": edge_direction_status,
        "edge_direction_counts": dict(sorted(edge_direction_counts.items())),
        "root_to_frontier_path_samples": path_samples,
    }


def reachable_from_entrypoints(
    *,
    entrypoint_roots: Sequence[str],
    edges: dict[str, list[str]],
    allowed_names: set[str],
) -> set[str]:
    reached: set[str] = set()
    queue: deque[str] = deque(name for name in entrypoint_roots if name in allowed_names)
    while queue:
        node = queue.popleft()
        if node in reached:
            continue
        reached.add(node)
        for target in edges.get(node, []):
            if target in allowed_names and target not in reached:
                queue.append(target)
    return reached


def reconstruct_ranked_path_to_leaf(
    *,
    leaf: str,
    ranks: dict[str, int],
    reverse_edges: dict[str, list[str]],
    reachable_names: set[str],
) -> list[str]:
    path = [leaf]
    current = leaf
    seen = {leaf}
    while ranks.get(current, 0) > 0:
        current_rank = ranks[current]
        predecessors = [
            source
            for source in reverse_edges.get(current, [])
            if source in reachable_names and ranks.get(source, -1) < current_rank and source not in seen
        ]
        if not predecessors:
            break
        predecessors.sort(
            key=lambda source: (
                ranks.get(source, 0),
                len([consumer for consumer in reverse_edges.get(source, []) if consumer in reachable_names]),
                source,
            ),
            reverse=True,
        )
        current = predecessors[0]
        path.append(current)
        seen.add(current)
    path.reverse()
    return path


def summarize_fragility_hotspots(declaration_metrics: list[DeclarationMetric]) -> dict[str, Any]:
    hotspots = [metric for metric in declaration_metrics if is_fragility_hotspot(metric)]
    hotspots.sort(
        key=lambda metric: (
            metric.fragility_calibrated_score,
            metric.fragility_signal_family_count,
            metric.fragility_score,
            metric.fragility_rw_count,
            metric.fragility_have_count,
            metric.fragility_calc_step_count,
            metric.full_name,
        ),
        reverse=True,
    )
    return {
        "scope": "analysis_closure",
        "top_declarations": [
            {
                "scope": "analysis_closure",
                "full_name": metric.full_name,
                "path": metric.path,
                "line": metric.line,
                "kind": metric.kind,
                "fragility_score": metric.fragility_score,
                "fragility_calibrated_score": metric.fragility_calibrated_score,
                "fragility_signal_family_count": metric.fragility_signal_family_count,
                "fragility_calibrated_band": metric.fragility_calibrated_band,
                "simp_like_count": metric.fragility_simp_like_count,
                "broad_simp_sites": metric.fragility_broad_simp_sites,
                "rw_count": metric.fragility_rw_count,
                "by_cases_count": metric.fragility_by_cases_count,
                "calc_step_count": metric.fragility_calc_step_count,
                "have_count": metric.fragility_have_count,
            }
            for metric in hotspots[:10]
        ],
    }


def list_preview(items: Sequence[str], *, limit: int = 12) -> str:
    if not items:
        return "<none>"
    shown = list(items[:limit])
    suffix = "" if len(items) <= limit else f", ... (+{len(items) - limit} more)"
    return ", ".join(shown) + suffix


def direct_import_closure_impacts(
    *,
    extraction: ExtractionResult,
    modules: dict[str, audit.ModuleInfo],
    declaration_metrics: list[DeclarationMetric],
) -> dict[str, Any]:
    root_info = modules.get(extraction.analysis_root_module)
    if root_info is None:
        return {"scope": "analysis_closure", "root_module": extraction.analysis_root_module, "top_imports": []}
    declaration_counts = Counter(metric.module for metric in declaration_metrics)
    impacts: list[dict[str, Any]] = []
    for imported in sorted(root_info.imports):
        if imported not in modules:
            impacts.append(
                {
                    "import": imported,
                    "in_analysis_closure": False,
                    "module_count": 0,
                    "declaration_count": 0,
                    "sample_modules": [],
                }
            )
            continue
        closure = sorted(reachable_modules(modules, [imported]))
        impacts.append(
            {
                "import": imported,
                "in_analysis_closure": True,
                "module_count": len(closure),
                "declaration_count": sum(declaration_counts[module] for module in closure),
                "sample_modules": closure[:10],
            }
        )
    impacts.sort(key=lambda item: (item["module_count"], item["declaration_count"], item["import"]), reverse=True)
    return {
        "scope": "analysis_closure",
        "root_module": extraction.analysis_root_module,
        "direct_import_count": len(root_info.imports),
        "top_imports": impacts,
    }


def read_existing_docs(root: Path, doc_files: Sequence[str]) -> dict[str, str]:
    texts: dict[str, str] = {}
    for doc in doc_files:
        path = root / doc
        if not path.exists():
            continue
        try:
            texts[doc] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            texts[doc] = ""
    return texts


def summarize_doc_coverage(
    *,
    root: Path,
    doc_files: Sequence[str],
    extraction: ExtractionResult,
    declaration_metrics: list[DeclarationMetric],
) -> dict[str, Any]:
    existing_texts = read_existing_docs(root, doc_files)
    missing_docs = [doc for doc in doc_files if doc not in existing_texts]
    root_decls = [metric for metric in declaration_metrics if metric.module == extraction.analysis_root_module]
    combined = "\n".join(existing_texts.values())
    mentioned_decls = [
        metric.full_name
        for metric in root_decls
        if metric.full_name in combined or metric.name in combined
    ]
    root_path_mentioned = extraction.analysis_root_file in combined
    root_basename = Path(extraction.analysis_root_file).stem
    root_basename_mentioned = root_basename in combined or extraction.analysis_root_module in combined
    if not doc_files:
        status = "unavailable"
    elif existing_texts:
        status = "audited"
    else:
        status = "all_docs_missing"
    return {
        "status": status,
        "requested_doc_count": len(doc_files),
        "existing_doc_count": len(existing_texts),
        "missing_docs": missing_docs,
        "existing_docs": sorted(existing_texts),
        "root_module": extraction.analysis_root_module,
        "root_path": extraction.analysis_root_file,
        "root_path_mentioned": root_path_mentioned,
        "root_module_or_basename_mentioned": root_basename_mentioned,
        "root_declaration_count": len(root_decls),
        "mentioned_root_declaration_count": len(mentioned_decls),
        "undocumented_root_declaration_count": max(0, len(root_decls) - len(mentioned_decls)),
        "sample_mentioned_root_declarations": mentioned_decls[:10],
        "sample_undocumented_root_declarations": [
            metric.full_name for metric in root_decls if metric.full_name not in set(mentioned_decls)
        ][:10],
    }


def summarize_witness_audit(
    *,
    root: Path,
    doc_files: Sequence[str],
    extraction: ExtractionResult,
) -> dict[str, Any]:
    existing_texts = read_existing_docs(root, doc_files)
    mentioned_paths = sorted(
        {
            match.group(0).rstrip(".,);]")
            for text in existing_texts.values()
            for match in WITNESS_PATH_RE.finditer(text)
        }
    )
    witness_root = root / "witnesses"
    witness_dirs: list[dict[str, Any]] = []
    if witness_root.exists():
        for child in sorted(path for path in witness_root.iterdir() if path.is_dir()):
            rel = repo_relative_path(root, child)
            artifact_count = len(list((child / "artifacts").glob("*.json"))) if (child / "artifacts").exists() else 0
            witness_dirs.append(
                {
                    "path": rel,
                    "checker_exists": (child / "check.py").exists(),
                    "artifact_count": artifact_count,
                    "mentioned_in_docs": any(path == rel or path.startswith(f"{rel}/") for path in mentioned_paths),
                }
            )
    root_tokens = set(normalized_name_tokens(extraction.analysis_root_module))
    root_tokens.update(normalized_name_tokens(extraction.analysis_root_file))
    likely_dirs = []
    for item in witness_dirs:
        dir_tokens = set(normalized_name_tokens(item["path"]))
        overlap = sorted(root_tokens & dir_tokens)
        if overlap:
            likely_dirs.append({**item, "matched_tokens": overlap})
    likely_dirs.sort(key=lambda item: (len(item["matched_tokens"]), item["artifact_count"], item["path"]), reverse=True)
    status = "audited" if witness_root.exists() else "unavailable"
    return {
        "status": status,
        "witness_root_exists": witness_root.exists(),
        "doc_mentioned_witness_paths": mentioned_paths,
        "doc_mentioned_witness_path_count": len(mentioned_paths),
        "witness_dir_count": len(witness_dirs),
        "witness_dirs": witness_dirs[:20],
        "likely_related_witness_dirs": likely_dirs[:10],
    }


def git_workspace_summary(root: Path) -> dict[str, Any]:
    head_proc = run_git_command(root, ["rev-parse", "HEAD"])
    top_proc = run_git_command(root, ["rev-parse", "--show-toplevel"])
    status_proc = run_git_command(
        root,
        ["status", "--porcelain=v1", "--untracked-files=all", "--", "."],
    )
    if head_proc.returncode != 0 or top_proc.returncode != 0 or status_proc.returncode != 0:
        return {
            "status": "unavailable",
            "head_sha": None,
            "is_dirty": None,
            "tracked_change_count": None,
            "untracked_count": None,
            "sample_status_entries": [],
        }
    git_top = Path(top_proc.stdout.strip()).resolve()
    if git_top != root.resolve():
        return {
            "status": "unavailable_subdirectory_repo_root",
            "head_sha": head_proc.stdout.strip(),
            "is_dirty": None,
            "tracked_change_count": None,
            "untracked_count": None,
            "sample_status_entries": [],
            "git_toplevel": str(git_top),
        }
    entries = [line for line in status_proc.stdout.splitlines() if line.strip()]
    tracked = [line for line in entries if not line.startswith("??")]
    untracked = [line for line in entries if line.startswith("??")]
    return {
        "status": "available",
        "head_sha": head_proc.stdout.strip(),
        "is_dirty": bool(entries),
        "tracked_change_count": len(tracked),
        "untracked_count": len(untracked),
        "sample_status_entries": entries[:80],
    }


def proof_hole_scan(root: Path, inventory: InventorySelection) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    for rel_path in inventory.files:
        text = (root / rel_path).read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            for match in PROOF_HOLE_RE.finditer(line):
                hits.append(
                    {
                        "path": rel_path,
                        "line": line_no,
                        "token": match.group(0),
                        "snippet": stripped[:200],
                    }
                )
    by_token = Counter(hit["token"] for hit in hits)
    return {
        "scope": "repo_inventory",
        "scanned_file_count": len(inventory.files),
        "hole_count": len(hits),
        "by_token": dict(sorted(by_token.items())),
        "clean": not hits,
        "sample_hits": hits[:50],
    }


def openspec_backlog_summary(root: Path) -> dict[str, Any]:
    changes_root = root / "openspec" / "changes"
    if not changes_root.exists():
        return {"status": "unavailable", "active_change_count": 0}
    active_changes: list[dict[str, Any]] = []
    total_task_files = 0
    unchecked_total = 0
    checked_total = 0
    for change_dir in sorted(path for path in changes_root.iterdir() if path.is_dir()):
        if change_dir.name == "archive":
            continue
        task_files = sorted(change_dir.rglob("tasks.md"))
        if not task_files:
            continue
        change_unchecked = 0
        change_checked = 0
        for task_file in task_files:
            total_task_files += 1
            for line in task_file.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("- [ ]"):
                    unchecked_total += 1
                    change_unchecked += 1
                elif stripped.startswith("- [x]") or stripped.startswith("- [X]"):
                    checked_total += 1
                    change_checked += 1
        if change_unchecked or change_checked:
            active_changes.append(
                {
                    "change": change_dir.name,
                    "task_file_count": len(task_files),
                    "checked_task_count": change_checked,
                    "unchecked_task_count": change_unchecked,
                }
            )
    active_changes.sort(
        key=lambda item: (item["unchecked_task_count"], item["task_file_count"], item["change"]),
        reverse=True,
    )
    return {
        "status": "available",
        "active_change_count": len(active_changes),
        "task_file_count": total_task_files,
        "checked_task_count": checked_total,
        "unchecked_task_count": unchecked_total,
        "unchecked_change_count": sum(
            1 for change in active_changes if change["unchecked_task_count"] > 0
        ),
        "top_unchecked_changes": active_changes[:20],
    }


def local_scripts_inventory(root: Path) -> dict[str, Any]:
    scripts_root = root / "local-scripts"
    if not scripts_root.exists():
        return {"status": "unavailable", "script_count": 0}
    scripts: list[dict[str, Any]] = []
    for path in sorted(scripts_root.glob("*.py")):
        rel = repo_relative_path(root, path)
        text = path.read_text(encoding="utf-8")
        artifact_mentions = sorted(set(re.findall(r"data/runtime/[A-Za-z0-9_./-]+\\.(?:json|csv)", text)))
        doc_mentions = sorted(set(re.findall(r"docs/[A-Za-z0-9_./-]+\\.md", text)))
        openspec_mentions = sorted(set(re.findall(r"openspec/changes/[A-Za-z0-9_./-]+", text)))
        scripts.append(
            {
                "path": rel,
                "is_diagnostic_like": bool(LOCAL_SCRIPT_RE.search(path.name)),
                "artifact_mentions": artifact_mentions[:20],
                "artifact_mention_count": len(artifact_mentions),
                "doc_mentions": doc_mentions[:20],
                "doc_mention_count": len(doc_mentions),
                "openspec_mentions": openspec_mentions[:20],
                "openspec_mention_count": len(openspec_mentions),
            }
        )
    diagnostic_like = [script for script in scripts if script["is_diagnostic_like"]]
    without_artifacts = [
        script for script in diagnostic_like if script["artifact_mention_count"] == 0
    ]
    return {
        "status": "available",
        "script_count": len(scripts),
        "diagnostic_like_script_count": len(diagnostic_like),
        "diagnostic_like_without_runtime_artifact_mentions": len(without_artifacts),
        "top_diagnostic_like_scripts": diagnostic_like[:50],
        "diagnostic_like_without_runtime_artifact_sample": without_artifacts[:25],
    }


def add_repo_context_findings(
    base_findings: list[LadonFinding],
    *,
    extraction: ExtractionResult,
    root_declarations: dict[str, Any],
    direct_import_impacts: dict[str, Any],
    reference_graph_summary: dict[str, Any],
    build_mode: str,
    export_surface: dict[str, Any],
    git_summary: dict[str, Any],
    openspec_summary: dict[str, Any],
    script_summary: dict[str, Any],
) -> list[LadonFinding]:
    findings = list(base_findings)
    next_id = len(findings) + 1
    if (
        root_declarations.get("root_declaration_count", 0) == 0
        and direct_import_impacts.get("direct_import_count", 0) > 0
    ):
        findings.append(
            LadonFinding(
                id=f"L{next_id:04d}",
                category="facade_root_without_declarations",
                severity="warn",
                confidence="deterministic",
                title=f"Analysis root is an import facade: {extraction.analysis_root_module}",
                summary=(
                    f"{extraction.analysis_root_module} has no declarations but imports "
                    f"{direct_import_impacts.get('direct_import_count', 0)} modules. "
                    "Declaration-level DAG shape is therefore unavailable from this root."
                ),
                files=[extraction.analysis_root_file],
                modules=[extraction.analysis_root_module],
                declarations=[],
                scope="root_focus",
                evidence=[
                    f"root_declaration_count={root_declarations.get('root_declaration_count', 0)}",
                    f"direct_import_count={direct_import_impacts.get('direct_import_count', 0)}",
                    "recommended_action=use repo_inventory.module_dag or rerun on owner roots",
                ],
                remediation=(
                    "Treat this as a facade/import root. Review `summary.repo_inventory.module_dag` "
                    "for repo-wide structure, or rerun Ladon on declaration-owning roots."
                ),
            )
        )
        next_id += 1
    if reference_graph_summary.get("confidence_limiter", False):
        findings.append(
            LadonFinding(
                id=f"L{next_id:04d}",
                category="low_reference_graph_resolution",
                severity="warn",
                confidence="deterministic",
                title="Declaration reference graph has low resolution",
                summary=(
                    "Ladon resolved too few parser reference candidates for strong declaration-level "
                    "reachability claims."
                ),
                files=[],
                modules=[],
                declarations=[],
                scope="analysis_closure",
                evidence=[
                    f"candidate_count={reference_graph_summary.get('candidate_count', 0)}",
                    f"resolved_candidate_count={reference_graph_summary.get('resolved_candidate_count', 0)}",
                    f"unresolved_candidate_count={reference_graph_summary.get('unresolved_candidate_count', 0)}",
                    f"resolution_ratio={reference_graph_summary.get('resolution_ratio', 0.0)}",
                ],
                remediation=(
                    "Use declaration-level deadness and DAG reasoning as limited-confidence evidence "
                    "until reference resolution improves."
                ),
            )
        )
        next_id += 1
    if build_mode == "skipped" or export_surface.get("status") == "skipped":
        findings.append(
            LadonFinding(
                id=f"L{next_id:04d}",
                category="incomplete_evidence_due_to_skipped_checks",
                severity="warn",
                confidence="deterministic",
                title="Build or export-surface checks were skipped",
                summary=(
                    "This report is incomplete evidence because build warnings or export-surface "
                    "freshness checks were not run."
                ),
                files=[],
                modules=[],
                declarations=[],
                scope="repo_inventory",
                evidence=[
                    f"build_mode={build_mode}",
                    f"export_surface_status={export_surface.get('status')}",
                ],
                remediation="Rerun without `--skip-build` and with `--verify-export-surface` for stronger evidence.",
            )
        )
        next_id += 1
    if git_summary.get("is_dirty"):
        findings.append(
            LadonFinding(
                id=f"L{next_id:04d}",
                category="dirty_workspace_report",
                severity="info",
                confidence="deterministic",
                title="Ladon report was generated from a dirty workspace",
                summary="Saved reports may be hard to reproduce without the dirty/untracked worktree state.",
                files=[],
                modules=[],
                declarations=[],
                scope="repo_inventory",
                evidence=[
                    f"head_sha={git_summary.get('head_sha')}",
                    f"tracked_change_count={git_summary.get('tracked_change_count')}",
                    f"untracked_count={git_summary.get('untracked_count')}",
                ],
                remediation="Record or commit the relevant changes before treating the report as reproducible evidence.",
            )
        )
        next_id += 1
    if openspec_summary.get("unchecked_task_count", 0) > 0:
        findings.append(
            LadonFinding(
                id=f"L{next_id:04d}",
                category="openspec_backlog_state",
                severity="review",
                confidence="deterministic",
                title="OpenSpec active backlog has unchecked tasks",
                summary=(
                    f"OpenSpec has {openspec_summary.get('unchecked_task_count', 0)} unchecked "
                    f"tasks across {openspec_summary.get('unchecked_change_count', 0)} active changes."
                ),
                files=["openspec/changes"],
                modules=[],
                declarations=[],
                scope="repo_inventory",
                evidence=[
                    f"active_change_count={openspec_summary.get('active_change_count', 0)}",
                    f"task_file_count={openspec_summary.get('task_file_count', 0)}",
                    f"unchecked_change_count={openspec_summary.get('unchecked_change_count', 0)}",
                    f"unchecked_task_count={openspec_summary.get('unchecked_task_count', 0)}",
                ],
                remediation="Prioritize unchecked packets that intersect current code hotspots or theorem-frontier modules.",
            )
        )
        next_id += 1
    if script_summary.get("diagnostic_like_script_count", 0) > script_summary.get("script_count", 0) // 3:
        findings.append(
            LadonFinding(
                id=f"L{next_id:04d}",
                category="local_script_provenance_surface",
                severity="review",
                confidence="heuristic",
                title="Large diagnostic local-script surface needs provenance review",
                summary=(
                    f"local-scripts contains {script_summary.get('diagnostic_like_script_count', 0)} "
                    "diagnostic/check/certify-like scripts."
                ),
                files=["local-scripts"],
                modules=[],
                declarations=[],
                scope="repo_inventory",
                evidence=[
                    f"script_count={script_summary.get('script_count', 0)}",
                    f"diagnostic_like_script_count={script_summary.get('diagnostic_like_script_count', 0)}",
                    "recommended_graph=script-to-runtime-artifact-to-doc-to-OpenSpec/Lean",
                ],
                remediation=(
                    "Add or inspect a script-to-artifact provenance graph before relying on local-script "
                    "coverage as theorem evidence."
                ),
            )
        )
        next_id += 1
    return findings


def proof_shape_signature(metric: DeclarationMetric) -> tuple[Any, ...]:
    def bucket(value: int | None, size: int) -> int:
        return int((value or 0) // size)

    return (
        metric.kind,
        bucket(metric.line_span, 8),
        bucket(metric.fragility_rw_count, 2),
        bucket(metric.fragility_have_count, 3),
        bucket(metric.fragility_calc_step_count, 4),
        bucket(metric.fragility_simp_like_count, 3),
        metric.fragility_by_cases_count > 0,
        metric.body_uses_calc,
        metric.body_uses_have,
        metric.parser_decision_rank,
    )


def summarize_root_proof_skeleton_families(
    *,
    extraction: ExtractionResult,
    declaration_metrics: list[DeclarationMetric],
) -> dict[str, Any]:
    groups: dict[tuple[Any, ...], list[DeclarationMetric]] = defaultdict(list)
    for metric in declaration_metrics:
        if metric.module != extraction.analysis_root_module or metric.kind not in {"theorem", "lemma"}:
            continue
        if metric.line_span < 4:
            continue
        groups[proof_shape_signature(metric)].append(metric)
    families = []
    for signature, metrics in groups.items():
        if len(metrics) < 2:
            continue
        metrics.sort(key=lambda item: (item.line, item.full_name))
        families.append(
            {
                "root_module": extraction.analysis_root_module,
                "family_size": len(metrics),
                "signature": [str(item) for item in signature],
                "declarations": [
                    {
                        "full_name": metric.full_name,
                        "path": metric.path,
                        "line": metric.line,
                        "line_span": metric.line_span,
                        "fragility_calibrated_score": metric.fragility_calibrated_score,
                    }
                    for metric in metrics[:12]
                ],
            }
        )
    families.sort(key=lambda item: (item["family_size"], item["declarations"][0]["full_name"]), reverse=True)
    return {
        "scope": "analysis_closure",
        "root_module": extraction.analysis_root_module,
        "family_count": len(families),
        "families": families[:10],
    }


def summarize_root_declaration_metrics(
    *,
    extraction: ExtractionResult,
    declaration_metrics: list[DeclarationMetric],
) -> dict[str, Any]:
    root_decls = [metric for metric in declaration_metrics if metric.module == extraction.analysis_root_module]
    by_kind = Counter(metric.kind for metric in root_decls)

    def decl_payload(metric: DeclarationMetric) -> dict[str, Any]:
        return {
            "full_name": metric.full_name,
            "name": metric.name,
            "kind": metric.kind,
            "path": metric.path,
            "line": metric.line,
            "line_span": metric.line_span,
            "parser_decision_complexity": metric.parser_decision_complexity,
            "fragility_score": metric.fragility_score,
            "fragility_calibrated_score": metric.fragility_calibrated_score,
            "fragility_calibrated_band": metric.fragility_calibrated_band,
            "body_tree_node_count": metric.body_tree_node_count,
            "body_tree_max_depth": metric.body_tree_max_depth,
        }

    return {
        "scope": "analysis_closure",
        "root_module": extraction.analysis_root_module,
        "root_path": extraction.analysis_root_file,
        "root_declaration_count": len(root_decls),
        "by_kind": dict(sorted(by_kind.items())),
        "declarations": [decl_payload(metric) for metric in sorted(root_decls, key=lambda item: (item.line, item.full_name))],
        "top_fragility": [
            decl_payload(metric)
            for metric in sorted(
                root_decls,
                key=lambda item: (
                    item.fragility_calibrated_score,
                    item.fragility_score,
                    item.line_span,
                    item.full_name,
                ),
                reverse=True,
            )[:10]
        ],
        "top_decision": [
            decl_payload(metric)
            for metric in sorted(
                root_decls,
                key=lambda item: (
                    item.parser_decision_complexity or 0,
                    item.parser_decision_nesting_complexity or 0,
                    item.full_name,
                ),
                reverse=True,
            )[:10]
        ],
        "largest_declarations": [
            decl_payload(metric)
            for metric in sorted(root_decls, key=lambda item: (item.line_span, item.full_name), reverse=True)[:10]
        ],
    }


def run_git_command(root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def changed_paths_since_base(root: Path, base: str) -> tuple[list[str], str | None]:
    proc = run_git_command(root, ["diff", "--name-only", "--diff-filter=ACMRT", base, "--"])
    if proc.returncode != 0:
        return [], (proc.stderr or proc.stdout).strip()
    tracked = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    untracked_proc = run_git_command(root, ["ls-files", "--others", "--exclude-standard"])
    untracked = (
        {line.strip() for line in untracked_proc.stdout.splitlines() if line.strip()}
        if untracked_proc.returncode == 0
        else set()
    )
    ignored_prefixes = (".git/", ".lake/", "__pycache__/", "outputs/")
    ignored_suffixes = (".pyc", ".olean", ".ilean")
    paths = [
        path
        for path in sorted(tracked | untracked)
        if not path.startswith(ignored_prefixes)
        and not any(part == "__pycache__" for part in Path(path).parts)
        and not path.endswith(ignored_suffixes)
    ]
    return paths, None


def git_file_at_ref(root: Path, ref: str, rel_path: str) -> str | None:
    proc = run_git_command(root, ["show", f"{ref}:{rel_path}"])
    if proc.returncode != 0:
        return None
    return proc.stdout


def simple_declaration_source_slices(source: str) -> dict[str, str]:
    matches = list(DECL_START_RE.finditer(source))
    slices: dict[str, str] = {}
    name_re = re.compile(
        r"^\s*(?:@[^\n]+\n\s*)*(?:def|theorem|lemma|structure|class|abbrev|instance|inductive)\s+([A-Za-z0-9_'.]+)",
        re.MULTILINE,
    )
    for index, match in enumerate(matches):
        name_match = name_re.match(source, match.start())
        if not name_match:
            continue
        name = name_match.group(1).split(".")[-1]
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        slices[name] = source[match.start():end].strip()
    return slices


def changed_root_declarations_since_base(
    *,
    root: Path,
    base: str,
    changed_paths: set[str],
    extraction: ExtractionResult,
    declaration_metrics: list[DeclarationMetric],
) -> list[dict[str, Any]]:
    root_decls = [metric for metric in declaration_metrics if metric.module == extraction.analysis_root_module]
    if not root_decls:
        return []
    current_slices = declaration_source_slices(root, root_decls)
    base_text_by_path: dict[str, str | None] = {}
    base_slices_by_path: dict[str, dict[str, str]] = {}
    changed: list[dict[str, Any]] = []
    for metric in sorted(root_decls, key=lambda item: (item.line, item.full_name)):
        if metric.path not in changed_paths:
            continue
        if metric.path not in base_text_by_path:
            base_text_by_path[metric.path] = git_file_at_ref(root, base, metric.path)
            base_slices_by_path[metric.path] = (
                simple_declaration_source_slices(base_text_by_path[metric.path] or "")
                if base_text_by_path[metric.path] is not None
                else {}
            )
        base_slice = base_slices_by_path[metric.path].get(metric.name)
        current_slice = (current_slices.get(metric.full_name) or "").strip()
        if base_slice is None:
            status = "new"
        elif current_slice != base_slice.strip():
            status = "changed"
        else:
            continue
        changed.append(
            {
                "full_name": metric.full_name,
                "name": metric.name,
                "kind": metric.kind,
                "path": metric.path,
                "line": metric.line,
                "line_span": metric.line_span,
                "status": status,
            }
        )
    return changed


def module_for_changed_path(path: str, modules: dict[str, audit.ModuleInfo]) -> str | None:
    for module, info in modules.items():
        if info.path == path:
            return module
    if path.endswith(".lean"):
        return str(Path(path).with_suffix("")).replace("/", ".")
    return None


def summarize_diff_focus(
    *,
    root: Path,
    args: argparse.Namespace,
    extraction: ExtractionResult,
    repo_modules: dict[str, audit.ModuleInfo],
    declaration_metrics: list[DeclarationMetric],
    findings: list[LadonFinding],
) -> dict[str, Any] | None:
    if not args.diff_base:
        return None
    changed_paths, error = changed_paths_since_base(root, args.diff_base)
    if error is not None:
        return {
            "status": "failed",
            "base": args.diff_base,
            "error": error,
            "changed_path_count": 0,
            "changed_paths": [],
            "changed_root_declaration_count": 0,
            "changed_root_declarations": [],
            "changed_finding_count": 0,
            "changed_findings": [],
        }
    changed_path_set = set(changed_paths)
    changed_modules = sorted(
        {
            module
            for path in changed_paths
            for module in [module_for_changed_path(path, repo_modules)]
            if module is not None
        }
    )
    changed_root_decls = changed_root_declarations_since_base(
        root=root,
        base=args.diff_base,
        changed_paths=changed_path_set,
        extraction=extraction,
        declaration_metrics=declaration_metrics,
    )
    changed_findings = [
        finding
        for finding in findings
        if changed_path_set.intersection(finding.files) or set(changed_modules).intersection(finding.modules)
    ]
    changed_findings.sort(key=lambda finding: (finding.scope, finding.category, finding.title))
    return {
        "status": "audited",
        "base": args.diff_base,
        "changed_path_count": len(changed_paths),
        "changed_paths": changed_paths,
        "changed_analysis_closure_files": [path for path in changed_paths if path in extraction.analysis_closure_files],
        "changed_repo_inventory_files": [
            path
            for path in changed_paths
            if any(info.path == path for info in repo_modules.values())
        ],
        "changed_doc_files": [path for path in changed_paths if path.endswith((".md", ".tex", ".txt"))],
        "changed_witness_paths": [path for path in changed_paths if path.startswith("witnesses/")],
        "changed_modules": changed_modules,
        "changed_root_declaration_count": len(changed_root_decls),
        "changed_root_declarations": changed_root_decls,
        "changed_finding_count": len(changed_findings),
        "changed_findings": [asdict(finding) for finding in changed_findings[:20]],
    }


def root_related_findings(findings: list[LadonFinding], extraction: ExtractionResult) -> list[LadonFinding]:
    root_module = extraction.analysis_root_module
    root_file = extraction.analysis_root_file
    related: list[LadonFinding] = []
    for finding in findings:
        if root_module in finding.modules or root_file in finding.files:
            related.append(finding)
            continue
        if finding.category in {"analysis_closure_explosion", "source_export_mismatch", "source_export_mismatch_stale_build_suspected"}:
            related.append(finding)
    severity_order = {"warn": 3, "review": 2, "info": 1}
    related.sort(
        key=lambda finding: (
            severity_order.get(finding.severity, 0),
            finding.confidence == "deterministic",
            finding.category,
            finding.title,
        ),
        reverse=True,
    )
    return related


def summarize_metrics(module_metrics_payload: dict[str, dict[str, Any]], declaration_metrics: list[DeclarationMetric]) -> dict[str, Any]:
    body_metrics = [metric for metric in declaration_metrics if metric.body_tree_node_count is not None]
    decision_metrics = [metric for metric in declaration_metrics if metric.parser_decision_complexity is not None]
    return {
        "scope": "analysis_closure",
        "module_count": len(module_metrics_payload),
        "declaration_count": len(declaration_metrics),
        "max_module_fan_in": max((m["fan_in"] for m in module_metrics_payload.values()), default=0),
        "max_module_line_count": max((m["line_count"] for m in module_metrics_payload.values()), default=0),
        "max_warning_density_per_100_lines": max((m["warning_density_per_100_lines"] for m in module_metrics_payload.values()), default=0.0),
        "declarations_with_body_metrics": len(body_metrics),
        "max_body_tree_node_count": max((metric.body_tree_node_count or 0 for metric in body_metrics), default=0),
        "max_body_tree_depth": max((metric.body_tree_max_depth or 0 for metric in body_metrics), default=0),
        "declarations_with_decision_metrics": len(decision_metrics),
        "max_parser_decision_complexity": max((metric.parser_decision_complexity or 0 for metric in decision_metrics), default=0),
        "max_parser_decision_nesting_complexity": max((metric.parser_decision_nesting_complexity or 0 for metric in decision_metrics), default=0),
    }


def healthy_owner_components(metric: dict[str, Any], concentration: dict[str, Any], module_findings: set[str]) -> list[str]:
    components: list[str] = []
    decl_kind_count = len(metric["declaration_kinds"])
    if metric["fan_in"] >= HEALTHY_OWNER_MIN_FAN_IN:
        components.append("moderate_fan_in")
    if metric["import_count"] <= HEALTHY_OWNER_MAX_IMPORTS:
        components.append("thin_import_surface")
    if metric["fan_out"] <= HEALTHY_OWNER_MAX_FAN_OUT:
        components.append("low_fan_out")
    if metric["line_count"] <= HEALTHY_OWNER_MAX_LINE_COUNT:
        components.append("bounded_size")
    if metric["declaration_count"] <= HEALTHY_OWNER_MAX_DECLARATIONS:
        components.append("bounded_surface")
    if metric["declaration_count"] >= HEALTHY_OWNER_MIN_DECLARATIONS:
        components.append("nontrivial_surface")
    if decl_kind_count <= HEALTHY_OWNER_MAX_DECL_KIND_COUNT:
        components.append("cohesive_decl_kinds")
    if concentration["score"] < CONCENTRATION_SCORE_THRESHOLD:
        components.append("low_concentration")
    if not {
        "mixed_responsibility_module",
        "registry_facade_concentration",
        "family_residue_in_generic_owner",
        "transit_import_surface",
        "owner_surface_role_mixture",
        "near_duplicate_structure_surface",
        "repeated_semantic_expression",
    } & module_findings:
        components.append("no_owner_smells")
    return components


def umbrella_owner_components(metric: dict[str, Any], concentration: dict[str, Any], module_findings: set[str]) -> list[str]:
    components: list[str] = []
    decl_kind_count = len(metric["declaration_kinds"])
    if metric["fan_in"] >= UMBRELLA_OWNER_MIN_FAN_IN:
        components.append("high_fan_in")
    if metric["import_count"] >= UMBRELLA_OWNER_MIN_IMPORTS:
        components.append("broad_import_surface")
    if metric["fan_out"] >= UMBRELLA_OWNER_MIN_FAN_OUT:
        components.append("high_fan_out")
    if metric["declaration_count"] >= UMBRELLA_OWNER_MIN_DECLARATIONS:
        components.append("broad_surface")
    if decl_kind_count >= UMBRELLA_OWNER_MIN_DECL_KIND_COUNT:
        components.append("mixed_decl_kinds")
    if concentration["score"] >= CONCENTRATION_SCORE_THRESHOLD:
        components.append("high_concentration")
    if "mixed_responsibility_module" in module_findings:
        components.append("mixed_responsibility_signal")
    if "registry_facade_concentration" in module_findings:
        components.append("registry_facade_signal")
    if "family_residue_in_generic_owner" in module_findings:
        components.append("owner_mismatch_signal")
    if "owner_surface_role_mixture" in module_findings:
        components.append("role_mixture_signal")
    if "near_duplicate_structure_surface" in module_findings:
        components.append("duplicate_structure_signal")
    if "repeated_semantic_expression" in module_findings:
        components.append("semantic_repetition_signal")
    return components


def assess_owner_health(
    module_metrics_payload: dict[str, dict[str, Any]],
    base_findings: list[LadonFinding],
) -> OwnerHealthAssessment:
    findings = list(base_findings)
    next_id = len(findings) + 1
    module_findings: dict[str, set[str]] = defaultdict(set)
    for finding in findings:
        if finding.scope != "repo_inventory":
            continue
        for module in finding.modules:
            module_findings[module].add(finding.category)

    by_module: dict[str, dict[str, Any]] = {}
    healthy_modules: list[dict[str, Any]] = []
    umbrella_modules: list[dict[str, Any]] = []
    for module, metric in sorted(module_metrics_payload.items()):
        concentration = concentration_components(metric)
        existing = module_findings.get(module, set())
        healthy_components = healthy_owner_components(metric, concentration, existing)
        umbrella_components = umbrella_owner_components(metric, concentration, existing)
        is_healthy = (
            metric["fan_in"] >= HEALTHY_OWNER_MIN_FAN_IN
            and metric["declaration_count"] >= HEALTHY_OWNER_MIN_DECLARATIONS
            and len(healthy_components) >= 6
            and len(umbrella_components) < 4
        )
        is_umbrella = metric["fan_in"] >= UMBRELLA_OWNER_MIN_FAN_IN and len(umbrella_components) >= 4
        state = "healthy" if is_healthy and not is_umbrella else "umbrella" if is_umbrella else "neutral"
        payload = {
            "module": module,
            "path": metric["path"],
            "state": state,
            "healthy_components": healthy_components,
            "umbrella_components": umbrella_components,
            "fan_in": metric["fan_in"],
            "fan_out": metric["fan_out"],
            "import_count": metric["import_count"],
            "declaration_count": metric["declaration_count"],
            "decl_kind_count": len(metric["declaration_kinds"]),
            "concentration_score": concentration["score"],
        }
        by_module[module] = payload
        if state == "healthy":
            healthy_modules.append(payload)
        elif state == "umbrella":
            umbrella_modules.append(payload)
            findings.append(
                LadonFinding(
                    id=f"L{next_id:04d}",
                    category="umbrella_owner",
                    severity="review",
                    confidence="heuristic",
                    title=f"Umbrella owner hotspot: {module}",
                    summary=f"{module} still looks like an umbrella owner rather than a narrow cohesive module.",
                    files=[metric["path"]],
                    modules=[module],
                    declarations=[],
                    scope="repo_inventory",
                    evidence=[
                        f"fan_in={metric['fan_in']}",
                        f"fan_out={metric['fan_out']}",
                        f"import_count={metric['import_count']}",
                        f"declaration_count={metric['declaration_count']}",
                        f"decl_kind_count={len(metric['declaration_kinds'])}",
                        f"concentration_score={concentration['score']}",
                        f"components={','.join(umbrella_components)}",
                    ],
                    remediation="Review whether this module should be split into narrower owners or reduced to a thin migration facade.",
                )
            )
            next_id += 1

    healthy_modules.sort(key=lambda item: (item["fan_in"], -item["concentration_score"], item["module"]), reverse=True)
    umbrella_modules.sort(key=lambda item: (len(item["umbrella_components"]), item["fan_in"], item["declaration_count"], item["module"]), reverse=True)
    return OwnerHealthAssessment(
        by_module=by_module,
        findings=findings,
        summary={
            "scope": "repo_inventory",
            "healthy_owner_count": len(healthy_modules),
            "umbrella_owner_count": len(umbrella_modules),
            "healthy_modules": healthy_modules[:10],
            "umbrella_modules": umbrella_modules[:10],
        },
    )


def reinterpret_import_hotspots(findings: list[LadonFinding], owner_health: dict[str, dict[str, Any]]) -> list[LadonFinding]:
    updated: list[LadonFinding] = []
    for finding in findings:
        if finding.scope != "repo_inventory" or finding.category != "import_hotspot" or len(finding.modules) != 1:
            updated.append(finding)
            continue
        module = finding.modules[0]
        state = owner_health.get(module, {}).get("state", "neutral")
        if state == "healthy":
            continue
        if state == "umbrella":
            updated.append(
                LadonFinding(
                    id=finding.id,
                    category=finding.category,
                    severity="review",
                    confidence=finding.confidence,
                    title=f"Umbrella-owner import hotspot: {module}",
                    summary=f"{module} has high fan-in and also looks like an umbrella owner, so its coupling remains an architectural smell.",
                    files=finding.files,
                    modules=finding.modules,
                    declarations=finding.declarations,
                    scope=finding.scope,
                    evidence=list(finding.evidence) + [
                        "owner_health=umbrella",
                        f"umbrella_components={','.join(owner_health[module]['umbrella_components'])}",
                    ],
                    remediation=finding.remediation,
                )
            )
            continue
        updated.append(finding)
    return updated


def summarize_inventory_metrics(module_metrics_payload: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "scope": "repo_inventory",
        "module_count": len(module_metrics_payload),
        "declaration_count": sum(metric["declaration_count"] for metric in module_metrics_payload.values()),
        "max_module_fan_in": max((m["fan_in"] for m in module_metrics_payload.values()), default=0),
        "max_module_line_count": max((m["line_count"] for m in module_metrics_payload.values()), default=0),
        "max_warning_density_per_100_lines": max(
            (m["warning_density_per_100_lines"] for m in module_metrics_payload.values()),
            default=0.0,
        ),
    }


def percentile_rank(values: list[float], value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return 1.0
    leq = sum(1 for item in ordered if item <= value)
    return max(0.0, min(1.0, (leq - 1) / (len(ordered) - 1)))


def saturating_ratio(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return min(1.0, math.log1p(max(value, 0.0)) / math.log1p(max_value))


def combine_normalized_feature(values: list[float], value: float) -> float:
    if not values:
        return 0.0
    return round((percentile_rank(values, value) + saturating_ratio(value, max(values))) / 2.0, 4)


def aggregate_module_fragility(declaration_metrics: list[DeclarationMetric]) -> dict[str, dict[str, float]]:
    by_module: dict[str, list[DeclarationMetric]] = defaultdict(list)
    for metric in declaration_metrics:
        by_module[metric.module].append(metric)
    result: dict[str, dict[str, float]] = {}
    for module, metrics in by_module.items():
        scores = [metric.fragility_score for metric in metrics]
        hotspots = [metric for metric in metrics if is_fragility_hotspot(metric)]
        result[module] = {
            "max_fragility_score": max(scores, default=0),
            "max_fragility_calibrated_score": max((metric.fragility_calibrated_score for metric in metrics), default=0),
            "fragility_hotspot_count": len(hotspots),
        }
    return result


def aggregate_module_deadness(module_deadness: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    return module_deadness


def module_score_severity(axis_scores: dict[str, float]) -> str:
    available = [value for value in axis_scores.values()]
    strong = sum(1 for value in available if value >= 0.8)
    moderate = sum(1 for value in available if value >= 0.6)
    if strong >= 2 or (strong >= 1 and moderate >= 2):
        return "high"
    if strong >= 1 or moderate >= 2:
        return "medium"
    if moderate >= 1 or any(value >= 0.4 for value in available):
        return "low"
    return "info"


def summarize_hotspot_scores(
    module_metrics_payload: dict[str, dict[str, Any]],
    declaration_metrics: list[DeclarationMetric],
    module_deadness: dict[str, dict[str, float]],
    owner_health: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    fragility_by_module = aggregate_module_fragility(declaration_metrics)
    deadness_by_module = aggregate_module_deadness(module_deadness)
    concentration_by_module = {module: concentration_components(metric) for module, metric in module_metrics_payload.items()}

    feature_values = {
        "line_count": [metric["line_count"] for metric in module_metrics_payload.values()],
        "declaration_count": [metric["declaration_count"] for metric in module_metrics_payload.values()],
        "warning_density_per_100_lines": [metric["warning_density_per_100_lines"] for metric in module_metrics_payload.values()],
        "fan_in": [metric["fan_in"] for metric in module_metrics_payload.values()],
        "fan_out": [metric["fan_out"] for metric in module_metrics_payload.values()],
        "import_count": [metric["import_count"] for metric in module_metrics_payload.values()],
        "concentration_score": [components["score"] for components in concentration_by_module.values()],
        "declaration_density_per_100_lines": [components["declaration_density_per_100_lines"] for components in concentration_by_module.values()],
        "def_like_ratio": [components["def_like_ratio"] for components in concentration_by_module.values()],
        "max_fragility_score": [fragility["max_fragility_score"] for fragility in fragility_by_module.values()] or [0],
        "max_fragility_calibrated_score": [fragility["max_fragility_calibrated_score"] for fragility in fragility_by_module.values()] or [0],
        "fragility_hotspot_count": [fragility["fragility_hotspot_count"] for fragility in fragility_by_module.values()] or [0],
        "dead_module_finding_count": [deadness["dead_module_finding_count"] for deadness in deadness_by_module.values()] or [0],
        "warn_dead_module_finding_count": [deadness["warn_dead_module_finding_count"] for deadness in deadness_by_module.values()] or [0],
        "dead_declaration_count": [deadness["dead_declaration_count"] for deadness in deadness_by_module.values()] or [0],
        "dead_component_count": [deadness["dead_component_count"] for deadness in deadness_by_module.values()] or [0],
        "prioritized_dead_component_count": [deadness["prioritized_dead_component_count"] for deadness in deadness_by_module.values()] or [0],
        "prioritized_dead_declaration_count": [deadness["prioritized_dead_declaration_count"] for deadness in deadness_by_module.values()] or [0],
        "strong_dead_declaration_count": [deadness["strong_dead_declaration_count"] for deadness in deadness_by_module.values()] or [0],
    }

    ranked: list[dict[str, Any]] = []
    for module, metric in module_metrics_payload.items():
        concentration = concentration_by_module[module]
        fragility = fragility_by_module.get(module)
        deadness = deadness_by_module.get(module)
        health = owner_health.get(module, {"state": "neutral", "healthy_components": [], "umbrella_components": []})

        axis_details: dict[str, Any] = {}
        axis_scores: dict[str, float] = {}
        feature_explanations: list[dict[str, Any]] = []

        def add_axis(name: str, raw_features: list[tuple[str, float]], available: bool) -> None:
            nonlocal axis_details, axis_scores, feature_explanations
            if not available:
                axis_details[name] = {"available": False}
                return
            features = []
            for feature_name, raw_value in raw_features:
                normalized = combine_normalized_feature(feature_values[feature_name], raw_value)
                payload = {"feature": feature_name, "raw": raw_value, "normalized": normalized}
                features.append(payload)
                feature_explanations.append({"axis": name, **payload})
            score = round(sum(item["normalized"] for item in features) / max(len(features), 1), 4)
            axis_details[name] = {"available": True, "score": score, "features": features}
            axis_scores[name] = score

        add_axis(
            "complexity",
            [
                ("line_count", metric["line_count"]),
                ("declaration_count", metric["declaration_count"]),
                ("warning_density_per_100_lines", metric["warning_density_per_100_lines"]),
            ],
            True,
        )
        add_axis(
            "coupling",
            [
                ("fan_in", metric["fan_in"]),
                ("fan_out", metric["fan_out"]),
                ("import_count", metric["import_count"]),
            ],
            True,
        )
        if axis_details["coupling"]["available"]:
            base_score = axis_details["coupling"]["score"]
            adjustment = 0.0
            if health["state"] == "healthy":
                adjustment = -0.2
            elif health["state"] == "umbrella":
                adjustment = 0.15
            adjusted = round(max(0.0, min(1.0, base_score + adjustment)), 4)
            axis_details["coupling"]["base_score"] = base_score
            axis_details["coupling"]["score"] = adjusted
            axis_details["coupling"]["owner_health_state"] = health["state"]
            axis_details["coupling"]["owner_health_adjustment"] = adjustment
            axis_details["coupling"]["owner_health_components"] = (
                health["healthy_components"] if health["state"] == "healthy" else health["umbrella_components"]
            )
            axis_scores["coupling"] = adjusted
        add_axis(
            "concentration",
            [
                ("concentration_score", concentration["score"]),
                ("declaration_density_per_100_lines", concentration["declaration_density_per_100_lines"]),
                ("def_like_ratio", concentration["def_like_ratio"]),
            ],
            True,
        )
        if fragility is not None:
            add_axis(
                "fragility",
                [
                    ("max_fragility_calibrated_score", fragility["max_fragility_calibrated_score"]),
                    ("fragility_hotspot_count", fragility["fragility_hotspot_count"]),
                ],
                True,
            )
        else:
            add_axis("fragility", [], False)
        if deadness is not None:
            add_axis(
                "deadness",
                [
                    ("dead_module_finding_count", deadness["dead_module_finding_count"]),
                    ("prioritized_dead_declaration_count", deadness["prioritized_dead_declaration_count"]),
                    ("prioritized_dead_component_count", deadness["prioritized_dead_component_count"]),
                    ("strong_dead_declaration_count", deadness["strong_dead_declaration_count"]),
                ],
                True,
            )
        else:
            add_axis("deadness", [], False)

        overall_score = round(sum(axis_scores.values()) / max(len(axis_scores), 1), 4) if axis_scores else 0.0
        severity = module_score_severity(axis_scores)
        top_contributors = sorted(feature_explanations, key=lambda item: (item["normalized"], item["raw"], item["feature"]), reverse=True)[:3]
        ranked.append(
            {
                "scope": "repo_inventory",
                "module": module,
                "path": metric["path"],
                "score": overall_score,
                "severity": severity,
                "axes": axis_details,
                "top_contributors": top_contributors,
            }
        )

    severity_order = {"high": 3, "medium": 2, "low": 1, "info": 0}
    ranked.sort(
        key=lambda item: (
            severity_order[item["severity"]],
            item["score"],
            item["module"],
        ),
        reverse=True,
    )
    return {
        "scope": "repo_inventory",
        "top_modules": ranked[:10],
    }


def normalized_name_tokens(raw: str) -> list[str]:
    normalized = raw.replace(".", "_").replace("/", "_").replace("'", "_")
    tokens: list[str] = []
    for chunk in re.split(r"[^A-Za-z0-9]+", normalized):
        if not chunk:
            continue
        parts = TOKEN_SPLIT_RE.findall(chunk) or [chunk]
        for part in parts:
            lowered = part.lower()
            if lowered.isdigit() or len(lowered) < 2:
                continue
            tokens.append(lowered)
    return tokens


def segment_surface_tokens(segment: str) -> set[str]:
    tokens = normalized_name_tokens(segment)
    surface = set(tokens)
    for i in range(len(tokens) - 1):
        surface.add(tokens[i] + tokens[i + 1])
    for i in range(len(tokens) - 2):
        surface.add(tokens[i] + tokens[i + 1] + tokens[i + 2])
    return surface


def module_surface_tokens(module: str, path: str) -> set[str]:
    tokens: set[str] = set()
    for segment in module.split("."):
        tokens.update(segment_surface_tokens(segment))
    tokens.update(segment_surface_tokens(Path(path).stem))
    return tokens


def declaration_leading_token(name: str) -> str | None:
    tokens = normalized_name_tokens(name)
    return tokens[0] if tokens else None


def generic_owner_basename_tokens(path: str) -> set[str]:
    return set(normalized_name_tokens(Path(path).stem))


def add_family_residue_findings(
    repo_modules: dict[str, audit.ModuleInfo],
    base_findings: list[LadonFinding],
) -> list[LadonFinding]:
    findings = list(base_findings)
    next_id = len(findings) + 1
    for module, info in sorted(repo_modules.items()):
        declarations = info.declarations
        if len(declarations) < FAMILY_RESIDUE_MIN_DECLARATIONS and info.fan_in < FAMILY_RESIDUE_MIN_FAN_IN:
            continue
        owner_tokens = module_surface_tokens(module, info.path)
        basename_tokens = generic_owner_basename_tokens(info.path)
        if not basename_tokens.intersection(GENERIC_OWNER_TOKENS):
            continue
        if any(token not in GENERIC_OWNER_TOKENS for token in basename_tokens):
            continue
        token_to_names: dict[str, list[str]] = {}
        for decl in declarations:
            token = declaration_leading_token(decl.name)
            if token is None:
                continue
            token_to_names.setdefault(token, []).append(decl.name)
        foreign_candidates = {
            token: names
            for token, names in token_to_names.items()
            if token not in owner_tokens
            and token not in GENERIC_OWNER_TOKENS
            and token not in FAMILY_RESIDUE_IGNORED_TOKENS
        }
        if not foreign_candidates:
            continue
        dominant_token, dominant_names = max(
            foreign_candidates.items(),
            key=lambda item: (len(item[1]), item[0]),
        )
        foreign_count = len(dominant_names)
        total_count = len(declarations)
        foreign_ratio = foreign_count / max(total_count, 1)
        if foreign_count < FAMILY_RESIDUE_MIN_FOREIGN_DECLS or foreign_ratio < FAMILY_RESIDUE_MIN_RATIO:
            continue
        findings.append(
            LadonFinding(
                id=f"L{next_id:04d}",
                category="family_residue_in_generic_owner",
                severity="review",
                confidence="heuristic",
                title=f"Family residue in generic owner: {module}",
                summary=(
                    f"{module} looks like a generic owner, but its declaration surface is dominated by "
                    f"`{dominant_token}`-prefixed names."
                ),
                files=[info.path],
                modules=[module],
                declarations=sorted(dominant_names[:5]),
                scope="repo_inventory",
                evidence=[
                    f"module_tokens={','.join(sorted(owner_tokens))}",
                    f"dominant_foreign_token={dominant_token}",
                    f"foreign_declaration_count={foreign_count}",
                    f"total_declaration_count={total_count}",
                    f"foreign_ratio={foreign_ratio:.2f}",
                    f"fan_in={info.fan_in}",
                ],
                remediation=(
                    "Review whether the generic owner should be renamed or whether the foreign-prefixed declarations should move to a family-owned module."
                ),
            )
        )
        next_id += 1
    return findings


def declaration_basename(name: str) -> str:
    return name.split(".")[-1]


def declaration_tokens(info: audit.ModuleInfo) -> list[str]:
    tokens: list[str] = []
    for decl in info.declarations:
        tokens.extend(normalized_name_tokens(declaration_basename(decl.name)))
    return tokens


OWNER_ROLE_FAMILIES: dict[str, set[str]] = {
    "diagnostic": {"diagnostic", "obstruction", "idempotence", "invalid", "failure", "counterexample"},
    "positive_bridge": {"alignment", "compatibility", "transport", "bridge", "endpoint"},
    "target_surface": {"goal", "target", "seam", "surface", "boundary", "prerequisite"},
    "profile_pair": {"profile", "pair", "density", "law"},
    "exactness": {"exact", "warm", "start", "canonical"},
}


def owner_role_hits(info: audit.ModuleInfo) -> dict[str, int]:
    tokens = declaration_tokens(info)
    return {
        family: sum(1 for token in tokens if token in family_tokens)
        for family, family_tokens in OWNER_ROLE_FAMILIES.items()
    }


def add_owner_surface_role_mix_findings(
    module_metrics_payload: dict[str, dict[str, Any]],
    repo_modules: dict[str, audit.ModuleInfo],
    base_findings: list[LadonFinding],
) -> list[LadonFinding]:
    findings = list(base_findings)
    next_id = len(findings) + 1
    for module, info in sorted(repo_modules.items()):
        metric = module_metrics_payload[module]
        if (
            metric["line_count"] < OWNER_ROLE_MIX_MIN_LINE_COUNT
            or metric["declaration_count"] < OWNER_ROLE_MIX_MIN_DECLARATIONS
        ):
            continue
        hits = owner_role_hits(info)
        active = {family: count for family, count in hits.items() if count > 0}
        total_hits = sum(active.values())
        if len(active) < OWNER_ROLE_MIX_MIN_ROLE_FAMILIES or total_hits < OWNER_ROLE_MIX_MIN_ROLE_HITS:
            continue
        findings.append(
            LadonFinding(
                id=f"L{next_id:04d}",
                category="owner_surface_role_mixture",
                severity="review",
                confidence="heuristic",
                title=f"Mixed theorem-owner roles: {module}",
                summary=(
                    f"{module} is a large owner whose declaration names mix multiple theorem-surface roles "
                    "such as diagnostics, bridge/alignment endpoints, and goal/seam targets."
                ),
                files=[info.path],
                modules=[module],
                declarations=[],
                scope="repo_inventory",
                evidence=[
                    f"line_count={metric['line_count']}",
                    f"declaration_count={metric['declaration_count']}",
                    f"active_role_families={','.join(sorted(active))}",
                    f"role_hits={','.join(f'{family}:{count}' for family, count in sorted(active.items()))}",
                ],
                remediation=(
                    "Review whether diagnostic/obstruction claims, positive bridge witnesses, and endpoint consumers should live in separate owner modules."
                ),
            )
        )
        next_id += 1
    return findings


def structure_blocks(text: str) -> list[dict[str, Any]]:
    matches = list(STRUCTURE_DECL_RE.finditer(text))
    blocks: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        start = match.start()
        next_decl = DECL_START_RE.search(text, match.end())
        if next_decl is None:
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        else:
            end = next_decl.start()
        block = text[start:end]
        fields = STRUCTURE_FIELD_RE.findall(block)
        blocks.append(
            {
                "name": match.group(1),
                "line": text.count("\n", 0, match.start()) + 1,
                "fields": fields,
                "field_set": set(fields),
            }
        )
    return blocks


def add_near_duplicate_structure_findings(
    root: Path,
    repo_modules: dict[str, audit.ModuleInfo],
    base_findings: list[LadonFinding],
) -> list[LadonFinding]:
    findings = list(base_findings)
    next_id = len(findings) + 1
    for module, info in sorted(repo_modules.items()):
        blocks = structure_blocks((root / info.path).read_text(encoding="utf-8"))
        for left_index, left in enumerate(blocks):
            left_fields = left["field_set"]
            if len(left_fields) < NEAR_DUPLICATE_STRUCTURE_MIN_FIELDS:
                continue
            for right in blocks[left_index + 1:]:
                right_fields = right["field_set"]
                if len(right_fields) < NEAR_DUPLICATE_STRUCTURE_MIN_FIELDS:
                    continue
                common = left_fields & right_fields
                similarity = len(common) / max(len(left_fields), len(right_fields), 1)
                if similarity < NEAR_DUPLICATE_STRUCTURE_MIN_SIMILARITY:
                    continue
                findings.append(
                    LadonFinding(
                        id=f"L{next_id:04d}",
                        category="near_duplicate_structure_surface",
                        severity="review",
                        confidence="heuristic",
                        title=f"Near-duplicate structure surfaces: {left['name']} and {right['name']}",
                        summary=(
                            f"{module} defines two structures with highly overlapping field surfaces, which often means a shared core structure is missing."
                        ),
                        files=[info.path],
                        modules=[module],
                        declarations=[left["name"], right["name"]],
                        scope="repo_inventory",
                        evidence=[
                            f"left_line={left['line']}",
                            f"right_line={right['line']}",
                            f"left_field_count={len(left_fields)}",
                            f"right_field_count={len(right_fields)}",
                            f"common_field_count={len(common)}",
                            f"similarity={similarity:.2f}",
                            f"common_fields={','.join(sorted(common)[:12])}",
                        ],
                        remediation=(
                            "Extract the shared fields into a common core structure and let the variant structures extend it with only their genuinely different fields."
                        ),
                    )
                )
                next_id += 1
    return findings


def repeated_semantic_expressions(text: str) -> list[tuple[str, int]]:
    counts = Counter(
        re.sub(r"\s+", " ", match.group(0).strip())
        for match in REPEATED_SEMANTIC_EXPR_RE.finditer(text)
    )
    return [
        (expr, count)
        for expr, count in counts.most_common()
        if count >= REPEATED_SEMANTIC_EXPR_THRESHOLD
    ]


def add_repeated_semantic_expression_findings(
    root: Path,
    repo_modules: dict[str, audit.ModuleInfo],
    base_findings: list[LadonFinding],
) -> list[LadonFinding]:
    findings = list(base_findings)
    next_id = len(findings) + 1
    for module, info in sorted(repo_modules.items()):
        repeated = repeated_semantic_expressions((root / info.path).read_text(encoding="utf-8"))
        if not repeated:
            continue
        expr, count = repeated[0]
        findings.append(
            LadonFinding(
                id=f"L{next_id:04d}",
                category="repeated_semantic_expression",
                severity="review",
                confidence="heuristic",
                title=f"Repeated semantic expression should probably be named: {module}",
                summary=(
                    f"{module} repeats `{expr}` {count} times. Repeated dotted arithmetic often hides an off-by-one or horizon convention that should be named."
                ),
                files=[info.path],
                modules=[module],
                declarations=[],
                scope="repo_inventory",
                evidence=[
                    f"expression={expr}",
                    f"occurrences={count}",
                    "pattern=dotted_arithmetic_expression",
                ],
                remediation=(
                    "Introduce a named helper/abbrev for the expression if it carries semantic meaning, especially for horizon, window, or shifted-count conventions."
                ),
            )
        )
        next_id += 1
    return findings


def concentration_components(metric: dict[str, Any]) -> dict[str, Any]:
    line_count = metric["line_count"]
    import_count = metric["import_count"]
    fan_out = metric["fan_out"]
    declaration_count = metric["declaration_count"]
    def_like_count = metric["def_like_count"]
    theorem_like_count = metric["theorem_like_count"]
    density = round((declaration_count / max(line_count, 1)) * 100, 2)
    def_like_ratio = round(def_like_count / max(declaration_count, 1), 2)
    theorem_like_ratio = round(theorem_like_count / max(declaration_count, 1), 2)
    score = 0
    components: list[str] = []
    if line_count >= CONCENTRATION_LINE_THRESHOLD:
        score += 1
        components.append("line_count")
    if import_count >= CONCENTRATION_IMPORT_THRESHOLD:
        score += 1
        components.append("import_count")
    if fan_out >= CONCENTRATION_FAN_OUT_THRESHOLD:
        score += 1
        components.append("fan_out")
    if declaration_count >= CONCENTRATION_DECL_THRESHOLD:
        score += 1
        components.append("declaration_count")
    if def_like_count >= CONCENTRATION_DEF_LIKE_THRESHOLD:
        score += 1
        components.append("def_like_count")
    if density >= CONCENTRATION_DENSITY_THRESHOLD:
        score += 1
        components.append("declaration_density")
    if theorem_like_count == 0 and def_like_ratio >= 0.75 and declaration_count >= CONCENTRATION_DECL_THRESHOLD:
        score += 1
        components.append("def_like_ratio")
    if theorem_like_ratio <= CONCENTRATION_THEOREM_LIKE_RATIO_CEILING and declaration_count >= CONCENTRATION_DECL_THRESHOLD:
        score += 1
        components.append("theorem_like_ratio")
    return {
        "score": score,
        "components": components,
        "line_count": line_count,
        "import_count": import_count,
        "fan_out": fan_out,
        "declaration_count": declaration_count,
        "def_like_count": def_like_count,
        "theorem_like_count": theorem_like_count,
        "declaration_density_per_100_lines": density,
        "def_like_ratio": def_like_ratio,
        "theorem_like_ratio": theorem_like_ratio,
    }


def concentration_is_registry_like(components: dict[str, Any]) -> bool:
    theorem_light = components["theorem_like_ratio"] <= CONCENTRATION_THEOREM_LIKE_RATIO_CEILING
    if not theorem_light and components["fan_out"] < CONCENTRATION_FAN_OUT_THRESHOLD:
        return False
    return (
        components["fan_out"] >= CONCENTRATION_FAN_OUT_THRESHOLD
        or components["line_count"] >= CONCENTRATION_LARGE_LINE_THRESHOLD
        or components["declaration_count"] >= CONCENTRATION_LARGE_DECL_THRESHOLD
        or (
            components["declaration_density_per_100_lines"] >= CONCENTRATION_DENSITY_THRESHOLD
            and components["import_count"] >= CONCENTRATION_IMPORT_THRESHOLD + 1
            and components["declaration_count"] <= CONCENTRATION_DENSE_SMALL_DECL_THRESHOLD
        )
    )


def add_concentration_findings(
    module_metrics_payload: dict[str, dict[str, Any]],
    base_findings: list[LadonFinding],
) -> list[LadonFinding]:
    findings = list(base_findings)
    next_id = len(findings) + 1
    for module, metric in sorted(
        module_metrics_payload.items(),
        key=lambda item: (
            concentration_components(item[1])["score"],
            item[1]["line_count"],
            item[1]["declaration_count"],
            item[0],
        ),
        reverse=True,
    ):
        components = concentration_components(metric)
        if components["score"] < CONCENTRATION_SCORE_THRESHOLD or not concentration_is_registry_like(components):
            continue
        findings.append(
            LadonFinding(
                id=f"L{next_id:04d}",
                category="registry_facade_concentration",
                severity="review",
                confidence="heuristic",
                title=f"Registry/facade concentration hotspot: {module}",
                summary=(
                    f"{module} combines broad surface concentration signals in repo inventory, "
                    f"including {', '.join(components['components'])}."
                ),
                files=[metric["path"]],
                modules=[module],
                declarations=[],
                scope="repo_inventory",
                evidence=[
                    f"score={components['score']}",
                    f"line_count={components['line_count']}",
                    f"import_count={components['import_count']}",
                    f"fan_out={components['fan_out']}",
                    f"declaration_count={components['declaration_count']}",
                    f"def_like_count={components['def_like_count']}",
                    f"theorem_like_count={components['theorem_like_count']}",
                    f"declaration_density_per_100_lines={components['declaration_density_per_100_lines']}",
                    f"def_like_ratio={components['def_like_ratio']}",
                    f"theorem_like_ratio={components['theorem_like_ratio']}",
                    f"components={','.join(components['components'])}",
                ],
                remediation=(
                    "Review whether this module is acting as a broad registry or facade surface and whether its declarations, imports, or examples should be split across narrower owner modules."
                ),
            )
        )
        next_id += 1
    return findings


def summarize_concentration_hotspots(module_metrics_payload: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ranked: list[dict[str, Any]] = []
    for module, metric in module_metrics_payload.items():
        components = concentration_components(metric)
        if components["score"] < CONCENTRATION_SCORE_THRESHOLD or not concentration_is_registry_like(components):
            continue
        ranked.append(
            {
                "scope": "repo_inventory",
                "module": module,
                "path": metric["path"],
                "score": components["score"],
                "components": components["components"],
                "line_count": components["line_count"],
                "import_count": components["import_count"],
                "fan_out": components["fan_out"],
                "declaration_count": components["declaration_count"],
                "declaration_density_per_100_lines": components["declaration_density_per_100_lines"],
                "theorem_like_ratio": components["theorem_like_ratio"],
            }
        )
    ranked.sort(
        key=lambda item: (
            item["score"],
            item["line_count"],
            item["declaration_count"],
            item["module"],
        ),
        reverse=True,
    )
    return {
        "scope": "repo_inventory",
        "top_modules": ranked[:10],
    }


def render_text(report: dict[str, Any]) -> str:
    meta = report["metadata"]
    root_focus = report["summary"].get("root_focus", {})
    closure_summary = report["summary"]["analysis_closure"]
    inventory_summary = report["summary"]["repo_inventory"]
    certificate_boundary_summary = report["summary"].get("certificate_boundary", {})
    concentration_summary = inventory_summary["concentration_hotspots"]
    hotspot_score_summary = inventory_summary["hotspot_scores"]
    owner_health_summary = inventory_summary["owner_health"]
    module_dag_summary = inventory_summary.get("module_dag", {})
    proof_hole_summary = inventory_summary.get("proof_holes", {})
    openspec_summary = inventory_summary.get("openspec_backlog", {})
    local_scripts_summary = inventory_summary.get("local_scripts", {})
    git_summary = inventory_summary.get("git_workspace", {})
    reference_graph_summary = closure_summary["reference_graph"]
    graph_reasoning_summary = closure_summary.get("graph_reasoning", {})
    fragility_summary = closure_summary["fragility_hotspots"]
    deadness_summary = closure_summary["deadness_summary"]
    lines = [
        "Ladon",
        f"Version: {meta['tool_version']} (report {meta['report_version']})",
        f"Repo root: {meta['repo_root']}",
        f"Analysis root: {meta['analysis_root']} ({meta['analysis_root_module']})",
        f"Analysis closure modules ({len(meta['analysis_closure_modules'])}): {list_preview(meta['analysis_closure_modules'])}",
        f"Analysis closure files ({len(meta['analysis_closure_files'])}): {list_preview(meta['analysis_closure_files'])}",
        f"Repo inventory root: {meta['repo_inventory_root']}",
        f"Repo inventory modules ({len(meta['repo_inventory_modules'])}): {list_preview(meta['repo_inventory_modules'])}",
        f"Build mode: {meta['build_mode']}",
        f"Warning build mode: {meta.get('warning_build_mode', meta['build_mode'])}",
        f"Extraction build verified: {meta.get('extraction_build_verified', '<unknown>')}",
        f"Export surface verification: {meta.get('export_surface_verification', 'skipped')}",
        f"Export surface checked declarations: {meta.get('export_surface_checked_declarations', 0)}",
        f"Export surface missing declarations: {meta.get('export_surface_missing_declarations', 0)}",
        f"Extraction backend: {meta['extraction_backend']} ({meta['extraction_policy']})",
        f"Extraction provenance: {meta['extraction_provenance']}",
        f"Extraction degraded: {meta['extraction_is_degraded']}",
        f"Git HEAD: {meta.get('git_head_sha') or '<unavailable>'}",
        f"Git dirty: {meta.get('git_is_dirty')} tracked={meta.get('git_status_tracked_count')} untracked={meta.get('git_status_untracked_count')}",
        f"Reachability root policy: {meta['reachability_root_policy']} ({meta['reachability_policy_strength']})",
        f"Requested root modules: {', '.join(meta['reachability_requested_root_modules']) if meta['reachability_requested_root_modules'] else '<none>'}",
        f"Requested root prefixes: {', '.join(meta['reachability_requested_root_prefixes']) if meta['reachability_requested_root_prefixes'] else '<none>'}",
        f"Resolved roots: {', '.join(meta['reachability_resolved_roots']) if meta['reachability_resolved_roots'] else '<none>'}",
        f"Reachability exclusion policy: {meta['reachability_exclusion_policy']}",
        f"Requested excluded modules: {', '.join(meta['reachability_requested_excluded_modules']) if meta['reachability_requested_excluded_modules'] else '<none>'}",
        f"Requested excluded prefixes: {', '.join(meta['reachability_requested_excluded_prefixes']) if meta['reachability_requested_excluded_prefixes'] else '<none>'}",
        f"Resolved exclusions: {', '.join(meta['reachability_resolved_exclusions']) if meta['reachability_resolved_exclusions'] else '<none>'}",
        "",
        "Root-Focused Findings",
        f"- root: {root_focus.get('analysis_root', meta['analysis_root'])} ({root_focus.get('analysis_root_module', meta['analysis_root_module'])})",
        f"- root findings: {root_focus.get('root_finding_count', 0)}",
        f"- root declarations: {root_focus.get('root_declarations', {}).get('root_declaration_count', 0)}",
        f"- doc audit: {root_focus.get('doc_coverage', {}).get('status', 'unavailable')}",
        f"- witness audit: {root_focus.get('witness_audit', {}).get('status', 'unavailable')}",
    ]
    doc_coverage = root_focus.get("doc_coverage", {})
    lines.extend(
        [
            f"- root path mentioned in docs: {doc_coverage.get('root_path_mentioned', False)}",
            f"- root decls mentioned in docs: {doc_coverage.get('mentioned_root_declaration_count', 0)}/{doc_coverage.get('root_declaration_count', 0)}",
        ]
    )
    witness_audit = root_focus.get("witness_audit", {})
    likely_witness_dirs = witness_audit.get("likely_related_witness_dirs", [])
    if likely_witness_dirs:
        lines.append(
            "- likely witness dirs: "
            + "; ".join(
                f"{item['path']} artifacts={item['artifact_count']} tokens={','.join(item.get('matched_tokens', []))}"
                for item in likely_witness_dirs[:5]
            )
        )
    import_impacts = root_focus.get("direct_import_closure_impacts", {}).get("top_imports", [])
    if import_impacts:
        lines.append("- direct import closure impact:")
        for item in import_impacts[:5]:
            lines.append(
                f"  {item['import']}: modules={item['module_count']} declarations={item['declaration_count']}"
            )
    packet_review = report["summary"].get("packet_review")
    if packet_review:
        lines.extend(
            [
                "",
                "Packet Review Audit",
                f"- status: {packet_review.get('status', 'unavailable')}",
                f"- packet dir: {packet_review.get('packet_dir', '<none>')}",
                f"- source map: {packet_review.get('source_map_status', 'unknown')} entries={packet_review.get('source_map_entry_count', 0)}",
                f"- runtime artifacts: {packet_review.get('runtime_artifact_count', 0)}",
                f"- target separation: {packet_review.get('target_separation_status', 'unknown')}",
                f"- authority targets: {', '.join(packet_review.get('authority_targets', [])) or '<none>'}",
                f"- background targets: {', '.join(packet_review.get('background_targets', [])) or '<none>'}",
                f"- runtime targets: {', '.join(packet_review.get('runtime_targets', [])) or '<none>'}",
                f"- packet/repo drift entries: {packet_review.get('packet_repo_drift_count', 0)}",
                f"- packet findings: {packet_review.get('finding_count', 0)}",
            ]
        )
    for finding in root_focus.get("root_findings", [])[:8]:
        lines.append(
            f"- [{finding['severity']}/{finding['confidence']}/{finding['scope']}] {finding['title']}"
        )
    skeleton_families = root_focus.get("proof_skeleton_families", {})
    if skeleton_families.get("family_count", 0):
        lines.append(f"- near-duplicate root proof skeleton families: {skeleton_families['family_count']}")
        for family in skeleton_families.get("families", [])[:3]:
            names = [decl["full_name"].split(".")[-1] for decl in family["declarations"][:6]]
            lines.append(f"  family size={family['family_size']} declarations={','.join(names)}")
    diff_focus = report["summary"].get("diff_focus")
    if diff_focus is not None:
        lines.extend([
            "",
            "Diff-Focused Review",
            f"- status: {diff_focus.get('status')}",
            f"- base: {diff_focus.get('base')}",
        ])
        if diff_focus.get("status") == "failed":
            lines.append(f"- error: {diff_focus.get('error', '<unknown>')}")
        else:
            lines.extend([
                f"- changed paths: {diff_focus.get('changed_path_count', 0)}",
                f"- changed root declarations: {diff_focus.get('changed_root_declaration_count', 0)}",
                f"- changed findings: {diff_focus.get('changed_finding_count', 0)}",
            ])
            if diff_focus.get("changed_paths"):
                lines.append(f"- changed path sample: {list_preview(diff_focus['changed_paths'], limit=8)}")
            for decl in diff_focus.get("changed_root_declarations", [])[:8]:
                lines.append(
                    f"- root decl {decl['status']}: {decl['full_name']} @ {decl['path']}:{decl['line']}"
                )
            for finding in diff_focus.get("changed_findings", [])[:5]:
                lines.append(
                    f"- changed finding [{finding['severity']}/{finding['scope']}]: {finding['title']}"
                )
    lines.extend([
        "",
        "Analysis Closure Summary",
        f"- scope: {closure_summary['metrics']['scope']}",
        f"- total findings: {closure_summary['findings']['total_findings']}",
    ])
    for severity, count in closure_summary["findings"]["by_severity"].items():
        lines.append(f"- {severity}: {count}")
    lines.extend([
        "",
        "Analysis Closure Metrics",
        f"- modules: {closure_summary['metrics']['module_count']}",
        f"- declarations: {closure_summary['metrics']['declaration_count']}",
        f"- max fan-in: {closure_summary['metrics']['max_module_fan_in']}",
        f"- max file lines: {closure_summary['metrics']['max_module_line_count']}",
        f"- max warning density /100 lines: {closure_summary['metrics']['max_warning_density_per_100_lines']}",
        f"- declarations with body metrics: {closure_summary['metrics']['declarations_with_body_metrics']}",
        f"- max body-tree nodes: {closure_summary['metrics']['max_body_tree_node_count']}",
        f"- max body-tree depth: {closure_summary['metrics']['max_body_tree_depth']}",
        f"- declarations with decision metrics: {closure_summary['metrics']['declarations_with_decision_metrics']}",
        f"- max parser decision complexity: {closure_summary['metrics']['max_parser_decision_complexity']}",
        f"- max parser decision nesting complexity: {closure_summary['metrics']['max_parser_decision_nesting_complexity']}",
        "",
        "Reference Graph",
        f"- scope: {reference_graph_summary['scope']}",
        f"- provenance: {reference_graph_summary['provenance']}",
        f"- candidates: {reference_graph_summary['candidate_count']}",
        f"- resolved edges: {reference_graph_summary['resolved_edge_count']}",
        f"- resolved candidates: {reference_graph_summary['resolved_candidate_count']}",
        f"- unresolved candidates: {reference_graph_summary['unresolved_candidate_count']}",
        f"- resolution ratio: {reference_graph_summary.get('resolution_ratio', 0.0)}",
        f"- confidence limiter: {reference_graph_summary.get('confidence_limiter', False)}",
        "",
        "Proof Graph Reasoning",
        f"- method: {graph_reasoning_summary.get('method', 'unavailable')}",
        f"- ranked DAG status: {graph_reasoning_summary.get('ranked_dag_status', 'unavailable')}",
        f"- semiring reachability status: {graph_reasoning_summary.get('semiring_reachability_status', 'unavailable')}",
        f"- cycle decomposition: {graph_reasoning_summary.get('cycle_decomposition_status', 'unavailable')}",
        f"- root declarations: {graph_reasoning_summary.get('root_declaration_count', 0)}",
        f"- reachable declarations: {graph_reasoning_summary.get('reachable_declaration_count', 0)}",
        f"- unreachable declarations: {graph_reasoning_summary.get('unreachable_declaration_count', 0)}",
        f"- max dependency depth from root: {graph_reasoning_summary.get('max_dependency_depth_from_root', 0)}",
        f"- cyclic components: {graph_reasoning_summary.get('cyclic_component_count', 0)}",
        f"- frontier leaves: {graph_reasoning_summary.get('frontier_leaf_count', 0)}",
        f"- kernel candidates: {graph_reasoning_summary.get('kernel_candidate_count', 0)}",
    ])
    dag_shape = graph_reasoning_summary.get("dag_shape", {})
    if dag_shape:
        lines.extend(
            [
                f"- DAG shape: {dag_shape.get('status', 'unavailable')}",
                f"- DAG entrypoint declarations: {dag_shape.get('entrypoint_declaration_count', 0)}",
                f"- DAG reachable declarations: {dag_shape.get('shape_reachable_declaration_count', 0)}",
                f"- DAG layers: {dag_shape.get('topological_layer_count', 0)} max_rank={dag_shape.get('max_rank', 0)}",
                f"- DAG edge direction: {dag_shape.get('edge_direction_status', 'unavailable')}",
                f"- DAG bottleneck layers: {len(dag_shape.get('bottleneck_layers', []))}",
            ]
        )
        for layer in dag_shape.get("widest_layers", [])[:3]:
            lines.append(
                f"- widest layer rank={layer['rank']} width={layer['width']} modules={','.join(layer.get('sample_modules', []))}"
            )
        for layer in dag_shape.get("bottleneck_layers", [])[:3]:
            lines.append(
                f"- bottleneck layer rank={layer['rank']} width={layer['width']} prev={layer['previous_width']} next={layer['next_width']} samples={','.join(layer.get('sample_declarations', [])[:3])}"
            )
        for sample in dag_shape.get("root_to_frontier_path_samples", [])[:2]:
            lines.append(
                f"- root-to-frontier rank={sample['rank']}: {' -> '.join(sample.get('path', [])[:8])}"
            )
    for candidate in graph_reasoning_summary.get("top_kernel_candidates", [])[:5]:
        lines.append(
            f"- candidate {candidate['full_name']} consumers={candidate['reachable_consumer_count']} deps={candidate['reachable_dependency_count']} depth={candidate['depth_from_root']} score={candidate['score']}"
        )
    for component in graph_reasoning_summary.get("top_cyclic_components", [])[:3]:
        lines.append(
            f"- cyclic component size={component['size']} modules={','.join(component['modules'])} samples={','.join(component['sample_declarations'][:5])}"
        )
    if graph_reasoning_summary.get("top_module_dependency_flows"):
        lines.append("- module dependency flows:")
        for flow in graph_reasoning_summary["top_module_dependency_flows"][:5]:
            lines.append(
                f"  {flow['source_module']} -> {flow['target_module']}: edges={flow['edge_count']}"
            )
    lines.extend([
        "",
        "Deadness Summary",
        f"- scope: {deadness_summary['scope']}",
        f"- aggregated modules: {deadness_summary['aggregated_module_count']}",
        f"- aggregated dead declarations: {deadness_summary['aggregated_dead_declaration_count']}",
        f"- prioritized dead components: {deadness_summary['prioritized_dead_component_count']}",
        f"- prioritized dead declarations: {deadness_summary['prioritized_dead_declaration_count']}",
        f"- suppressed dead components: {deadness_summary['suppressed_dead_component_count']}",
        f"- strong declaration findings: {deadness_summary['strong_dead_declaration_finding_count']}",
        "",
        "Repo Inventory Summary",
        f"- scope: {inventory_summary['metrics']['scope']}",
        f"- total findings: {inventory_summary['findings']['total_findings']}",
    ])
    for severity, count in inventory_summary["findings"]["by_severity"].items():
        lines.append(f"- {severity}: {count}")
    lines.extend([
        "",
        "Repo Inventory Metrics",
        f"- modules: {inventory_summary['metrics']['module_count']}",
        f"- declarations: {inventory_summary['metrics']['declaration_count']}",
        f"- max fan-in: {inventory_summary['metrics']['max_module_fan_in']}",
        f"- max file lines: {inventory_summary['metrics']['max_module_line_count']}",
        f"- max warning density /100 lines: {inventory_summary['metrics']['max_warning_density_per_100_lines']}",
        "",
        "Repo Module DAG",
        f"- status: {'available' if module_dag_summary else 'unavailable'}",
        f"- modules: {module_dag_summary.get('module_count', 0)}",
        f"- edges: {module_dag_summary.get('edge_count', 0)}",
        f"- acyclic: {module_dag_summary.get('acyclic', False)}",
        f"- cyclic components: {module_dag_summary.get('cyclic_component_count', 0)}",
        f"- max rank: {module_dag_summary.get('max_rank', 0)}",
        f"- layers: {module_dag_summary.get('topological_layer_count', 0)}",
        f"- facade modules: {module_dag_summary.get('facade_module_count', 0)}",
        f"- source modules not reachable from chosen roots: {module_dag_summary.get('source_modules_not_reachable_from_chosen_roots_count', 0)}",
        "",
        "Repo Evidence State",
        f"- proof-hole scan clean: {proof_hole_summary.get('clean', False)} holes={proof_hole_summary.get('hole_count', 0)} scanned_files={proof_hole_summary.get('scanned_file_count', 0)}",
        f"- OpenSpec active changes: {openspec_summary.get('active_change_count', 0)} unchecked_changes={openspec_summary.get('unchecked_change_count', 0)} unchecked_tasks={openspec_summary.get('unchecked_task_count', 0)} task_files={openspec_summary.get('task_file_count', 0)}",
        f"- local scripts: {local_scripts_summary.get('script_count', 0)} diagnostic_like={local_scripts_summary.get('diagnostic_like_script_count', 0)} without_artifact_mentions={local_scripts_summary.get('diagnostic_like_without_runtime_artifact_mentions', 0)}",
        f"- git workspace: {git_summary.get('status', 'unavailable')} dirty={git_summary.get('is_dirty')} tracked={git_summary.get('tracked_change_count')} untracked={git_summary.get('untracked_count')}",
        "",
        "Owner Health",
        f"- healthy owners: {owner_health_summary['healthy_owner_count']}",
        f"- umbrella owners: {owner_health_summary['umbrella_owner_count']}",
        "",
        "Certificate Boundary Audit",
        f"- total findings: {certificate_boundary_summary.get('total_findings', 0)}",
        f"- export surface: {certificate_boundary_summary.get('export_surface_verification', {}).get('status', meta.get('export_surface_verification', 'skipped'))}",
        f"- checked declarations: {certificate_boundary_summary.get('export_surface_verification', {}).get('checked_declaration_count', meta.get('export_surface_checked_declarations', 0))}",
        f"- missing declarations: {certificate_boundary_summary.get('export_surface_verification', {}).get('missing_declaration_count', meta.get('export_surface_missing_declarations', 0))}",
    ])
    for category, count in certificate_boundary_summary.get("by_category", {}).items():
        lines.append(f"- {category}: {count}")
    for finding in certificate_boundary_summary.get("top_findings", [])[:5]:
        lines.append(
            f"- {finding['category']}: {finding['title']} @ {', '.join(finding.get('files') or ['<unknown>'])}"
        )
    lines.extend([
        "",
        "Repo Concentration Hotspots",
    ])
    for module in owner_health_summary["healthy_modules"][:3]:
        lines.append(
            f"- ({owner_health_summary['scope']}) healthy {module['module']} fan_in={module['fan_in']} imports={module['import_count']} decls={module['declaration_count']} components={','.join(module['healthy_components'])} @ {module['path']}"
        )
    for module in owner_health_summary["umbrella_modules"][:3]:
        lines.append(
            f"- ({owner_health_summary['scope']}) umbrella {module['module']} fan_in={module['fan_in']} imports={module['import_count']} decls={module['declaration_count']} components={','.join(module['umbrella_components'])} @ {module['path']}"
        )
    lines.extend([
        "",
        "Repo Concentration Hotspots",
    ])
    for module in concentration_summary["top_modules"][:5]:
        lines.append(
            f"- ({module['scope']}) {module['module']} score={module['score']} imports={module['import_count']} fan_out={module['fan_out']} declarations={module['declaration_count']} theorem_ratio={module['theorem_like_ratio']} lines={module['line_count']} @ {module['path']}"
        )
    lines.extend([
        "",
        "Repo Hotspot Scores",
    ])
    for module in hotspot_score_summary["top_modules"][:5]:
        contributor_text = ", ".join(
            f"{item['axis']}:{item['feature']}={item['normalized']:.2f}"
            for item in module["top_contributors"]
        ) or "<none>"
        lines.append(
            f"- ({module['scope']}) {module['module']} severity={module['severity']} score={module['score']:.2f} contributors={contributor_text} @ {module['path']}"
        )
    lines.extend([
        "",
        "Decision Hotspots",
    ])
    for decl in closure_summary["decision_hotspots"]["top_declarations"][:5]:
        lines.append(
            f"- ({decl['scope']}) {decl['full_name']} [{decl['rank']}] decision={decl['decision_complexity']} nesting={decl['nesting_complexity']} @ {decl['path']}:{decl['line']}"
        )
    lines.extend([
        "",
        "Fragility Hotspots",
    ])
    for decl in fragility_summary["top_declarations"][:5]:
        lines.append(
            f"- ({decl['scope']}) {decl['full_name']} fragility={decl['fragility_score']} calibrated={decl['fragility_calibrated_score']} band={decl['fragility_calibrated_band']} families={decl['fragility_signal_family_count']} rw={decl['rw_count']} by_cases={decl['by_cases_count']} calc={decl['calc_step_count']} have={decl['have_count']} simp={decl['simp_like_count']} @ {decl['path']}:{decl['line']}"
        )
    lines.extend([
        "",
        "Deadness Hotspots",
    ])
    for module in deadness_summary["top_modules"][:5]:
        lines.append(
            f"- ({module['scope']}) {module['module']} dead_decls={module['dead_declaration_count']} components={module['dead_component_count']} prioritized_components={module['prioritized_dead_component_count']} suppressed_components={module['suppressed_dead_component_count']} largest_component={module['largest_dead_component_size']} samples={','.join(module['sample_declarations'])} @ {module['path']}"
        )
    lines.extend([
        "",
        "Prioritized Dead Components",
    ])
    for component in deadness_summary["top_components"][:5]:
        lines.append(
            f"- ({component['scope']}) {component['module']} rank={component['priority_rank']} score={component['priority_score']} dead_decls={component['dead_declaration_count']} unresolved={component['unresolved_reference_candidate_count']} samples={','.join(component['sample_declarations'])} @ {component['path']}"
        )
    lines.extend([
        "",
        "Findings",
    ])
    for finding in report["findings"]:
        lines.append(f"- [{finding['severity']}/{finding['confidence']}/{finding['scope']}] {finding['title']}")
        lines.append(f"  category: {finding['category']}")
        if finding["files"]:
            lines.append(f"  files: {', '.join(finding['files'])}")
        if finding["modules"]:
            lines.append(f"  modules: {', '.join(finding['modules'])}")
        if finding["declarations"]:
            lines.append(f"  declarations: {', '.join(finding['declarations'])}")
        lines.append(f"  summary: {finding['summary']}")
        if finding["evidence"]:
            lines.append(f"  evidence: {'; '.join(finding['evidence'])}")
        lines.append(f"  remediation: {finding['remediation']}")
    return "\n".join(lines) + "\n"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    doc_files = args.doc_file or default_doc_files(root)

    extraction = extract_with_parser_helper(root, args)
    modules = extraction.modules
    assign_fan_counts(modules)
    repo_inventory = discover_repo_inventory(root, extraction.analysis_root_file, extraction.analysis_root_module)
    repo_modules = repo_inventory.modules
    assign_fan_counts(repo_modules)

    build_mode, build_command, build_lines = load_build_lines_for_ladon(root, args)
    build_warnings = audit.parse_build_warnings(root, build_lines)
    closure_basenames = {Path(info.path).stem for info in modules.values()}
    doc_module_mentions, doc_path_mentions = audit.parse_doc_mentions(root, doc_files, closure_basenames)
    repo_doc_module_mentions, repo_doc_path_mentions = audit.parse_doc_mentions(
        root,
        doc_files,
        {Path(info.path).stem for info in repo_modules.values()},
    )
    existing_doc_files = {doc for doc in doc_files if (root / doc).exists()}

    repo_base_findings = audit.generate_findings(
        repo_modules,
        build_warnings,
        doc_files,
        repo_doc_module_mentions,
        repo_doc_path_mentions,
        existing_doc_files=existing_doc_files,
    )
    declaration_metrics = extraction.declaration_metrics
    declaration_graph = build_declaration_reference_graph(declaration_metrics)
    closure_module_metrics_payload = module_metrics(root, modules, build_warnings)
    repo_module_metrics_payload = module_metrics(root, repo_modules, build_warnings)
    export_surface, export_findings = verify_export_surface(root=root, extraction=extraction, args=args)
    reachability = add_reachability_findings(
        modules=modules,
        declaration_metrics=declaration_metrics,
        declaration_graph=declaration_graph,
        doc_module_mentions=doc_module_mentions,
        args=args,
        base_findings=[],
    )
    closure_findings = reachability.findings
    closure_findings = add_decision_complexity_findings(declaration_metrics, closure_findings)
    closure_findings = add_fragility_findings(declaration_metrics, closure_findings)
    closure_findings = add_certificate_boundary_findings(
        root=root,
        declaration_metrics=declaration_metrics,
        base_findings=closure_findings,
    )
    closure_findings = add_closure_explosion_findings(
        extraction=extraction,
        modules=modules,
        declaration_metrics=declaration_metrics,
        base_findings=closure_findings,
    )
    closure_findings.extend(export_findings)
    repo_findings = to_ladon_findings(repo_base_findings, scope="repo_inventory")
    repo_findings = add_family_residue_findings(repo_modules, repo_findings)
    repo_findings = add_owner_surface_role_mix_findings(repo_module_metrics_payload, repo_modules, repo_findings)
    repo_findings = add_near_duplicate_structure_findings(root, repo_modules, repo_findings)
    repo_findings = add_repeated_semantic_expression_findings(root, repo_modules, repo_findings)
    repo_findings = add_concentration_findings(repo_module_metrics_payload, repo_findings)
    repo_findings = scan_python_witnesses(root, repo_findings)
    repo_findings = scan_json_witness_artifacts(root, repo_findings)
    repo_findings = lint_certificate_artifacts(root, args, repo_findings)
    packet_review_summary, packet_findings = analyze_packet_review(root, args)
    owner_health = assess_owner_health(repo_module_metrics_payload, repo_findings)
    repo_findings = reinterpret_import_hotspots(owner_health.findings, owner_health.by_module)
    requested_root_modules = sorted(args.reach_root_module)
    requested_root_prefixes = sorted(args.reach_root_prefix)
    requested_excluded_modules = sorted(args.exclude_module)
    requested_excluded_prefixes = sorted(args.exclude_module_prefix)
    resolved_roots = select_reachability_roots(args, modules, doc_module_mentions)
    resolved_exclusions = sorted(select_reachability_exclusions(args, modules))
    git_summary = git_workspace_summary(root)
    module_dag_summary = summarize_module_dag(
        repo_modules,
        resolved_roots=resolved_roots,
        analysis_root_module=extraction.analysis_root_module,
    )
    proof_hole_summary = proof_hole_scan(root, repo_inventory)
    openspec_summary = openspec_backlog_summary(root)
    local_scripts_summary = local_scripts_inventory(root)
    metadata = asdict(
        LadonMetadata(
            tool_name="ladon",
            tool_version=TOOL_VERSION,
            report_version=REPORT_VERSION,
            generated_at_utc=args.generated_at_utc
            or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            repo_root=str(root),
            analysis_root=extraction.analysis_root_file,
            analysis_root_module=extraction.analysis_root_module,
            analysis_closure_files=extraction.analysis_closure_files,
            analysis_closure_modules=extraction.analysis_closure_modules,
            docs=list(doc_files),
            build_mode=build_mode,
            build_command=build_command,
            warning_build_mode=build_mode,
            warning_build_command=build_command,
            extraction_build_verified=True,
            export_surface_verification=export_surface["status"],
            export_surface_command=export_surface["command"],
            export_surface_checked_declarations=export_surface["checked_declaration_count"],
            export_surface_missing_declarations=export_surface["missing_declaration_count"],
            extraction_backend=extraction.backend,
            extraction_provenance=extraction.provenance,
            extraction_policy=extraction.policy,
            extraction_is_degraded=extraction.is_degraded,
            extraction_coverage=asdict(extraction.coverage),
            git_head_sha=git_summary.get("head_sha"),
            git_is_dirty=git_summary.get("is_dirty"),
            git_status_tracked_count=git_summary.get("tracked_change_count"),
            git_status_untracked_count=git_summary.get("untracked_count"),
            repo_inventory_root=repo_inventory.root,
            repo_inventory_files=repo_inventory.files,
            repo_inventory_modules=sorted(repo_modules),
            reachability_root_policy=args.reachability_root_policy,
            reachability_policy_strength=reachability_policy_strength(args),
            reachability_requested_root_modules=requested_root_modules,
            reachability_requested_root_prefixes=requested_root_prefixes,
            reachability_resolved_roots=resolved_roots,
            reachability_exclusion_policy=args.reachability_exclusion_policy,
            reachability_requested_excluded_modules=requested_excluded_modules,
            reachability_requested_excluded_prefixes=requested_excluded_prefixes,
            reachability_resolved_exclusions=resolved_exclusions,
        )
    )
    root_declaration_metrics = summarize_root_declaration_metrics(
        extraction=extraction,
        declaration_metrics=declaration_metrics,
    )
    doc_coverage_summary = summarize_doc_coverage(
        root=root,
        doc_files=doc_files,
        extraction=extraction,
        declaration_metrics=declaration_metrics,
    )
    witness_audit_summary = summarize_witness_audit(
        root=root,
        doc_files=doc_files,
        extraction=extraction,
    )
    direct_import_impacts = direct_import_closure_impacts(
        extraction=extraction,
        modules=modules,
        declaration_metrics=declaration_metrics,
    )
    proof_skeleton_families = summarize_root_proof_skeleton_families(
        extraction=extraction,
        declaration_metrics=declaration_metrics,
    )
    graph_reasoning_summary = summarize_graph_reasoning(
        declaration_metrics=declaration_metrics,
        declaration_graph=declaration_graph,
        root_modules=resolved_roots,
        analysis_root_module=extraction.analysis_root_module,
    )
    reference_graph_summary = summarize_reference_graph(declaration_graph)
    certificate_boundary_summary = summarize_certificate_boundary(
        [*repo_findings, *closure_findings],
        export_surface,
    )
    findings = add_repo_context_findings(
        [*repo_findings, *closure_findings, *packet_findings],
        extraction=extraction,
        root_declarations=root_declaration_metrics,
        direct_import_impacts=direct_import_impacts,
        reference_graph_summary=reference_graph_summary,
        build_mode=build_mode,
        export_surface=export_surface,
        git_summary=git_summary,
        openspec_summary=openspec_summary,
        script_summary=local_scripts_summary,
    )
    repo_findings = [finding for finding in findings if finding.scope == "repo_inventory"]
    closure_findings = [finding for finding in findings if finding.scope == "analysis_closure"]
    root_findings = root_related_findings(findings, extraction)
    root_focus_summary = {
        "scope": "root_focus",
        "analysis_root": extraction.analysis_root_file,
        "analysis_root_module": extraction.analysis_root_module,
        "root_finding_count": len(root_findings),
        "root_findings": [asdict(finding) for finding in root_findings[:20]],
        "root_declarations": root_declaration_metrics,
        "direct_import_closure_impacts": direct_import_impacts,
        "doc_coverage": doc_coverage_summary,
        "witness_audit": witness_audit_summary,
        "proof_skeleton_families": proof_skeleton_families,
    }
    diff_focus_summary = summarize_diff_focus(
        root=root,
        args=args,
        extraction=extraction,
        repo_modules=repo_modules,
        declaration_metrics=declaration_metrics,
        findings=findings,
    )
    summary = {
        "root_focus": root_focus_summary,
        "certificate_boundary": certificate_boundary_summary,
        "analysis_closure": {
            "findings": summarize_findings(closure_findings, scope="analysis_closure"),
            "metrics": summarize_metrics(closure_module_metrics_payload, declaration_metrics),
            "decision_hotspots": summarize_decision_hotspots(declaration_metrics),
            "fragility_hotspots": summarize_fragility_hotspots(declaration_metrics),
            "reference_graph": reference_graph_summary,
            "graph_reasoning": graph_reasoning_summary,
            "deadness_summary": reachability.deadness_summary,
        },
        "repo_inventory": {
            "findings": summarize_findings(repo_findings, scope="repo_inventory"),
            "metrics": summarize_inventory_metrics(repo_module_metrics_payload),
            "module_dag": module_dag_summary,
            "proof_holes": proof_hole_summary,
            "openspec_backlog": openspec_summary,
            "local_scripts": local_scripts_summary,
            "git_workspace": git_summary,
            "concentration_hotspots": summarize_concentration_hotspots(repo_module_metrics_payload),
            "owner_health": owner_health.summary,
            "hotspot_scores": summarize_hotspot_scores(
                repo_module_metrics_payload,
                declaration_metrics,
                reachability.module_deadness,
                owner_health.by_module,
            ),
        },
    }
    if packet_review_summary.get("status") != "unavailable":
        summary["packet_review"] = packet_review_summary
    if diff_focus_summary is not None:
        summary["diff_focus"] = diff_focus_summary
    return {
        "metadata": metadata,
        "declaration_metrics": root_declaration_metrics,
        "metrics": {
            "analysis_closure": {
                "modules": closure_module_metrics_payload,
                "declarations": [asdict(metric) for metric in declaration_metrics],
                "reference_graph": {
                    "scope": declaration_graph["scope"],
                    "provenance": declaration_graph["provenance"],
                    "candidate_count": declaration_graph["candidate_count"],
                    "resolved_edge_count": declaration_graph["resolved_edge_count"],
                    "resolved_candidate_count": declaration_graph["resolved_candidate_count"],
                    "unresolved_candidate_count": declaration_graph["unresolved_candidate_count"],
                    "edges": declaration_graph["edges"],
                    "reverse_edges": declaration_graph["reverse_edges"],
                },
            },
            "repo_inventory": {
                "modules": repo_module_metrics_payload,
                "module_dag": module_dag_summary,
                "proof_holes": proof_hole_summary,
                "openspec_backlog": openspec_summary,
                "local_scripts": local_scripts_summary,
                "git_workspace": git_summary,
            },
        },
        "findings": [asdict(finding) for finding in findings],
        "findings_by_scope": {
            "root_focus": [asdict(finding) for finding in root_findings],
            "analysis_closure": [asdict(finding) for finding in closure_findings],
            "repo_inventory": [asdict(finding) for finding in repo_findings],
        },
        "summary": summary,
    }


def write_outputs(report: dict[str, Any], args: argparse.Namespace) -> None:
    text_payload = render_text(report)
    if args.output_json:
        output_json = Path(args.output_json)
        if not output_json.is_absolute():
            output_json = Path(args.repo_root) / output_json
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    if args.output_text:
        output_text = Path(args.output_text)
        if not output_text.is_absolute():
            output_text = Path(args.repo_root) / output_text
        output_text.parent.mkdir(parents=True, exist_ok=True)
        output_text.write_text(text_payload, encoding="utf-8")
    else:
        print(text_payload, file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        report = build_report(args)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    write_outputs(report, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
