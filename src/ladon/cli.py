"""Command-line orchestration for Ladon's clean core.

The CLI owns user-facing compatibility flags and filesystem orchestration. It
delegates analysis to pure modules so quality gates can keep the core small.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from ladon.pipeline import RunContext, run_pipeline
from ladon.render import write_report


UNSUPPORTED_OPTIONS = {
    "verify_export_surface": "--verify-export-surface",
    "certificate_artifact": "--certificate-artifact",
}


def build_parser() -> argparse.ArgumentParser:
    """Build the clean-core CLI parser.

    Some legacy option names are accepted so users get explicit unsupported
    messages instead of argparse's generic "unknown argument" error.
    """

    parser = argparse.ArgumentParser(description="Ladon clean-core Lean analyzer")
    parser.add_argument("target", nargs="?", help="Optional analysis root alias")
    parser.add_argument("--repo-root", default=".", help="Repository root to analyze")
    parser.add_argument("--root", dest="analysis_root", help="Lean root file or module")
    parser.add_argument("--skip-build", action="store_true", help="Accepted by clean core; no Lake build is run")
    parser.add_argument("--extraction-backend", choices=["text", "lean"], default="text")
    parser.add_argument("--lean-extraction-scope", choices=["root", "inventory"], default="root")
    parser.add_argument("--lean-cache-dir", help="Optional cache directory for Lean helper JSON payloads")
    parser.add_argument("--output-json", "--json", dest="output_json")
    parser.add_argument("--output-text", "--text", dest="output_text")
    parser.add_argument("--generated-at-utc")
    parser.add_argument("--doc-file", action="append", default=[])
    parser.add_argument("--packet-dir", action="append", default=[])
    parser.add_argument("--verify-export-surface", action="store_true")
    parser.add_argument("--certificate-artifact", action="append", default=[])
    return parser


def unsupported_requests(args: argparse.Namespace) -> list[str]:
    """Return requested legacy features not yet rebuilt in the clean core."""

    requested: list[str] = []
    for attr, option in UNSUPPORTED_OPTIONS.items():
        value = getattr(args, attr)
        if value:
            requested.append(option)
    return requested


def selected_root(args: argparse.Namespace) -> str | None:
    """Resolve old positional-root usage and the newer `--root` option."""

    return args.analysis_root or args.target


def main(argv: Sequence[str] | None = None) -> int:
    """Run one clean-core Ladon analysis and return a process status code."""

    parser = build_parser()
    args = parser.parse_args(argv)
    unsupported = unsupported_requests(args)
    if unsupported:
        # Refuse partial reports for old feature flags until they are rebuilt
        # as tested clean-core modules.
        print(
            "unsupported clean-core option(s): " + ", ".join(sorted(unsupported)),
            file=sys.stderr,
        )
        return 2
    try:
        result = run_pipeline(
            RunContext(
                repo_root=Path(args.repo_root),
                requested_root=selected_root(args),
                extraction_backend=args.extraction_backend,
                lean_extraction_scope=args.lean_extraction_scope,
                lean_cache_dir=optional_path(args.lean_cache_dir),
                packet_dirs=tuple(Path(path) for path in args.packet_dir),
                generated_at_utc=args.generated_at_utc,
                warnings=clean_core_warnings(args),
            )
        )
        payload = result.to_report_payload()
        write_report(payload, output_json=args.output_json, output_text=args.output_text)
    except Exception as exc:
        print(f"ladon: {exc}", file=sys.stderr)
        return 1
    return 0


def clean_core_warnings(args: argparse.Namespace) -> list[str]:
    """Collect non-fatal support-boundary warnings for accepted flags."""

    warnings: list[str] = []
    if args.doc_file:
        warnings.append("doc-file audit is not implemented in clean core yet")
    return warnings


def optional_path(value: str | None) -> Path | None:
    """Convert optional path strings at the CLI boundary."""

    return Path(value) if value else None


if __name__ == "__main__":
    raise SystemExit(main())
