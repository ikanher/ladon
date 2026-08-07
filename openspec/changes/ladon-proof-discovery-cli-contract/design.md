## Context

The canonical CLI already owns output selection, report versions, no-build defaults,
and exit taxonomy, but maintained examples still mention removed compatibility flags.
Later children need a stable proof-search command surface before adding query types.

## Goals / Non-Goals

**Goals:** provide one installed `proof-search` family, synchronize maintained docs
and skills with `--help`, and gate examples from the installed wheel.

**Non-Goals:** no separate model API, editor-only command, hidden rebuild, or return
to dual-output compatibility flags.

## Decisions

- Make proof search a subcommand family under the installed `ladon` executable and
  reuse canonical `--format`, `--output`, `--report-version`, stream, and exit rules.
- Generate/test maintained examples against parser help and use docs tests to reject
  removed `--skip-build`, `--output-json`, and `--output-text` forms.
- Keep architecture analysis and compact proof-search rendering as separate modes
  over shared underlying authorities.
- Treat the Codex skill as maintained distribution content and test its examples
  against an installed candidate, not merely the source checkout.

## Risks / Trade-offs

- [Docs drift again] → Add installed-help/example conformance tests.
- [New commands bypass shared exits] → Route through existing CLI services and gate
  invocation, operational, policy, and signal cases.

## Migration Plan

Replace stale examples in one release; errors for removed flags retain actionable
migration text. Rollback removes proof-search commands without changing analyzer
defaults.
