## Context

The previous large-repository umbrella established explicit scopes, bounded
projections, audit-command rows, generated-population calibration, actionable
findings, and installed report-set workflows. A new text-backed run on a live
Matrix-Factorization checkout exercised those capabilities together and exposed
integrity failures at their seams:

- an owner slice classified known inventory imports as missing because the DAG
  summary received only the selected module map;
- inventory scope declared roots irrelevant while reachability analysis silently
  reused a report anchor as a root;
- a composite finding paired an import closure with an unrelated global fan-in
  maximum and summed incomparable counts;
- namespace and declaration-role context was discarded before collision analysis;
- command-only audit modules were classified as pure barrels before audit evidence
  was attached, and multiline command subjects were left unparsed;
- configured provenance worked, but highly regular unconfigured generated-looking
  families entered target-owned “handwritten” rankings;
- the complete lexical source index existed on disk while normal reports discarded
  most declaration rows and the ordinary CLI could not inspect the retained data;
- projections and atlas imports exposed partial tables without a consistent
  completeness contract; and
- concurrent source edits could make separate format renders describe different
  repository states.

These observations are text-authority evidence. No Matrix-Factorization build was
run, so the design does not treat lexical collisions as Lean environment errors,
audit intent as a captured result, tactic syntax as a dependency, or configured
resource limits as consumed runtime.

Existing capabilities remain authoritative at their seams:

- `ladon-analysis-root-and-scope-contract` owns population selection;
- `ladon-signal-correctness` owns missing-import and fan-in population semantics;
- `ladon-architecture-correlator` owns composite finding kinds;
- `ladon-declaration-source-evidence` owns source declaration rows, while
  `ladon-elaborated-declaration-surface` owns Lean-confirmed identities;
- `ladon-lean-audit-command-surface` owns command/result authority, and
  `ladon-common-layer-and-facade-quality` owns facade subtype vocabulary;
- `ladon-project-ownership-and-generated-calibration` owns configured provenance;
- `ladon-actionable-findings-workflow` owns stable finding identity and evidence
  references;
- `ladon-large-inventory-scale-contract` and `ladon-report-contract-v2` own
  canonical payloads, projections, compatibility, and render parity;
- `ladon-cli-execution-contract` owns streams, exits, and the single-stdout
  representation rule;
- `ladon-installed-reportset-workflow` owns atlas/query/card algorithms; and
- `ladon-proof-xray-roadmap` owns future elaborated proof/tactic structure.

This umbrella adds integrity checks and cross-capability joins; it does not create
parallel engines. In particular, `ladon-analysis-inspection-surface` owns only
ordinary navigation over existing evidence. Optional elaborated tactic/proof-shape
work remains owned by `ladon-proof-xray-roadmap`.

## Goals / Non-Goals

**Goals:**

- Make scope boundary, reachability, and composite-finding evidence truthful.
- Recover namespace-aware lexical declaration and audit navigation without
  overstating Lean semantics.
- Surface unconfigured generated-looking families as advisory policy candidates.
- Make the retained source index inspectable through ordinary, caller-neutral CLI
  operations.
- Summarize lexical proof mechanisms, scope context, options, and resource pressure
  with explicit authority and completeness.
- Make every projected or derived table disclose its coverage.
- Produce all selected formats from one immutable analysis snapshot and diagnose
  source drift.
- Gate the changes with portable positive and negative fixtures plus optional
  fingerprinted live-repository observations.

**Non-Goals:**

- No LLM-facing command, model-specific ranking, hidden prompt protocol, or
  caller-specific default.
- No hard-coded Matrix-Factorization modules, theorem names, family prefixes,
  cardinalities, or thresholds in production code.
- No theorem-truth, proof-correctness, axiom-freedom, runtime-consumption, or dead
  module claim from lexical evidence.
- No automatic source rewrite, import removal, proof repair, or provenance
  promotion.
