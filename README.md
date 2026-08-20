# Ladon is an experimental Lean codebase quality tool, e.g. "radon" for Lean.

Ladon is a host-side analyzer for Lean projects. The current clean core reads
Lean source text, can optionally ask Lean for root-file declaration candidates,
reports module/declaration graph structure, and keeps Python quality gates
strict enough that analyzer code stays small and testable.

Ladon is not a proof checker. Declaration edges, source ranges, source hashes,
packet diagnostics, and native ProofIR v3 projections are review-routing
evidence only. Theorem truth and proof correctness must come from Lean or an
explicit check-run observation naming its checker and exact environment.

The near-term supported product is deliberately narrow: architecture review,
semantic declaration discovery with explicit candidate checks, and stored
evidence/theorem-lineage inspection. Atlas, runset/reportset, theorem-capsule,
and bridge surfaces are optional layers. See [Product scope](docs/PRODUCT_SCOPE.md)
and the generated [supported-feature matrix](docs/SUPPORTED_FEATURE_MATRIX.md).

## Setup and support

Ladon currently supports CPython 3.11 and 3.12. Create the project environment
from the committed lock without re-resolving dependencies:

```bash
uv lock --check
uv sync --locked
```

The required CI matrix tests both supported Python minors. Its Lean integration
fixture pins Lean 4.32.1 as a reference compatibility target; normal analysis
uses the target repository's own `lean-toolchain` and Lake environment.

See [Reproducibility and release support](docs/REPRODUCIBILITY.md) for the
tracked-input boundary, required gates, optional external smokes, execution
risk, and publication status.
See [Portable signal benchmarks](docs/BENCHMARKS.md) for the installed-CLI
correctness, coverage, resource, cache, process, and report-stability gate.
See [Report contract v3](docs/REPORT_CONTRACT_V3.md) for canonical payload
ownership, projections, fingerprints, and bounded JSON serialization.
See [Theorem capsules](docs/THEOREM_CAPSULES.md) for exact theorem planning,
module-prefix packaging, clean-room Lean replay, and the guarantee boundary.

## Usage

From this repository:

```bash
uv run --locked ladon --repo-root /path/to/lean/project --root Some/Owner.lean \
  --format json --output /tmp/ladon-report.json
```

One analysis can render both ordinary representations from the same immutable
snapshot decision:

```bash
uv run --locked ladon --repo-root /path/to/lean/project --root Some/Owner.lean \
  --emit json=/tmp/ladon-report.json \
  --emit text=/tmp/ladon-report.txt
```

`--emit` is repeatable and cannot be mixed with `--format`, `--output`, or the
deprecated `--json`/`--text` file flags. Formats and normalized destinations
must be unique, and at most one destination may be `-`.

Lean-backed root declaration graph:

```bash
uv run --locked ladon --repo-root /path/to/lean/project --root Some/Owner.lean \
  --extraction-backend lean --lean-extraction-scope root \
  --lean-cache-dir /tmp/ladon-lean-cache \
  --format json --output /tmp/ladon-declarations.json
```

The clean core does not invoke Lake during default module-DAG smoke runs.
Building is opt-in with `--build`; the removed `--skip-build` flag is replaced
by simply omitting `--build`.
The Lean backend shells out through the target repo's Lake/Lean toolchain. The
cache stores helper JSON payloads by source/helper content for repeated root
runs; it is not a sound incremental cache for indirect import changes. Loading
target modules can execute imported initializers, so the Lean backend is not a
safe way to analyze an untrusted repository.

Build the repository-local proof-navigation index explicitly:

```bash
uv run --locked ladon proof-search index build \
  --repo-root /path/to/lean/project \
  --format json --output -

uv run --locked ladon proof-search index query \
  --repo-root /path/to/lean/project \
  --text integrable --scope repository --limit 20
```

The default database is `.ladon/index/proof-search.sqlite`. The directory is
disposable generated state and should be ignored by version control. Use
`--index PATH` for a read-only checkout or CI-owned location. Version one
contains project-owned lexical declaration and import navigation with explicit
coverage gaps for elaborated binders, structure fields, and declaration
dependencies. It does not invoke Lean, build the target, or promote indexed
text to a type match or proof fact. `index status` verifies current source,
configuration, toolchain, helper, and schema identity; pass
`--no-verify-sources` only for a cheap stored-metadata inspection.
Builds default to a 512 MiB hard database ceiling, configurable with
`--max-index-mib`. Lexical signatures are capped at 16 KiB with per-row
truncation evidence, and queries cannot return more than 1,000 rows.

