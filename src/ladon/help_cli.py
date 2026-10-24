"""Compact installed help, with a parser-derived catalog available on request."""

from __future__ import annotations

from collections.abc import Sequence

COMMON_HELP = """\
usage: ladon COMMAND [OPTIONS]
       ladon --repo-root REPO --root MODULE [OPTIONS]

Find reusable Lean theorems, check applications, and inspect proof architecture.

Common commands (append --help for exact options):
  proof-search index status       Check index freshness and coverage.
  proof-search index build        Create or replace the lexical index.
  proof-search index update       Refresh changed lexical sources.
  proof-search search name        Find declarations by name.
  proof-search search type-text   Find declarations by proposition text.
  proof-search discover           Check candidates against a goal and local hypotheses.
  proof-search check candidate    Check one candidate against a closed goal.
  proof-search goal capture       Capture the context of an actual source goal.
  proof-search goal complete      Check a proof term against a captured goal.
  theorem lineage                Inspect compiled proof dependencies.
  preview                        Preview analysis scope and costs.
  result inspect                 Inspect saved result evidence.
  version                        Report installed version and source identity.
  doctor                         Check installation and repository readiness.

Type-text search is lexical; use explicit Lean checks to assess applications.
Analyze module architecture: ladon --repo-root REPO --root MODULE

  -h, --help                     Show this compact guide.
  -h --verbose                   Show all commands and analyzer options.
  --version                      Show a one-line version.

For less common commands, run 'ladon -h --verbose'.
For command options, run e.g. 'ladon proof-search discover --help'.
"""


DIAGNOSTIC_HELP = {
    "version": """\
usage: ladon version [--json]

Report installed version and source identity as JSON.
Use 'ladon --version' for a one-line version.
""",
    "doctor": """\
usage: ladon doctor [--json] [--repo-root PATH] [--require-isolation]

Check installation and repository readiness without running Lean.
  --json                Emit structured diagnostics.
  --repo-root PATH      Repository to inspect (defaults to the current directory).
  --require-isolation   Report whether the target isolation policy is satisfied.
""",
}


def dispatch_help(arguments: Sequence[str]) -> int | None:
    """Handle root help and the two diagnostic commands without argparse parsers."""
    if len(arguments) == 2 and arguments[0] in DIAGNOSTIC_HELP and arguments[1] in {"-h", "--help"}:
        print(DIAGNOSTIC_HELP[arguments[0]], end="")
        return 0
    flags = set(arguments)
    if not flags.intersection({"-h", "--help"}):
        return None
    if not flags <= {"-h", "--help", "--verbose"}:
        return None
    print(verbose_help() if "--verbose" in flags else COMMON_HELP, end="")
    return 0


def verbose_help() -> str:
    """Enumerate the live parser trees without running command handlers."""
    from ladon.cli import build_parser as analyzer_parser
    from ladon.investigation_cli import _investigation_parser
    from ladon.proof_contract_cli import _parser as contract_parser
    from ladon.proof_search_cli import build_proof_search_parser
    from ladon.proofir_v3_cli import build_parser as proofir_parser
    from ladon.reportset_cli import build_reportset_parser
    from ladon.result_cli import _parser as result_parser
    from ladon.runset_cli import build_runset_parser
    from ladon.theorem_cli import build_theorem_parser

    lines = [
        "usage: ladon COMMAND [OPTIONS]",
        "       ladon --repo-root REPO --root MODULE [OPTIONS]",
        "",
        "All commands (append --help to a command path for its options):",
        "  version [--json]  Report installed version and source identity.",
        "  doctor [--json] [--repo-root PATH] [--require-isolation]",
        "    Check installation and repository readiness without running Lean.",
    ]
    families = (
        ("proof-search", build_proof_search_parser()),
        ("theorem", build_theorem_parser()),
        ("result", result_parser()),
        ("proofir", proofir_parser()),
        ("investigation", _investigation_parser()),
        ("runset", build_runset_parser()),
    )
    # Investigation dispatches contract before parsing its placeholder. Expand
    # that delegated parser too, so the catalog includes its real subcommands.
    overrides = {("investigation", "contract"): contract_parser()}
    for name, parser in families:
        lines.append(f"  {name}" + _description(parser.description))
        lines.extend(_command_lines(parser, (name,), overrides))
    lines.extend(_command_lines(build_reportset_parser(), (), overrides))
    lines.extend(
        [
            "",
            "Global help: -h / --help (compact), -h --verbose (this catalog).",
            "Version shortcut: --version. Use 'ladon -h' for the common workflows.",
            "",
            "Analyzer options:",
        ]
    )
    parser = analyzer_parser()
    parser.prog = "ladon"
    parser.epilog = None  # The live command catalog above replaces the static epilog.
    return "\n".join(lines) + "\n" + parser.format_help()


def _description(value: str | None) -> str:
    return "  " + " ".join(value.split()) if value else ""


def _command_lines(parser, prefix, overrides) -> list[str]:
    import argparse

    lines = []
    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            continue
        descriptions = {item.dest: item.help for item in action._choices_actions}
        for name, child in action.choices.items():
            path = (*prefix, name)
            child = overrides.get(path, child)
            description = descriptions.get(name) or child.description
            lines.append("  " + " ".join(path) + _description(description))
            lines.extend(_command_lines(child, path, overrides))
    return lines
