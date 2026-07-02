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
   including root direct-import closure attribution, duplicate import rows,
   generated-module tags, generated-filtered fan tables, facade/barrel fan-out,
   implementation fan-out, and large source-file triage rows.
5. `analysis.architecture_policy`: apply optional project-supplied module group
   policies to the DAG. Ladon supplies generic glob matching and graph traversal
   only; projects define the groups, forbidden imports, and exclusions.
6. `analysis.source_patterns`: apply optional project-supplied source text
   pattern scans. Ladon supplies generic substring/regex matching only; projects
   define stale terms, local trust markers, and generated-code filtering.
7. `lean_extraction`: optionally run the bundled Lean parser helper for selected
   files and cache helper JSON payloads by source/helper content.
8. `analysis.declaration_graph`: summarize conservative declaration-reference
   edges, fan-in/fan-out, reachability, and unresolved candidate hot spots.
9. `analysis.findings`: promote high-signal graph rows into concise root-focused
   findings.
10. `pipeline`: record phase timings and counters around extraction, analysis,
   findings, and rendering.
11. `render`: write JSON/text reports from already-computed data.
12. `proofir_bridge`: optionally joins compact ProofIR review inputs to Ladon
    declaration evidence. Accepted inputs are `proofir_bridge_index` and
    Quux-style `proof_ir_lean_surface_bundle`; raw ProofIR dialects remain out
    of core.
13. `proof_surface_witness`: normalizes optional quoted proof-surface witness
    artifacts for frozen spec stubs, proof endpoints, no-drift gates, source
    pins, axiom audits, and proof-hole quarantine. The witness is route
    governance metadata, not theorem-truth evidence.
14. `atlas`, `atlas_diff`, `atlas_sqlite`, and `atlas_workflow`: derive
    reviewer-routing graphs, diffs, canned queries, cards, and workflow
    summaries from Ladon report JSON plus optional bridge reports.
15. `quality`: enforce radon/vulture gates for active Python code.

Unsupported until rebuilt with tests:

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

Proof-surface witness audit extends this seam with quoted verifier metadata.
It can report when a claim cites a frozen spec stub as authority, lacks a clean
no-drift gate, lacks an accepted axiom audit, quotes suspicious axioms, or has a
clean endpoint route. These diagnostics are source-attachment and
route-governance checks only. They do not validate Lean theorem truth, replay
proofs, certify witness adequacy, or decide mathematical scope.

## Current Architecture Policy Seam

`ladon.analysis.architecture_policy` defines a pure policy layer over the
module DAG. A project can define module groups using glob patterns and then
state which group-to-group imports are forbidden. Ladon can report direct
violations, optional transitive witness paths, ambiguous group matches, and
shared peer dependencies that may belong in a lower common layer.

This seam is intentionally generic. Ladon does not know about any project's
samplers, proof families, generated modules, bridges, or kernels. A target
repository must provide those names in a JSON policy file, and rule-level
exclusions decide which integration or generated modules are allowed to cross
boundaries. The resulting diagnostics are source-level architecture findings;
they are not proof dependencies or theorem-truth claims.

Intentional bridge or common-layer imports should be modeled in the policy, not
hard-coded into Ladon. Typical choices are separate groups such as `bridge` or
`common`, plus rule exclusions like `ignoreSource`, `ignoreTarget`, or exact
`ignoreEdges`. This keeps the same analyzer usable for sampler families,
optimization kernels, generated surfaces, integration modules, and future Lean
projects without teaching Ladon any project-specific names.

Policy discovery is repo-local and explicit. The CLI accepts
`--architecture-policy <json>`, otherwise the pipeline searches
`.ladon/architecture-policy.json`, `ladon.architecture.json`, and
`ladon-architecture-policy.json`. If no file is found, the report includes an
`architecture_policy.skipped_no_policy` info finding instead of silently
omitting this class of checks. The skipped report may include a draft policy
suggestion based on repeated module-name prefixes and observed cross-prefix
imports; that suggestion is heuristic guidance and is not enforced.

Text extraction preserves source path, line, and import text for imports.
Policy findings attach that evidence to direct violations, while transitive
findings carry witness paths plus per-edge source evidence when available. The
policy report also includes direct pair summaries and ranked shared-dependency
summaries so reviewers can see whether a problem is a single bad import or a
systemic misplaced common layer.

Human-readable policy output is deliberately summary-first: direct group-pair
counts, top offending source files, and ranked common-layer candidates come
before raw finding counts. The complete direct edges, transitive witness paths,
and import-site evidence remain in JSON for scripts and detailed review.

Common-layer candidate scanning has two explicit modes. The default
`sharedDependencyMode: "policy_targets"` preserves the narrow behavior: only
targets selected by the rule's `to` groups are considered. Projects that want a
broader lower-layer audit can set
`sharedDependencyMode: "all_multi_group_imports"`; then any imported target seen
from multiple selected source groups can become a ranked common-layer
candidate. Both modes use project-supplied groups and exclusions rather than
hard-coded module-family names.

Direct policy findings also carry triage context. Rules can provide
`bridgeTokens` or `contextClassifiers.bridgeTokens`; otherwise Ladon uses a
small generic bridge vocabulary such as `Bridge`, `Transport`, `Comparison`,
`Calibration`, and `Surface`. Matching rows are labeled `bridge-ish`; rows
whose source or target module metadata says `facade` are labeled `facade-ish`;
the rest are `core-looking`. These labels do not suppress policy violations.
They help reviewers decide whether to extract a lower common layer, make an
intentional bridge explicit in policy, or move facade aggregation out of owner
implementation code.

The module DAG itself deduplicates graph edges so repeated import lines do not
inflate fan-in, fan-out, pair summaries, or policy violations. Repeated import
targets are still reported separately as duplicate-import rows with line
evidence and a generic cleanup hint to remove repeated import lines or fix the
generator that emits them.

Module metadata includes facade-like subtypes. `pure_barrel` means imports with
no declarations; `generated_all` means generated `All` aggregation files;
`public_root_facade` means a namespace root file importing a broad child
surface; `mixed_barrel_and_theorems` means a module combines broad imports with
local declarations. These are source-shape classifications, not proof claims.

Text extraction also records lightweight lexical markers for anchored
`sorry`/`admit`/`axiom` in code and TODO/FIXME markers in source text, plus
imports that look internal to the top namespace but are missing from the
discovered inventory.

## Current Source Pattern Policy Seam

`ladon.analysis.source_patterns` defines a generic policy layer for source text
matches that are project-specific. A policy row names the pattern, its kind, its
severity, whether it is a regex, whether matching is case-sensitive, and whether
generated files should be excluded. The analyzer does not know about any target
project's stale names, local trust terms, or deprecated phases.

The CLI accepts `--source-pattern-policy <json>`, otherwise the pipeline
searches `.ladon/source-pattern-policy.json`, `.ladon/source-patterns.json`,
`ladon.source-patterns.json`, and `ladon-source-pattern-policy.json`. If no
policy is found, the phase is recorded as skipped and no source-pattern findings
are emitted.

Matches carry module, source path, line, matched policy id, kind, severity, and
whether extraction classified the file as generated. They are review-routing
signals only. A stale term in source text does not establish a proof issue, and
the absence of a configured term does not prove semantic freshness.

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
- handwritten module fan-in hotspots;
- root direct-import closure hotspots;
- duplicate import targets;
- large handwritten modules;
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
