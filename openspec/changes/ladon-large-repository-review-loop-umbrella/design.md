## Context

Ladon's alpha hardening made the ordinary CLI reproducible, versioned, and
bounded on portable fixtures. The first post-alpha trial against
Matrix-Factorization shows that the analysis itself is useful but the end-to-end
operator loop does not scale yet. The exact observations, commands,
fingerprints, output hashes, and authority boundary are recorded in
`discovery-evidence.md`.

The important observations are:

- text-backed full inventory succeeds and identifies real policy/facade/
  generated-family pressure, but takes roughly 53 seconds for 2,611 modules;
- JSON construction peaks near 1.6 GiB and writes 218 MB because the large
  module payload is repeated at top level, in phase data, and in the legacy
  pipeline timing view;
- an owner-selected Lean run still scans the whole inventory, peaks near
  8 GiB, exits with a partial result, and does not expose the failure reason;
- owner reports mix target declarations, imported declarations, generated
  declarations, synthetic declarations, and global findings into one review
  surface;
- useful atlas/query/card implementations exist, but only as checkout scripts,
  not as supported installed operations;
- Matrix-Factorization has coherent multi-root frontiers, command-only audit
  files, generated table families, and resource overrides that the current
  root/declaration model does not represent well.

Several neighboring capabilities already exist and remain authoritative:

- `ladon-report-contract-v2` owns report versioning and compatibility;
- `ladon-cli-execution-contract` owns public process/exit/output behavior;
- `ladon-lean-extraction-runtime-hardening` owns process supervision, batch
  protocol, cancellation, and Lean cache fingerprints;
- the atlas/export/query/diff/workflow modules own report-set algorithms;
- `ladon-theorem-surface-changelog` owns semantic before/after declaration
  comparison, and the Review Radar roadmap owns its future reviewer-card
  consumer.

This umbrella must compose those seams rather than create replacements.

## Goals / Non-Goals

**Goals:**

- Make a large Lean repository usable through the same ordinary public CLI used
  by every caller.
- Make inventory cost reusable, root scope explicit, output size intentional,
  and long-run state observable.
- Keep owner-focused review separate from optional global context.
- Recover useful, bounded partial evidence without hiding why the requested
  analysis failed.
- Make promoted findings navigable to raw evidence and source locations.
- Support deterministic, resumable multi-root review and installed report-set
  workflows.
- Recognize audit-command modules and resource directives as review surfaces
  with explicit authority.
- Gate implementation with portable scale fixtures and repeat the fingerprinted
  live-repository observation at umbrella closeout.

**Non-Goals:**

- No LLM-facing command, role-specific threshold, hidden prompt layer, or
  caller-specific output.
- No hard-coded Matrix-Factorization roots, module names, filename statuses,
  generated families, or policy vocabulary.
- No automatic choice of the mathematically correct review root.
- No source rewrite, import deletion, proof repair, theorem-truth verdict, or
  witness-adequacy claim.
- No second Lean helper protocol, process supervisor, cache system, report-set
  graph, theorem comparator, or atlas implementation.
- No mandatory dependency on a sibling repository in portable CI.
- No web UI, editor integration, graph database, or Rust rewrite in this
  umbrella.

## Decisions

### 1. Sequence the work around an operable review loop

The child dependency shape is:

```text
large-inventory scale ───────┬──> root/scope contract ──┐
partial-run observability ───┘                          │
                                                       ├──> runsets/bundles ──┐
ownership/generated calibration ─> actionable findings ┘                     │
          │                                                                   ├──> installed report-set workflow
          └──────────────> audit-command surface ─────────────────────────────┘
```

The scale and partial-observability children are first because every later
workflow depends on bounded, diagnosable analysis. Scope planning precedes
runsets. Ownership calibration precedes finding ranking and audit-surface
promotion. Installed report-set operations are last because they consume the
reports and bundle manifests produced earlier.

Alternative considered: start with Review Radar or a new dashboard. That would
wrap current 53-second/218-MB runs without fixing their operability.

