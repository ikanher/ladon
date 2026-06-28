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

Project-specific architecture boundary policy:

```bash
uv run ladon --repo-root /path/to/lean/project --root Some/Owner.lean --skip-build \
  --architecture-policy docs/ladon-architecture-policy.json \
  --output-json /tmp/ladon-report.json --output-text /tmp/ladon-report.txt
```

Architecture policies are JSON files that define module groups with glob
patterns and rules between those groups. Ladon does not hard-code project
families such as samplers, kernels, bridges, or generated modules; the target
project supplies those names and exclusions.
See `docs/policies/architecture-policy.example.json` for a generic starting
point.

If `--architecture-policy` is omitted, Ladon looks for these repo-local files:

- `.ladon/architecture-policy.json`
- `ladon.architecture.json`
- `ladon-architecture-policy.json`

When no policy is found, Ladon emits an
`architecture_policy.skipped_no_policy` info finding and may include a
draft-policy suggestion derived from repeated module-name prefixes with
cross-prefix imports. Draft suggestions are review prompts only; they are not
enforced rules.

Project-specific source pattern policy:

```bash
uv run ladon --repo-root /path/to/lean/project --root Some/Owner.lean --skip-build \
  --source-pattern-policy docs/ladon-source-pattern-policy.json \
  --output-json /tmp/ladon-report.json --output-text /tmp/ladon-report.txt
```

Source-pattern policies are JSON files with project-owned pattern rows:

```json
{
  "id": "local-source-audit",
  "patterns": [
    {
      "id": "stale-term",
      "pattern": "OldProjectTerm",
      "kind": "stale_term",
      "severity": "warning",
      "excludeGenerated": true
    }
  ]
}
```

Patterns are plain substring searches by default. Set `"regex": true` for a
regular expression, `"caseSensitive": false` for case-insensitive matching, and
`"maxMatches"` to cap reported rows per pattern. Ladon does not hard-code stale
terms, trust words, or project conventions; the target repository supplies
those names. If `--source-pattern-policy` is omitted, Ladon looks for
`.ladon/source-pattern-policy.json`, `.ladon/source-patterns.json`,
`ladon.source-patterns.json`, or `ladon-source-pattern-policy.json`.
See `docs/policies/source-pattern-policy.example.json` for a generic starting
point.

## Current State

Very experimental.

Supported today:

- text-based Lean module discovery under a selected root namespace;
- optional Lean parser-helper extraction for root-file declaration candidates;
- pure module-DAG analysis through `ladon.analysis.module_dag`;
- optional project-supplied architecture policy checks over the module DAG,
  including forbidden direct imports, optional transitive witness paths, and
  shared-dependency extraction candidates;
- line-level import evidence for text-backed architecture policy findings;
- policy text summaries for direct group pairs, top offending files, and ranked
  common-layer candidates while full edge/path detail remains in JSON;
- common-layer candidate modes for either policy-target-only scanning or all
  multi-group imports via `sharedDependencyMode: "all_multi_group_imports"`;
- policy finding triage context for direct imports, including configurable
  bridge/facade/core-looking classification and fix-oriented suggested actions;
- duplicate import detection with line-level evidence, while graph edges remain
  deduplicated, including generated-family attribution when files look
  generated;
- source-level module metadata, including line counts and generic generated-code
  tags inferred from common file/path/comment conventions;
- generated-aware fan-in/fan-out, facade/barrel fan-out, implementation fan-out,
  and largest-handwritten-module report rows so generated modules and public
  barrels do not hide owner-file architecture pressure;
- facade-like module subtype rows for pure barrels, generated `All` barrels,
  public root facades, and mixed barrel/theorem modules;
- lightweight lexical and import-target smell rows for anchored
  `sorry`/`admit`/`axiom`, TODO/FIXME, and missing internal import targets;
- optional project-supplied source-pattern scans for stale terms, local trust
  words, or other project conventions, with source locations and generated-code
  filtering when configured;
- pure declaration graph analysis through `ladon.analysis.declaration_graph`;
- additive `declaration_graph.declarations` rows with source path/range/hash,
  extraction backend/version, name-resolution method, and confidence when the
  Lean helper supplies that evidence;
- root-focused findings for module fan-in, handwritten module fan-in, root
  import closure, duplicate imports, large handwritten modules, declaration
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
