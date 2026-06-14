# Ladon is an experimental Lean codebase quality tool, e.g. "radon" for Lean.

Ladon is a host-side analyzer for Lean projects. The current clean core reads
Lean source text, can optionally ask Lean for root-file declaration candidates,
reports module/declaration graph structure, and keeps Python quality gates
strict enough that analyzer code stays small and testable.

Ladon is not a proof checker. Declaration edges, source ranges, source hashes,
packet diagnostics, and optional ProofIR bridge joins are review-routing
evidence only. Theorem truth and proof correctness must come from Lean or an
explicit external artifact with its own authority and hash.

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

Very experimental.

Supported today:

- text-based Lean module discovery under a selected root namespace;
- optional Lean parser-helper extraction for root-file declaration candidates;
- pure module-DAG analysis through `ladon.analysis.module_dag`;
- pure declaration graph analysis through `ladon.analysis.declaration_graph`;
- additive `declaration_graph.declarations` rows with source path/range/hash,
  extraction backend/version, name-resolution method, and confidence when the
  Lean helper supplies that evidence;
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

Optional bridge:

- `ladon-proofir-bridge` can join an existing Ladon JSON report with a compact
  ProofIR bridge index and emit reviewer cards/diagnostics.  This is separate
  from core Ladon analysis and does not make Ladon a proof checker.
- when compact ProofIR inputs include route-authority fields, Ladon can audit
  whether a claim's advertised authority matches its evidence route. For
  example, it can flag a Lean-closed claim whose required finite-window evidence
  is still imported interval-certified, or an arbitrary-neighbor public claim
  whose primary theorem surface is sampled/null only.

Atlas workflow:

- `scripts/ladon_atlas_export.py` builds canonical atlas JSON plus optional
  Markdown, SQLite, and reviewer-card outputs from a report directory.
- `scripts/ladon_atlas_workflow.py` derives a reviewer workflow from atlas JSON,
  an optional earlier atlas, and optional ProofIR bridge reports. It summarizes
  changed rows, recurring hotspots, review-priority roots, low-confidence joins,
  and incomplete or stale evidence.

Unsupported legacy flags fail explicitly rather than emitting partial reports.

Near-term work:

- make claim authority route auditing the priority review surface: claimed
  status vs required evidence authority, endpoint-scope overclaim, missing
  primary theorem surfaces, and warning-only conditional-signature hints;
- improve declaration-reference resolution beyond string classification;
- reintroduce witness audit and packet audit as small TDD-backed modules;
- only port stable hot paths after profiling proves they are worth moving.

## Internal Python quality audits of Ladon

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

## LLM Disclaimer

This is close to 100% AI assisted code. Much of it is even "vibe-coded", i.e. not looking at the generated code. This is evolved on the side when developing some experimental Lean code and trying to keep the codebase clean.