Stored ProofIR evidence is queried through the same ordinary CLI and the same
project-local database:

```bash
uv run --locked ladon proof-search evidence theorem Theorem.Name \
  --repo-root /path/to/lean/project --format json
uv run --locked ladon proof-search evidence triage all \
  --repo-root /path/to/lean/project --format json
```

The theorem dossier keeps subjects, claims, checker and governance
observations, derivations, source attachments, coverage, omissions, navigation,
and limitations in separate sections. Warm evidence queries are read-only and
never refresh the index or run external tools implicitly. A stored derivation
or navigation route remains structural evidence; it does not imply checker
acceptance.

Theorem extraction is an explicit Lean-backed CLI workflow:

```bash
uv run --locked ladon theorem extract Fully.Qualified.theorem \
  --repo-root /path/to/lean/project \
  --output /tmp/theorem-capsule \
  --verify
```

`ladon theorem plan`, `materialize`, and `replay` expose the same phases
separately. Planning requires pinned, compiled target state and is read-only with
respect to the checkout. Materialization writes outside the checkout. Replay
validates and rebuilds a fresh capsule copy, then compares the exact theorem's
toolchain-scoped structural and trust evidence. A verified capsule remains a
locked/rebuildable module-prefix package; it is not claimed to be globally
minimal, offline-vendored, system-hermetic, or independently proved by Ladon.

Exact theorem lineage is queried from the same repository-local SQLite index:

```bash
uv run --locked ladon theorem lineage Fully.Qualified.theorem \
  --repo-root /path/to/lean/project --refresh missing \
  --view routes --from trust --format text --output -
```

Lineage summaries are aggregate-only and do not enumerate routes:

```bash
uv run --locked ladon theorem lineage Fully.Qualified.theorem \
  --repo-root /path/to/lean/project --refresh never --view summary \
  --max-database-mib 1536 --format json --output -
```

The proof-search database is disposable and schema-versioned. A schema-v5
database uses a complete-database ceiling for lineage publication in addition
to the 512 MiB base-index ceiling. Status/build payloads expose SQLite
`dbstat` object and grouped byte accounting. Coverage-sensitive commands report
`unavailable`, `not-populated`, or `partial` rather than treating empty
observations as proof facts. Search results include inspectable ranking
contributions; global report populations remain opt-in and bounded.

Build or inspect the base index with `ladon proof-search index build|status`.
Warm closures are reused without starting Lean; use `--refresh never` to forbid
refresh, or `stale`/`always` to permit a supervised theorem plan. Views are
bounded (`routes`, `graph`, `tree`, `bottlenecks`) and support trust/project/
external/package/declaration roots, typed edges, generated-node policy, and
depth/node/edge/route caps. The result is dependency lineage for one compiled
proof term, not a list of all possible proofs, a proof alternative, or a
natural-language proof.

```bash
cd <target-repo>
lake env lean --run /path/to/ladon/src/ladon/lean/ladon_parser_helper.lean -- <target-file>
```

Project-specific architecture boundary policy:

```bash
uv run --locked ladon --repo-root /path/to/lean/project --root Some/Owner.lean \
  --architecture-policy docs/ladon-architecture-policy.json \
  --format json --output /tmp/ladon-report.json
```

Architecture policies are JSON files that define module groups with glob
patterns and rules between those groups. Ladon does not hard-code project
families such as samplers, kernels, bridges, or generated modules; the target
project supplies those names and exclusions.
See `docs/policies/architecture-policy.example.json` for a generic starting
point.

Artifact inspection is an ordinary, bounded CLI operation. It reads exactly
one existing report or compatible source-index JSON and does not implicitly
run discovery, Lake, Lean, version control, an initializer, or a build:

```bash
uv run --locked ladon inspect declarations \
  --report /tmp/ladon-report.json \
  --filter kind=theorem --filter module=Some.Owner \
  --limit 50 --format json
```