- No replacement parser, Lean helper protocol, atlas engine, report schema family,
  cache implementation, or source-index format without a migration need.
- No required CI dependency on a sibling Lean repository or a mutable dirty tree.

## Decisions

### 0. Sequence shared coverage before evidence-producing children

The child order is:

```text
report: coverage foundation
          |
          v
scope/join integrity -> declaration/audit integrity
                                |
                                v
                  generated-family candidates
                                |
                                v
                      analysis inspection
                                |
                                v
          report: snapshot/region closeout
```

The report child has two explicit milestones. Its `coverage-foundation` milestone
establishes compositional collection coverage, captured analysis identity, and
generic review-region registration before later children publish new bounded
collections. Scope/join then provides truthful context for collision evidence;
declaration/audit rows feed family detection; and inspection is integrated after
the canonical row kinds exist. Those producer children close on canonical rows,
registration evidence, and ordinary action templates; none requires or emits a
complete review-region object. The report child's
`snapshot-and-region-integration` milestone then closes multi-render, concrete
region routing, and cross-consumer parity after all producers are available.

Alternative considered: add coverage after all evidence producers. That would make
each earlier child invent temporary truncation semantics and would allow atlas and
render consumers to misread new partial tables during implementation.

### 1. Carry population identity and authority through one canonical evidence model

The source index remains the canonical owner of complete lexical evidence. Each
row used by a summary, finding, projection, inspection result, or atlas edge will
carry:

- stable source/index fingerprint and schema version;
- population and selected-scope identity;
- backend and registered authority value, including `lexical_text`,
  `module_import_graph`, `lean_environment`, `external_tool_quoted`, or
  `ladon_derived_heuristic` as applicable;
- source anchor when one exists;
- completeness/coverage reference; and
- typed links to other canonical rows rather than copied payloads.

Unavailable and partial are evidence statuses with structured reasons, not
authority values. Text evidence may create `candidate` relationships. Only Lean-backed evidence may
upgrade relationships whose meaning requires elaboration. A consumer must not
infer authority from a field's presence or from a module/declaration label.

Alternative considered: add integrity annotations only to rendered findings. That
would leave projections, atlas edges, and CLI inspection free to repeat the same
unsupported joins.

### 2. Separate selected modules, inventory membership, and navigation roots

The run context will retain both the selected module map and the normalized set of
all discovered internal module identities. Import targets are classified against
the full set:

- `selected_internal`;
- `known_inventory_boundary`;
- `external_boundary`; or
- `missing_internal`.

Selection roots decide population. Navigation roots are optional inputs to
reachability and closure metrics. Inventory scope has no implicit reachability
root; root-derived metrics are unavailable unless the caller explicitly supplied
a navigation root that the scope contract preserves as such. A report anchor used
for display must never become an analysis root.

Alternative considered: expand owner scope until all imports are present. That
would erase the bounded owner-slice contract and conflate selection with
classification.

### 3. Require an explicit join plan for every composite signal

A composite correlator will declare:

- participating evidence kinds;
- compatible populations and authority;
- the structural join predicate, such as same module, closure membership, import
  path, shared declaration identity, or configured family membership;
- aggregation semantics; and
- the bounded evidence witnesses retained in the finding.

Independent maxima are not a join. If no qualifying pair exists, the composite is
suppressed or reported as an unavailable correlation diagnostic. Composite counts
represent a documented unit; they do not sum unlike quantities merely to create
one score.

Alternative considered: keep the current score and add a disclaimer. The resulting
finding would still prioritize an evidence pair that is structurally unrelated.

### 4. Build namespace-aware lexical declaration candidates conservatively

The text indexer will maintain comment/string-safe lexical scope state sufficient
to attach namespace stack, declaration kind, modifiers, privacy/locality, source
range, and normalized declaration-block hash to supported top-level commands. It
will form a candidate fully-qualified name only when the syntax is safely
recognized.

Collision analysis will distinguish:

- same candidate name in different modules;
- exact normalized declaration-block duplicates;
- exact file-content duplicates;
- private/local or unresolved-name candidates; and
- pairs that can occur in one selected import/reachability context.

The lexical result is always a collision candidate. Lean extraction may attach a
confirmed environment identity or coexistence result separately. Ambiguous parser
state produces an unresolved row, never a guessed fully-qualified name.

Alternative considered: compare raw local names globally. That creates enormous
noise and cannot distinguish namespaces, private declarations, or repeated family
members.

### 5. Attach audit evidence before final module-role classification

Audit parsing becomes continuation-aware for supported `#check`,
`#print axioms`, and option command shapes while retaining bounded source text and
structured unparsed diagnostics. The pipeline will perform final facade/module-role
classification after declarations and audit rows are available.

Role precedence is evidence-based: every declaration-empty module with supported
audit commands receives `audit_surface`, while `command_only_audit_facade` is
added only when the existing facade predicate independently holds. Such a module
is not `pure_barrel`. Audit roles suppress generic public-API pressure unless
independent evidence supports it. Subject-to-owner links remain lexical
candidates unless the Lean backend resolves them.

Alternative considered: special-case filenames containing `Audit`. That would be
target convention masquerading as product semantics.

### 6. Keep generated-looking detection advisory and provenance authoritative

The first detector rule is the versioned
`generic-numbered-family-v1` predicate. It groups same-parent modules whose final
segment is a common nonempty prefix plus a decimal suffix, requires at least four
members, at least four-fifths numeric density, one common direct internal import
in at least four-fifths of members, and one versioned normalized declaration stem
or declaration-command skeleton in at least four-fifths of members. Required
feature totals must be known. Exact thresholds and normalization versions are
fingerprinted and rendered; predicate overrides are explicit separately
versioned profile inputs.
The supported explicit
`parent-final-segment-decimal-suffix-width-v1` grouping additionally separates
otherwise-equal families by decimal suffix spelling width, so padded and
unpadded sequences do not merge.

For each numeric partition, the analyzer counts every observed aggregate feature
key before `strongest-feature-keys-per-kind-version-v1` retains at most 12 keys
independently per feature kind and normalization version. Required import and
lexical predicate winners remain retained. Ordering is descending
distinct-member count, then feature value, then authority. The report exposes
the fixed projection version and cap plus exact visible, total, omitted, and
projection-cause coverage. This analyzer-owned cap is independent of candidate
profile and representative limits and participates in the analysis fingerprint.

Other structural evidence, including exact/near-exact source hashes and
non-numeric shape families, remains inspectable as canonical raw evidence but
does not qualify under v1; only the bounded aggregate feature rows are retained
on candidate partitions. Candidate family IDs are stable over ordering changes.

The output relation is `generated_looking_candidate`; it is not a primary
population. Configured policy remains the only project-generated provenance
authority. Target ownership means only that the file belongs to the selected
project; renderers and findings must not rename that population “handwritten.”
Candidate evidence can suggest a policy rule but cannot write or activate one.

Alternative considered: infer provenance automatically once a score crosses a
threshold. Regular handwritten tables and mechanically copied proofs make that
unsafe.

### 7. Expose the source index through ordinary inspection operations

The public CLI gains a shared inspection family for modules, declarations,
imports, audits, options, resources, and proof mechanisms. These operations read a
canonical report/source index or a fingerprint-matched cache; they do not rerun
analysis unless the ordinary command explicitly requests analysis.

Every list operation has deterministic filtering, stable cursor or offset
pagination, selected/visible/total/omitted counts, authority, and source/index
fingerprint. Exact lookup uses stable identity. Invalid filters and stale index
matches fail explicitly. Text and JSON are projections of the same selected rows.

This is one human CLI surface shared by people, scripts, editors, and models. No
consumer receives a privileged command or hidden evidence.

Alternative considered: raise the per-report declaration cap until the full
repository fits. That increases every report's size while still failing to support
targeted late-row lookup.

### 8. Treat proof mechanisms, lexical scope, and options as navigation evidence

The text index records supported tactic-command tokens and attributes in
comment/string-safe declaration ranges, along with namespace, section, variable,
`omit`, local notation/instance, `open scoped`, and export context when safely
available. Summaries aggregate by selected population, module, and candidate
family.

All `set_option` commands receive a generic lexical row. Supported resource options
add normalized values and lexical scope; other options retain bounded raw values
and option class. In this packet, normalized unlimited resource settings and
matches from an explicit fingerprinted repository policy are the only pressure
classes. Finite values without a matching policy remain navigation rows even when
they are numerically large. Distribution-derived finite thresholds are deferred.
No class implies measured cost or proof quality.

Lexical tactic occurrence is not a resolved tactic invocation, theorem dependency,
rewrite direction, simp use, or proof success. Lean-backed enrichment, when
available, remains separate.

Alternative considered: delay all mechanism visibility until Lean extraction.
That discards valuable navigation in the default text workflow and makes large
generated proof families opaque.

### 9. Make coverage a compositional report and atlas contract

Every bounded collection exposes `visible`, `total`, `omitted`, and
`completeness`, plus the population/authority to which those counts apply.
“Full” means no intentional projection omission; if an upstream analysis cap
remains, the collection is explicitly incomplete and the top-level projection
lists it.

Review projection uses deterministic stratification by evidence kind, severity,
status, population, and command/module role before stable tie-breaking. It will not
let alphabetic first-N selection erase an entire evidence class. Atlas ingestion
propagates coverage and marks exhaustive queries unavailable on incomplete source
tables unless the query is provably sound over the visible subset.

Alternative considered: teach each renderer and atlas query its own truncation
warning. Separate rules will drift and cannot compose.

### 10. Render once per immutable analysis snapshot

One analysis execution produces an immutable in-memory or file-backed result with a
source snapshot fingerprint. The ordinary CLI may request multiple file-backed
format/path outputs from that same result while allowing at most one stdout
destination. Rendering must not rediscover or reanalyze source, and ambiguous
legacy/canonical output-option mixing is rejected before analysis.

The pipeline captures a manifest of relevant source bytes and configuration.
Every source read used for evidence must match its manifest entry; a mismatch
causes restart from one new manifest or a structured
`source_changed_during_analysis` diagnostic without mixed-snapshot rows. A final
repository comparison determines whether the captured analysis still describes
current state. This contract does not claim observation of transient changes whose
bytes were never read and whose final bytes match the manifest. Drift identifies
affected completeness and prevents a stable-complete claim. All emitted formats
share analysis identity, source fingerprint, semantic counts, and drift state.

Alternative considered: invoke the CLI once per desired format. Active repositories
can change between invocations, making apparent format disagreement an input-state
disagreement.

### 11. Route integrity evidence into bounded review regions

Review-region synthesis gains regions for joined architecture policy evidence,
declaration collision candidates, audit surfaces, generated-looking candidates,
and option/resource pressure. Regions link to canonical rows and inspection
commands, state authority/nonclaims, and expose coverage. They do not duplicate
the evidence tables or create new finding taxonomies.

Alternative considered: add every row to the generic findings list. That would
turn navigation surfaces into unbounded defect claims.

### 12. Validate with portable predicates and optional live observations

Tracked fixtures cover:

- selected vs known-boundary vs genuinely missing imports;
- rootless inventory and explicit navigation-root reachability;
- joined and deliberately disjoint composite signals;
- namespace/private/multiline/duplicate declaration candidates;
- multiline audit commands and command-only role precedence;
- structurally regular generated candidates plus regular handwritten negatives;
- late-page declaration inspection and stale-fingerprint rejection;
- tactic/scope/option/resource positive and comment/string negative cases;
- stratified projection, incomplete atlas input, and multi-format parity; and
- deterministic source-drift injection.