### 2. Build one versioned source index and project it into scopes

Discovery will produce a versioned source index containing normalized module
identity, relative path, direct imports, source/content fingerprints, lexical
declaration summaries, generated-role evidence, and policy/configuration
fingerprints. Cold construction and warm reuse must be measured separately.
Cache/index writes must stay outside the target source tree unless the caller
explicitly selects a target-owned path.

The index feeds explicit scope plans:

- `owner`: the requested source owner;
- `closure`: the local direct-import closure, with depth/module limits;
- `namespace`: modules under a declared namespace/source root;
- `multi-root`: a named or explicit set of roots;
- `changed-set`: caller-supplied changed paths or a versioned manifest;
- `inventory`: every discovered target module.

Scope planning is non-executing and reports selected/omitted counts, policies,
expected Lean batches, truncation, and fingerprints. The first implementation
accepts changed paths/manifests; automatic git-ref orchestration remains in the
retained Review Radar lane.

Alternative considered: keep the current top-namespace scan for every root and
filter only at rendering time. That preserves the dominant parsing/memory cost
and cannot make runsets incremental.

### 3. Give every large payload one canonical owner

The report model will own each analysis payload once. Phase envelopes retain
status, counters, timing, reason, diagnostics, provenance, and a stable payload
reference. The legacy `pipeline.timings` view remains timing/status metadata and
must not embed phase payloads. Top-level report sections remain the canonical
payload owners.

The public format gains explicit projections:

- `summary`: bounded counts, phases, diagnostics, and promoted findings;
- `review`: summary plus bounded evidence tables needed for normal review;
- `full`: complete raw inventories and declaration/source evidence.

Every projection records its identity, omissions, and source analysis
fingerprint. Omitted data must never look like an observed empty population.
Text is a summary/review rendering of the same analysis result. JSON consumers
receive a compatibility window and adapter for the duplicated alpha-v2
locations before their removal.

Alternative considered: merely switch pretty JSON to compact JSON. That would
reduce whitespace but preserve three approximately 46-MB copies.

### 4. Treat scale as a contract, not an anecdotal optimization

A generated portable fixture will model thousands of modules, a broad facade,
deep generated families, command-only audit modules, and a six-figure lexical
declaration population without copying Matrix-Factorization source. Its
manifest records reviewed cold/warm time, peak RSS, output size, determinism,
and cache-invalidation budgets.

Required gates use the portable fixture. The live Matrix-Factorization run is
repeated only as observational acceptance, with source fingerprint, target
revision/dirty state, toolchain, Ladon identity, commands, timings, RSS, helper
counts, report hashes, and normalized semantic predicates.

Alternative considered: require moving sibling-repository cardinalities in CI.
That would make a private dirty worktree an undeclared product dependency.

### 5. Reuse the current supervisor and make partial state explicit

Long phases emit structured progress events to stderr under an explicit
progress policy while report bytes remain isolated on stdout or in the selected
file. The CLI gains an overall deadline in addition to existing build/Lean
deadlines. Discovery and rendering gain cancellation checkpoints.

A partial required phase must carry:

- a stable failure class and concise reason;
- structured diagnostics and selected/completed/omitted counts;
- whether cached rows were used or written;
- whether evidence tables are complete enough for downstream metrics;
- one concise stderr summary and the ordinary operational exit status.

Metrics derived from incomplete populations are suppressed or labeled partial;
all-zero declaration fan-in is not presented as a completed baseline when
dependency extraction failed. Existing process-group cleanup and cache
fingerprints remain the only implementation mechanisms.

Alternative considered: add another helper wrapper around the Lean backend.
That would duplicate the recently hardened runtime and risk new orphan-process
paths.

### 6. Separate declaration and module ownership populations

Every declaration row is classified as target-owned authored,
target-owned configured-generated, Lean/compiler-generated, or imported
dependency identity. Imported dependencies needed to explain owner edges remain
compact identities; they do not become full owner surfaces.