The supported nouns are `modules`, `declarations`, `imports`, `audits`,
`options`, `resources`, and `proof-mechanisms`. Use `--id` for exact stable-ID
lookup. A list page returns an opaque `nextCursor`; pass it back with the same
artifact, filters, and `--limit` to retrieve the next disjoint page. Cursors
bind the immutable artifact fingerprint, normalized query, page size, and last
stable ordering key. Each row includes its canonical artifact pointer, source
anchor or absence reason, authority, population, source fingerprint, and
collection coverage reference. Unknown totals remain unknown rather than
being presented as complete empty results.

Current v3 reports retain at most 10,000 option rows and 10,000
proof-mechanism rows before report projection. Coverage records the full
observed total and the internal omission when indexing was complete; a partial
source index keeps the total unknown. Review and summary projections may apply
additional explicit bounds. Older compatible reports that do not carry a noun
return an unavailable diagnostic rather than reconstructing source evidence.

`--repo-root` is optional and valid only with `--source-index`. Supplying it
explicitly asks Ladon to compare the artifact's source/configuration
fingerprint with the live repository and reject stale evidence. Without it,
inspection is artifact-only and checkout-independent. Run
`ladon inspect --help` for the finite filter vocabulary of each noun.

Lexical declaration, option, resource, audit, and proof-mechanism rows are
navigation evidence. Token occurrence is not an elaborated tactic invocation,
dependency, rewrite direction, simplifier use, proof-success result, or
theorem-quality verdict; optional Lean-backed enrichments retain a separate
authority row.

Generated-family candidate detection uses the frozen, caller-neutral
`generic-numbered-family-v1` conjunction. Candidate status is advisory and
does not change configured project-generated or Lean compiler-generated
provenance. `target_owned` is a separate ownership population, not provenance.
A non-default profile can be supplied with
`--generated-family-candidate-profile PATH`; it must use the strict separately
versioned schema, is fingerprinted into the analysis snapshot, and is rejected
before analysis if it disguises itself as the built-in profile. Explicit
profiles may select the supported
`parent-final-segment-decimal-suffix-width-v1` grouping to keep padded and
unpadded decimal families in separate partitions.

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
uv run --locked ladon --repo-root /path/to/lean/project --root Some/Owner.lean \
  --source-pattern-policy docs/ladon-source-pattern-policy.json \
  --format json --output /tmp/ladon-report.json
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
  and exact target-owned fan/large-module report rows so generated modules and
  public barrels do not hide owner-file architecture pressure;
- facade-like module subtype rows for pure barrels, generated `All` barrels,
  public root facades, and mixed barrel/theorem modules;
- lightweight lexical and import-target smell rows for anchored
  `sorry`/`admit`/`axiom`, TODO/FIXME, and missing internal import targets;
- optional project-supplied source-pattern scans for stale terms, local trust
  words, or other project conventions, with source locations and generated-code
  filtering when configured;
- optional proof-surface witness normalization and route diagnostics that
  preserve quoted verifier commands, source pins, axiom-audit metadata, and
  nonclaims without treating them as theorem-truth evidence;
- packet-evidence summaries for tracked review artifacts, with explicit
  completeness and authority boundaries;
- optional module-readiness, import-diet, proof-xray, and refactoring-
  prescription rows that route review while leaving Lean/Lake and named
  external tools authoritative;
- pure declaration graph analysis through `ladon.analysis.declaration_graph`;
- exact fully qualified theorem-capsule planning with an uncapped
  repository-dependency protocol and explicit external frontier;
- deterministic module-prefix capsule directories/archives with complete file
  inventory, stale-input rejection, and safe transactional publication;
- fresh-copy Lean replay with exact theorem/type/value/dependency/trust comparison
  and a bounded machine-readable receipt;
- additive `declaration_graph.declarations` rows with source path/range/hash,
  extraction backend/version, name-resolution method, and confidence when the
  Lean helper supplies that evidence;
- root-focused findings for module fan-in, target-owned module fan-in, root
  import closure, duplicate imports, large target-owned modules, declaration
  fan-in/fan-out, and unresolved-reference hotspots;
- unresolved-reference classification into local/field, external, parser-noise,
  known-inventory, and actionable-unknown classes;
- declaration-name family grouping for repeated theorem-shape suffixes;
- phase timing and Lean helper cache counters in JSON reports;
- JSON and text reports;
- strict Python quality gate with no active C-or-worse radon findings.

Not yet reintroduced:

