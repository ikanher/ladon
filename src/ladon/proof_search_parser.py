"""Proof-search command parsing, separate from operation execution."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from ladon.proof_search_discovery_cli import register_discover_parser
from ladon.proof_search_goal_cli import register_goal_parser
from ladon.proof_search_index import (
    DEFAULT_MAX_INDEX_BYTES,
    SUPPORTED_INDEX_SCOPES,
    ProofSearchIndexError,
)
from ladon.proof_search_semantic_cli import (
    add_semantic_output_options,
    add_semantic_registry_options,
    add_target_execution_options,
)
from ladon.resource_limits import DEFAULT_MAX_RSS_MIB


class ProofSearchArgumentParser(argparse.ArgumentParser):
    """Convert parser failures into the ordinary callable CLI contract."""

    def error(self, message: str) -> None:
        raise ProofSearchIndexError(message)


def build_proof_search_parser(*, evidence_kinds: Sequence[str]) -> argparse.ArgumentParser:
    """Build the caller-neutral proof-search command tree."""

    parser = ProofSearchArgumentParser(
        prog="ladon proof-search",
        description="Build and query local Lean proof-navigation evidence.",
    )
    operations = parser.add_subparsers(dest="proof_search_operation", required=True)
    proof = operations.add_parser("proof", help="Extract source-bound elaborated proof applications.")
    proof_commands = proof.add_subparsers(dest="proof_operation", required=True)
    proof_commands.add_parser("slice", help="Use 'proof slice --help' for the bounded extraction contract.")
    index = operations.add_parser(
        "index",
        help="Build, inspect, or query the persistent local index.",
    )
    commands = index.add_subparsers(dest="index_operation", required=True)

    build = commands.add_parser("build", help="Atomically build or replace the index.")
    _add_repository_options(build)
    _add_output_options(build)
    build.add_argument(
        "--max-index-mib",
        type=_positive_integer,
        default=DEFAULT_MAX_INDEX_BYTES // (1024 * 1024),
        help="Maximum database size in MiB; defaults to 1024.",
    )

    update = commands.add_parser("update", help="Explicitly refresh changed lexical modules.")
    _add_repository_options(update)
    _add_output_options(update)
    update.add_argument("--max-history-mib", type=_positive_integer)

    history = commands.add_parser("history", help="List preserved evidence snapshots.")
    _add_repository_options(history)
    _add_output_options(history)
    history.add_argument("--limit", type=_positive_integer, default=100)
    history.add_argument("--offset", type=int, default=0)

    status = commands.add_parser("status", help="Inspect index identity and freshness.")
    _add_repository_options(status)
    _add_output_options(status)
    status.add_argument(
        "--no-verify-sources",
        action="store_true",
        help="Read stored metadata without hashing current source/configuration bytes.",
    )
    listing = commands.add_parser("list", help="Inventory local index files and protected state.")
    _add_repository_options(listing)
    _add_output_options(listing)
    listing.add_argument("--directory", type=Path)
    listing.add_argument("--limit", type=_positive_integer, default=1000)

    prune = commands.add_parser("prune", help="Preview or apply selected private-index cleanup.")
    _add_repository_options(prune)
    _add_output_options(prune)
    prune.add_argument("--directory", type=Path)
    prune.add_argument("--select", action="append", default=[])
    prune.add_argument("--keep", action="append", default=[])
    prune.add_argument("--older-than-days", type=float)
    prune.add_argument("--apply", action="store_true")
    prune.add_argument("--preview-file", type=Path)
    status.add_argument(
        "--changed", action="store_true",
        help="List up to 1000 added, changed and removed supported source modules.",
    )
    status.add_argument(
        "--details", action="store_true",
        help="Expand the detailed index, schema and storage inventory in text output.",
    )

    query = commands.add_parser("query", help="Run a bounded declaration query.")
    _add_repository_options(query)
    _add_output_options(query)
    query.add_argument("--text", help="Literal name or lexical-signature substring.")
    query.add_argument(
        "--query-mode",
        choices=("all", "any", "phrase"),
        default="all",
        help="Boolean semantics for segmented name terms.",
    )
    query.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Folded name substring to exclude; repeatable.",
    )
    query.add_argument(
        "--scope",
        choices=sorted(SUPPORTED_INDEX_SCOPES),
        default="repository",
        help="Explicit candidate population; repository is the default.",
    )
    evidence = operations.add_parser("evidence", help="Query stored ProofIR evidence.")
    _add_repository_options(evidence)
    _add_output_options(evidence)
    evidence.add_argument(
        "kind",
        choices=evidence_kinds,
    )
    evidence.add_argument("name")
    evidence.add_argument("--start")
    evidence.add_argument("--end")
    evidence.add_argument("--limit", type=_bounded_limit, default=100)
    evidence.add_argument(
        "--local-id",
        help="Typed local ID required by semantic-check evidence expansion.",
    )
    add_semantic_registry_options(evidence, _positive_integer)
    query.add_argument(
        "--root",
        action="append",
        default=[],
        help="Module, namespace, or file root required by the selected scope.",
    )
    query.add_argument(
        "--limit",
        type=_bounded_limit,
        default=20,
        help="Maximum rows returned, between 1 and 1000.",
    )
    query.add_argument("--min-matched-segments", type=_positive_integer, default=1)
    search = operations.add_parser("search", help="Run the versioned name-search contract.")
    search_commands = search.add_subparsers(dest="search_operation", required=True)
    name = search_commands.add_parser("name", help="Search declarations by normalized name.")
    _add_repository_options(name)
    _add_output_options(name)
    name.add_argument("--text", required=True)
    name.add_argument("--query-mode", choices=("all", "any", "phrase"), default="all")
    name.add_argument("--exclude", action="append", default=[])
    name.add_argument("--scope", choices=sorted(SUPPORTED_INDEX_SCOPES), default="repository")
    name.add_argument("--root", action="append", default=[])
    name.add_argument("--limit", type=_bounded_limit, default=20)
    name.add_argument("--min-matched-segments", type=_positive_integer, default=1)
    name.add_argument("--freshness", choices=("verify", "stored"), default="verify")
    type_search = search_commands.add_parser(
        "type-text", help="Search declaration type text (lexical shortlist)."
    )
    _add_repository_options(type_search)
    _add_output_options(type_search)
    type_search.add_argument("--pattern", required=True)
    type_search.add_argument("--module")
    type_search.add_argument("--namespace")
    type_search.add_argument("--package")
    type_search.add_argument(
        "--scope", choices=sorted(SUPPORTED_INDEX_SCOPES), default="repository"
    )
    type_search.add_argument("--root", action="append", default=[])
    type_search.add_argument("--limit", type=_bounded_limit, default=20)
    type_search.add_argument("--diagnostic-limit", type=_diagnostic_limit, default=0)
    type_search.add_argument("--freshness", choices=("verify", "stored"), default="stored")
    explain = operations.add_parser("explain", help="Compare one indexed candidate type with a goal (structural evidence only).")
    _add_repository_options(explain)
    _add_output_options(explain)
    explain.add_argument("--goal", required=True)
    explain.add_argument("--candidate", required=True)
    explain.add_argument("--module", help="Restrict exact candidate lookup to this owning module.")
    explain.add_argument("--assumption", action="append", default=[])
    explain.add_argument("--suggestion-cap", type=_bounded_limit, default=10)
    explain.add_argument("--freshness", choices=("verify", "stored"), default="stored")
    explain.add_argument("--check-artifact", help="Explicit stored check artifact supplying the candidate type.")
    explain.add_argument("--check-local-id", help="Artifact-qualified check-run local ID.")
    add_semantic_registry_options(explain, _positive_integer)
    explain.add_argument(
        "--raw-signature",
        action="store_true",
        help="Use compatibility raw-signature comparison without binder normalization.",
    )
    register_discover_parser(
        operations,
        _add_repository_options,
        _add_output_options,
        lambda parser: add_semantic_output_options(parser, _positive_integer),
        _bounded_limit,
        _positive_integer,
        SUPPORTED_INDEX_SCOPES,
    )
    consumers = operations.add_parser("consumers", help="Find bounded declaration consumers.")
    _add_repository_options(consumers)
    _add_output_options(consumers)
    consumers.add_argument("--declaration", required=True)
    consumers.add_argument("--kind", choices=("all", "type", "value"), default="all")
    consumers.add_argument("--ownership", choices=("all", "project", "external"), default="all")
    consumers.add_argument("--limit", type=_bounded_limit, default=100)
    constructor = operations.add_parser(
        "constructor", help="Inspect bounded constructor field coverage."
    )
    _add_repository_options(constructor)
    _add_output_options(constructor)
    constructor.add_argument("--structure", required=True)
    constructor.add_argument("--module")
    constructor.add_argument("--argument", action="append", default=[])
    constructor.add_argument("--limit", type=_bounded_limit, default=100)
    constructor.add_argument("--freshness", choices=("verify", "stored"), default="stored")
    register_goal_parser(operations, _add_repository_options, _add_output_options)
    check = operations.add_parser("check", help="Run an explicit bounded Lean checker operation.")
    check_commands = check.add_subparsers(dest="check_operation", required=True)
    candidate = check_commands.add_parser(
        "candidate",
        help="Check one closed candidate against one exact goal.",
        description=(
            "Load one trusted target module with direct Lean and existing compiled .olean "
            "roots; Ladon does not reconcile Lake dependencies. Target initializers may run."
        ),
    )
    _add_repository_options(candidate)
    _add_output_options(candidate)
    add_semantic_output_options(candidate, _positive_integer)
    add_target_execution_options(candidate)
    candidate.add_argument("--module", required=True)
    candidate.add_argument("--goal", required=True)
    candidate.add_argument("--candidate", required=True)
    candidate.add_argument("--timeout-seconds", type=float, default=120.0)
    candidate.add_argument("--max-output-mib", type=_positive_integer, default=8)
    candidate.add_argument("--max-rss-mib", type=_positive_integer, default=DEFAULT_MAX_RSS_MIB)
    candidate.add_argument(
        "--toolchain-mode",
        choices=("ambient", "explicit"),
        default="ambient",
        help="Select ambient discovery (non-authoritative) or explicit pinned executables.",
    )
    candidate.add_argument("--lake-path", type=Path)
    candidate.add_argument("--lean-path", type=Path)

    source = check_commands.add_parser(
        "source",
        help="Associate a fresh source observation with one exact compiled owner.",
        description=(
            "Observe source and compiled coherence using scratch outputs. "
            "This operation does not run the candidate checker."
        ),
    )
    _add_repository_options(source)
    _add_output_options(source)
    add_target_execution_options(source)
    source.add_argument("--module", required=True)
    source.add_argument("--source", dest="source_path", required=True)
    source.add_argument("--candidate", required=True)
    source.add_argument("--subject-artifact", required=True)
    source.add_argument("--artifact", type=Path, action="append", default=[])
    source.add_argument("--setup", dest="setup_path", type=Path)
    source.add_argument("--timeout-seconds", type=float, default=120.0)
    source.add_argument("--max-output-mib", type=_positive_integer, default=8)
    source.add_argument("--max-rss-mib", type=_positive_integer, default=DEFAULT_MAX_RSS_MIB)
    source.add_argument(
        "--toolchain-mode",
        choices=("explicit",),
        default="explicit",
        help="Source association requires pinned explicit Lean and Lake executables.",
    )
    source.add_argument("--lake-path", type=Path, required=True)
    source.add_argument("--lean-path", type=Path, required=True)
    return parser


def _add_repository_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Lean repository owning the index.",
    )
    parser.add_argument(
        "--index",
        dest="index_path",
        help="Override the default <repo>/.ladon/index/proof-search.sqlite path.",
    )


def _add_output_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=("text", "json"),
        default="text",
        help="Result representation.",
    )
    parser.add_argument(
        "--output",
        default="-",
        help="Result path, or - for standard output.",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Write bounded JSON progress records to standard error.",
    )


def _diagnostic_limit(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("diagnostic limit must be an integer") from exc
    if not 0 <= parsed <= 1000:
        raise argparse.ArgumentTypeError("diagnostic limit must be between 0 and 1000")
    return parsed


def _bounded_limit(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("limit must be an integer") from exc
    if parsed < 1 or parsed > 1000:
        raise argparse.ArgumentTypeError("limit must be between 1 and 1000")
    return parsed


def _positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed

