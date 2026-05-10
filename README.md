# Ladon

Ladon is a host-side analyzer for Lean projects. The current clean core reads
Lean source text, can optionally ask Lean for root-file declaration candidates,
reports module/declaration graph structure, and keeps Python quality gates
strict enough that analyzer code stays small and testable.

This repository is the shared home for Ladon. Downstream projects such as
`matrix-factorization` and `quux` should call this tool instead of carrying
their own copies.

## Usage

From this repository:

```bash
uv run ladon --repo-root /path/to/lean/project --root Some/Owner.lean --skip-build \
  --output-json /tmp/ladon-report.json --output-text /tmp/ladon-report.txt
```

Lean-backed root declaration graph:

```bash
uv run ladon --repo-root /path/to/lean/project --root Some/Owner.lean \
  --extraction-backend lean --lean-extraction-scope root \
  --lean-cache-dir /tmp/ladon-lean-cache \
  --output-json /tmp/ladon-declarations.json --output-text /tmp/ladon-declarations.txt
```

The clean core does not invoke Lake for `--skip-build` module-DAG smoke runs.
The Lean backend shells out through the target repo's Lake/Lean toolchain. The
cache stores helper JSON payloads by source/helper content for repeated root
runs; it is not a sound incremental cache for indirect import changes.

```bash
cd <target-repo>
lake env lean --run /home/codex/projects/ladon/src/ladon/lean/ladon_parser_helper.lean -- <target-file>
```

## Current State

Ladon is now a clean Python-first seed, not a copy of the old
`matrix-factorization` monolith.

Supported today:

- text-based Lean module discovery under a selected root namespace;
- optional Lean parser-helper extraction for root-file declaration candidates;
- pure module-DAG analysis through `ladon.analysis.module_dag`;
- pure declaration graph analysis through `ladon.analysis.declaration_graph`;
- root-focused findings for module fan-in, root import closure, declaration
  fan-in/fan-out, and unresolved-reference hotspots;
- unresolved-reference classification into local/field, external, parser-noise,
  known-inventory, and actionable-unknown classes;
- declaration-name family grouping for repeated theorem-shape suffixes;
- phase timing and Lean helper cache counters in JSON reports;
- JSON and text reports;
- strict Python quality gate with no active C-or-worse radon findings.

Not yet reintroduced:

- packet-review internals;
- export-surface freshness checks;
- witness audits;
- elaborated proof dependency extraction.

Unsupported legacy flags fail explicitly rather than emitting partial reports.

Near-term work:

- improve declaration-reference resolution beyond string classification;
- reintroduce witness audit and packet audit as small TDD-backed modules;
- only port stable hot paths after profiling proves they are worth moving.

## Python Quality Audits

Run the project-local quality command from this repository:

```bash
uv run python scripts/python_quality.py
```

This runs:

- `radon cc` and `radon mi` as complexity/maintainability reports;
- `vulture` as the high-confidence dead-code scan.

Strict mode is the gate used for implementation work:

```bash
uv run python scripts/python_quality.py --strict
```

Strict mode fails on active C-or-worse radon blocks, C-grade maintainability,
high-confidence vulture findings, compile failures, or test failures. Treat
that as a design constraint: split analyzer behavior into small modules before
adding more heuristics.