Compiler-generated names and project-generated families are retained in full
evidence but excluded from authored proof-family promotion by default.
Project-generated family rules are inspectable configuration with matched
evidence and stable family IDs. Generic defaults may recognize syntactic Lean
compiler artifacts, but target-specific `Data`/`Row`/status conventions belong
to repository policy.

Module and declaration reports state the population used by every metric.
Generated-family summaries can collapse repetitive family members for ranking
without removing raw full-projection evidence.

Alternative considered: hard-code the Matrix-Factorization row/table naming
scheme. That would improve one repository while making Ladon less trustworthy
elsewhere.

### 7. Make findings inspectable instead of increasing their count

This umbrella does not add another generic smell taxonomy. Existing promoted
findings gain:

- stable IDs independent of wording and display order;
- scope classification and owner relevance;
- severity, confidence, priority, and authority in separate vocabularies;
- resolvable raw-row, aggregate, source-path, and source-range references;
- an explicit explanation when no exact source position exists;
- a suggested ordinary CLI lookup or next analysis command.

The installed CLI supports deterministic list/filter/show operations over a
report or bundle. Default owner output ranks owner/closure evidence before
optional inventory context. Phase counters are finalized after all promotion
steps so counts agree across text, JSON, phases, atlas, and bundles.

Alternative considered: print every finding in text. On the observed project
that replaces one navigation problem with an unbounded terminal dump.

### 8. Runsets contain reports; they do not merge authority

A versioned runset manifest names ordinary analysis entries and their root,
scope, backend, projection, configuration, resource policy, and output
identity. Execution is serial by default, shares only sound indexes/caches,
isolates failures, and produces one canonical report per root plus a
deterministic bundle manifest.

Resume decisions use input and output fingerprints. An unchanged completed
entry launches no new analysis; changing one entry invalidates only that entry
and dependents explicitly named by the manifest. Cancellation reuses the
existing supervisor and leaves no helper descendants.

Alternative considered: invent a merged multi-root report schema. Separate
reports preserve root-specific phase state and authority while the bundle/atlas
provides aggregation.

### 9. Install the report-set workflow already present

Atlas export, canned query, generic atlas diff, reviewer cards, SQLite
derivation, and workflow summaries become supported operations reachable from
the installed ordinary Ladon CLI. The implementation imports the existing
library functions; checkout scripts become thin compatibility wrappers or are
retired after a documented window.

CLI output follows the alpha execution contract: one requested machine payload
on stdout, diagnostics on stderr, stable invocation versus operational exit
codes, and no dependence on the source checkout. Atlas terminology distinguishes
highlighted module nodes from total inventory module counts.

Semantic declaration comparison is not added here. The existing
`ladon-theorem-surface-changelog` remains the sole owner and can later feed the
installed workflow.

Alternative considered: create new console scripts for each source module.
A coherent subcommand surface is easier to discover and keeps one ordinary
product contract, while still allowing thin compatibility entrypoints.

### 10. Model command-only audit files as references, not declarations

Ladon will recognize parsed or elaborated `#check` and `#print axioms` commands
as audit references with source anchors, resolved target identity when
available, backend authority, and explicit nonclaims. A file containing only
audit commands can be classified as an audit facade even though it declares no
new mathematics.

Resource directives such as heartbeat or recursion-depth overrides become
source facts with scope and literal value. Promotion to a finding is
policy-driven; Ladon does not infer that a high budget is incorrect.
Comment/string false positives must be excluded.

Alternative considered: infer audit status only from filenames such as
`FinalAudit`. The observed repository contains useful audit prose and commands,
but filename intent is project-specific and semantically ambiguous.

### 11. Resolve the implementation defaults before child application

The ordinary report default is `review` once report v3 becomes the default.
`summary` remains an explicit bounded automation projection and `full` remains
an explicit evidence projection. During migration, an invocation that does not
select a report major retains the current v2 behavior until v3 is declared the
default; Ladon must not silently reinterpret a v2 document as a review
projection.