- export-surface freshness checks;
- general report-facing transitive proof dependency extraction; theorem capsules
  use a separate exact target protocol rather than the bounded declaration report.

Native ProofIR v3:

- producers write canonical `proofirVersion: "3.0"` artifacts and list them in
  the repository ProofIR configuration; `ladon proofir validate ARTIFACT.json`
  checks an artifact before indexing;
- after artifacts change, rebuild the disposable project-local proof-search
  database explicitly with `ladon proof-search index build`; no query performs
  an implicit refresh;
- reviewers use `proof-search evidence theorem`, `route`, `slice`,
  `alternatives`, and `triage`. They must distinguish producer assertions,
  checker observations, attachments, structural derivations, coverage, and
  omissions rather than promoting any one row to theorem truth;
- `ladon proof-search check candidate --module MODULE --goal GOAL --candidate
  DECLARATION --format json` is the explicit Lean boundary for one declaration
  application against a closed goal. A closed application emits batch-closed
  environment, check-run, and derivation artifacts; remaining premises emit an
  incomplete attempt-log with typed substitutions, residuals, and context;
- former bridge, surface-bundle, replay, DAG, and witness dialects are rejected.
  Regenerate them at the producer as native v3; Ladon does not convert them.

Atlas workflow:

- `scripts/ladon_atlas_export.py` builds canonical atlas JSON plus optional
  Markdown, SQLite, and reviewer-card outputs from a report directory.
- `scripts/ladon_atlas_workflow.py` derives a reviewer workflow from atlas JSON,
  an optional earlier atlas, and optional generic external review reports. It
  summarizes changed rows, recurring hotspots, review-priority roots,
  low-confidence joins, and incomplete or stale evidence. Native ProofIR v3 is
  queried from the project-local proof-search database instead.
- installed `ladon query` results carry a versioned envelope. Useful positive
  results over incomplete inputs are labeled `non_exhaustive` with inherited
  collection coverage; `--exhaustive` instead returns a structured unavailable
  diagnostic when any required source table lacks complete authority.

Unsupported legacy flags fail explicitly rather than emitting partial reports.

Near-term work:

- harden the existing alpha surface: reconcile OpenSpec state, stabilize report
  and CLI contracts, correct known signals, bound Lean execution, add a bounded
  elaborated declaration surface, and require portable benchmark/clean-checkout
  gates;
- after that declaration surface is stable, let the bounded theorem-surface
  changelog child consume it without creating a second extractor;
- keep Review Radar as a planning umbrella until a separate MVP child can
  consume stable report/changelog rows;
- reserve future tactic-skeleton/InfoTree proof-xray generation for a separate
  backend contract; current optional rows remain quoted or explicitly
  authority-labeled inputs.

## Internal Python quality audits of Ladon

### Proof-search semantic commands

The installed CLI exposes bounded, ordinary-user commands:

```bash
ladon proof-search index build --repo-root .
ladon proof-search search name --repo-root . --text fixedIndex
ladon proof-search search type --repo-root . --pattern 'Nat → Nat'
ladon proof-search explain --repo-root . --goal 'P' --candidate 'lemma'
ladon proof-search consumers --repo-root . --declaration target
ladon proof-search constructor --repo-root . --structure Record
```

JSON results preserve freshness, authority, bounds, omissions, and nonclaims;
lexical/SQLite shortlist rows are never presented as Lean verification.

Run the project-local quality command from this repository:

```bash
uv run --locked python scripts/python_quality.py
```

This runs:

- scoped Ruff import, syntax-adjacent, and Pyflakes rules from `pyproject.toml`;
- `radon cc` and `radon mi` as complexity/maintainability reports;
- `vulture` as the high-confidence dead-code scan.

Strict mode is the gate used for implementation work:

```bash
uv run --locked python scripts/python_quality.py --strict
```

Strict mode fails on configured Ruff findings, active C-or-worse radon blocks,
C-grade maintainability, high-confidence vulture findings, compile failures,
or test failures. Formatting and broader Ruff style families remain deliberately
deferred so the lint baseline can expand through reviewed changes. Treat
that as a design constraint: split analyzer behavior into small modules before
adding more heuristics.

## LLM Disclaimer

This is close to 100% AI assisted code. Much of it is even "vibe-coded", i.e. not looking at the generated code. This is evolved on the side when developing some experimental Lean code and trying to keep the codebase clean.
