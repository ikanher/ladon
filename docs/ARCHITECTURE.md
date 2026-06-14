# Ladon Architecture

Ladon is a clean-core Lean analyzer that is being rebuilt as a tested analysis
pipeline. The rule for the rebuild is TDD: add a small testable seam first,
then add analyzer behavior only behind that seam.

The old broad prototype has been removed from active package code. If a feature
is not listed as supported here, do not describe it as implemented.

## Current Supported Surface

1. `cli`: parse compatibility flags, reject unsupported legacy features
   explicitly, and orchestrate one run.
2. `extraction`: discover Lean modules from source text without invoking Lake.
3. `ir`: hold stable dataclasses shared by pure analysis passes.
4. `analysis.module_dag`: summarize importer-to-imported module DAG structure,
   including root direct-import closure attribution.
5. `lean_extraction`: optionally run the bundled Lean parser helper for selected
   files and cache helper JSON payloads by source/helper content.
6. `analysis.declaration_graph`: summarize conservative declaration-reference
   edges, fan-in/fan-out, reachability, and unresolved candidate hot spots.
7. `analysis.findings`: promote high-signal graph rows into concise root-focused
   findings.
8. `pipeline`: record phase timings and counters around extraction, analysis,
   findings, and rendering.
9. `render`: write JSON/text reports from already-computed data.
10. `proofir_bridge`: optionally joins compact ProofIR review inputs to Ladon
    declaration evidence. Accepted inputs are `proofir_bridge_index` and
    Quux-style `proof_ir_lean_surface_bundle`; raw ProofIR dialects remain out
    of core.
11. `atlas`, `atlas_diff`, `atlas_sqlite`, and `atlas_workflow`: derive
    reviewer-routing graphs, diffs, canned queries, cards, and workflow
    summaries from Ladon report JSON plus optional bridge reports.
12. `quality`: enforce radon/vulture gates for active Python code.

Unsupported until rebuilt with tests:

- witness metadata audits;
- review-packet audits;
- export-surface freshness checks;
- elaborated proof dependency extraction.

## Current Claim Authority Audit Seam

`ladon.analysis.claim_authority` defines a pure governance layer for quoted
claim/evidence route metadata. It answers one question:

```text
Does the claim's authority label match the observed evidence route?
```

It does not prove theorem truth, replay Lean, validate witnesses, or decide
mathematical correctness. It emits review-routing diagnostics when route
metadata says, for example, that a claim is Lean-closed while a required premise
is imported interval-certified, or that a public claim advertises an
arbitrary-neighbor endpoint while the primary theorem surface is sampled/null.

This is Ladon's highest-priority product seam after the ProofIR bridge: process
overclaim detection is more urgent than adding new architecture-smell classes.
Graph metrics, proof-family similarity, atlas diffs, and OpenSpec hygiene remain
useful context, but they should not displace claim authority route auditing.

## Target Pipeline

1. `extraction`: run text or Lean-native extraction and produce stable IR.
2. `ir`: dataclasses for modules, declarations, references, files, witnesses,
   review packets, and OpenSpec tasks.
3. `analysis`: pure functions over IR, with no filesystem or subprocess side
   effects.
4. `findings`: convert analysis results into review findings.
5. `report`: render JSON/text from stable report objects.
6. `cli`: orchestrate filesystem discovery, Lean subprocess calls, caching, and
   report writing.

## Current First Seam

`ladon.ir.LeanModule` and `ladon.analysis.module_dag.summarize_module_dag`
define the first extracted architecture seam.

Why this seam first:

- matrix-factorization and Quux both have clear acyclic module graphs;
- repo-wide module DAG analysis was a known Ladon blind spot;
- module DAG logic is pure and easy to test;
- it gives a useful Rust-port candidate later without touching Lean-native
  extraction.

## Current Declaration Seam

`ladon.ir.LeanDeclaration` and
`ladon.analysis.declaration_graph.summarize_declaration_graph` define the first
declaration-level seam.

The Lean helper supplies parser-level declaration commands and raw reference
candidates. The pure graph analysis resolves only exact full names,
module-local names, and globally unique basenames. This is useful for triage,
but it is not an elaborated proof-dependency graph.

When declaration extraction is available, reports include an additive
`declaration_graph.declarations` table. Rows can carry the declaration name,
module, kind, source path, source range, selection range, source content hash,
extractor backend/version, name-resolution method, and confidence label. These
fields establish source attachment confidence for reviewer routing. They do not
establish Lean kernel dependencies, theorem truth, witness adequacy, or proof
correctness.

The seam also classifies unresolved reference candidates. It separates parser
noise, local/field names, external Lean/library names, known text-inventory
declarations, and genuinely actionable unknowns. Text inventory is used only as
a classification aid, not as proof-dependency edge evidence.

Declaration name families group similarly named declarations by suffix after the
first underscore. This catches repeated proof-shape families such as
`ge_one_add_firstLag` without comparing proof terms.

Why this seam now:

- it identifies shared kernels and orchestration declarations from real owner
  files;
- it gives root-focused signal without restoring the old broad monolith;
- unresolved candidates produce concrete next work for better name resolution;
- the cache makes repeated root-level Lean extraction cheap enough for review
  loops.

## Current Findings Seam

`ladon.analysis.findings.summarize_findings` turns graph rows into concise
triage items. It currently reports:

- module fan-in hotspots;
- root direct-import closure hotspots;
- declaration fan-in/fan-out hotspots;
- declaration name family hotspots;
- unresolved reference hotspots;
- unreachable declaration counts.

Findings are not proof claims. They are ordering hints for reviewers so raw graph
tables are not the first thing a human has to interpret.

## Current Atlas Workflow Seam

Atlas JSON is the canonical machine-readable surface for report sets. Markdown,
SQLite, diffs, reviewer cards, and workflow summaries are derived from atlas
JSON and optional ProofIR bridge reports.

The workflow answers review-routing questions: what changed, what recurs, which
roots need review first, which joins are low-confidence, and which packet or
bridge evidence is incomplete or stale. Optional bridge diagnostics stay in the
`proofir.*` namespace and remain quoted context, not Ladon-validated proof
status. Quux `ladon_proofir_bridge_snapshot` artifacts can be summarized as
already-rendered bridge evidence, but compact surface inputs remain the primary
ProofIR bridge contract.

## TDD Rules

- New architecture surfaces start with tests in `tests/`.
- Analysis modules must be pure: no shelling out, no reading arbitrary repo
  paths, no global state.
- CLI code may adapt extracted objects into IR, but analysis modules should not
  import the CLI.
- `uv run python scripts/python_quality.py --strict` is a design gate, not just
  a lint report.
- Do not port to Rust until the Python seam has stable tests and phase timing
  proves the seam is a real hotspot.

## Next Test Slices

1. Calibrate declaration-reference and evidence-join signals on portable
   fixtures before adding more finding classes.
2. Improve declaration reference resolution without overclaiming elaboration.
3. Move OpenSpec task backlog scanning into `analysis.openspec_backlog`.
4. Move witness metadata checks into `analysis.witnesses`.
5. Rebuild export-surface freshness checks as a separate tested module.
6. Profile stable hot paths before considering Rust.