Report v2 remains readable. Explicit v2 serialization remains supported for
the first two Ladon minor releases after v3 becomes the default, with a
diagnostic naming its duplicate-payload cost; the third minor may remove v2
writing but not v2 reading. In-repository consumers must migrate before v3
promotion.

The default reusable cache lives in the platform user-cache directory under a
`ladon` namespace. `XDG_CACHE_HOME` takes precedence on Unix; documented
platform fallbacks are used otherwise. An explicit `--cache-dir` always wins,
and cache writes never enter the target checkout unless the caller explicitly
chooses such a path.

The portable scale gate uses an Ubuntu 24.04 x86-64 reference image with four
available CPU cores and the supported Python matrix. It records three cold and
three warm samples and requires every sample to satisfy the committed
ceilings. There is no numeric budget inflation for noise; a rerun is allowed
only for a separately recorded infrastructure failure, never because Ladon
crossed a ceiling.

Audit-command extraction is lexical and comment-safe for every backend.
Selecting the Lean backend may enrich those rows through the existing bounded
helper and supervisor; lack of Lean enrichment remains explicit rather than
blocking lexical audit evidence.

`--lean-strict` is deprecated in favor of the existing general failure-selector
contract. During the two-minor report migration window it remains a
compatibility alias for rejecting a partial Lean-extraction phase and emits a
deprecation diagnostic; it must not become a semantic no-op. After the window,
callers use the documented `--fail-on phase:lean_extraction:partial` selector.

## Risks / Trade-offs

- [Risk] Removing duplicated report payloads breaks alpha consumers. →
  Mitigation: version the projection contract, ship an adapter/diagnostic
  window, and test every in-repository reader before removal.
- [Risk] A warm source index becomes stale after indirect layout, policy, or
  tool changes. → Mitigation: fingerprint layout, source bytes, tool version,
  and effective configuration; expose every reuse/invalidation reason.
- [Risk] Scoped analysis hides important global architecture pressure. →
  Mitigation: record the exact population, offer explicit inventory context,
  and never label omitted modules as observed clean.
- [Risk] Progress events corrupt JSON consumers. → Mitigation: stderr only,
  explicit progress policy, and installed stdout-channel tests.
- [Risk] Resource budgets are noisy across CI machines. → Mitigation: gate
  deterministic semantic ceilings and broad reviewed resource envelopes;
  retain exact live timings as observational evidence.
- [Risk] Generated classification suppresses authored work. → Mitigation:
  evidence-backed configurable rules, raw full-projection retention, and
  authored/generated negative fixtures.
- [Risk] Partial reports are mistaken for successful analysis. → Mitigation:
  required phase state, prominent reason, nonzero exit, and downstream
  rejection of incomplete required populations.
- [Risk] Audit commands appear to prove the referenced claims. → Mitigation:
  model them as references/queries with separate Lean or lexical authority and
  repeated nonclaims at report boundaries.
- [Risk] The umbrella duplicates retained changelog or atlas work. →
  Mitigation: dependency ledger names authoritative packets/modules and forbids
  parallel implementations.

## Migration Plan

1. Freeze portable scale fixtures and current observational baselines.
2. Implement single-owner report payloads and source-index profiling with
   adapters for current v2 readers.
3. Add explicit scope planning and partial-run observability before changing
   default owner behavior.
4. Calibrate ownership/generated populations and then re-rank/link existing
   findings.
5. Add runsets and audit-command surfaces on the bounded scope/index/runtime.
6. Expose existing report-set libraries through the installed CLI.
7. Run full installed-distribution, benchmark, OpenSpec, and live observational
   acceptance gates.
8. Remove compatibility payload copies only after all in-repository readers and
   the documented compatibility window are complete.

Rollback keeps the previous report adapter and single-analysis CLI path
available. Every child must remain independently disableable until its portable
gates and dependent readers pass.

## Open Questions

None block application. Child implementation may refine syntax or internal
module boundaries, but changing the defaults, compatibility window, authority
boundary, or committed resource ceilings requires an explicit design update.