An optional live Matrix-Factorization acceptance run records target fingerprint,
dirty state, toolchain, Ladon identity, commands, output hashes, coverage, timing,
and peak RSS. It asserts normalized predicates rather than frozen repository
cardinalities.

Alternative considered: make the live sibling tree a required regression fixture.
Its size and active dirty state are not portable CI contracts.

## Risks / Trade-offs

- **[Lexical fully-qualified names can be wrong for unsupported syntax]** →
  preserve parser status and unresolved candidates; require Lean authority for
  confirmed identity.
- **[Candidate collision and family grouping can be quadratic]** → partition by
  normalized name/stem/hash, stream bounded witnesses, and gate time/RSS on a
  generated large fixture.
- **[Conservative joins may reduce finding counts]** → treat suppression as the
  correct result when structural evidence is absent and expose correlation
  diagnostics for debugging.
- **[Role precedence may change existing text output]** → retain stable module
  identity, document old/new role mapping, and test JSON/text parity.
- **[Inspection can expose very large tables]** → require pagination, bounded text,
  deterministic filters, and no implicit full dump.
- **[Generic generated-looking rules can still flag regular handwritten code]** →
  keep the result advisory, show feature evidence, include negative fixtures, and
  never auto-promote provenance.
- **[Fingerprint rechecks add I/O]** → reuse source-index metadata where sound,
  measure overhead, and keep the correctness check mandatory for stable-snapshot
  claims.
- **[Coverage metadata expands schema and consumer work]** → add fields
  compatibly, centralize collection helpers, and reject only operations whose
  claimed exhaustiveness would be false.

## Migration Plan

1. Add shared inventory-membership, authority, typed-join, and coverage models
   behind compatibility adapters.
2. Fix owner/inventory scope semantics and composite joins before adding new
   promoted surfaces.
3. Extend the source index with namespace, declaration-block, audit-continuation,
   mechanism, scope-context, and generic option evidence under a new fingerprint
   version.
4. Reclassify audit facades and add advisory generated-family candidates without
   changing configured provenance.
5. Add inspection operations and coverage-aware atlas ingestion.
6. Introduce stratified projection, integrity review regions, immutable
   multi-render, and source-drift diagnostics.
7. Run portable gates, installed-candidate smoke tests, and optional fingerprinted
   Matrix-Factorization acceptance.

Rollback is additive at the schema boundary: new inspection routes and evidence
tables can be disabled while old report readers continue consuming existing keys.
The scope and structural-join correctness fixes must not be rolled back to known
false claims; affected findings should instead be suppressed if compatibility
rendering cannot represent the corrected evidence.

## Resolved Interface Decisions

- Inspection uses
  `ladon inspect <modules|declarations|imports|audits|options|resources|proof-mechanisms>`
  with exactly one of `--report PATH` or `--source-index PATH`, repeatable
  `--filter FIELD=VALUE`, optional `--id`, `--cursor`, and `--limit`, plus the
  established `--format` and `--output`. Supplying `--repo-root` explicitly binds
  inspection to live repository state; artifact-only mode is the default.
- Canonical multi-output analysis uses repeatable `--emit FORMAT=PATH`. Existing
  `--format` plus `--output` remains the single-output spelling. `--emit` cannot be
  mixed with that canonical pair or deprecated `--output-json`/`--output-text`;
  duplicate formats and destination paths are invalid; and at most one
  destination may be `-`. All conflicts fail before discovery or analysis.
- The captured source manifest registers every file whose bytes affect discovery,
  extraction, classification, findings, or policy: discovered Lean sources and
  every Lake/toolchain, changed-manifest, architecture/source/generated policy, or
  quoted-evidence file actually read. Normalized CLI configuration, tool identity,
  backend identity, and schema versions belong to the analysis fingerprint. The
  read registry, rather than a hard-coded filename list, is authoritative.
- Generic finite resource-pressure thresholds are deferred. This umbrella routes
  normalized unlimited settings and explicit fingerprinted policy matches only.
