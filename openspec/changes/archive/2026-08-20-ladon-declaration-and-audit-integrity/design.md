## Context

The text backend already owns useful pieces of this surface, but their current
composition loses integrity:

- `ladon.extraction` masks comments and strings and records bounded local
  declaration names, kinds, and ranges, but does not retain namespace state,
  modifiers, locality, stable declaration identities, or declaration-block
  hashes;
- the source index caches those lexical declaration rows, while module-DAG
  reporting applies an inventory-wide detail cap before later consumers can
  inspect or correlate them;
- `ladon.analysis.audit_surface` owns stable lexical `#check`,
  `#print axioms`, and resource rows, but its command patterns consume only the
  keyword line;
- module facade subtypes are computed before audit surfaces are attached, so
  command-only audit modules remain `pure_barrel`; and
- text audit subjects do not join to the complete lexical declaration inventory,
  while Lean-backed audit results correctly remain a separate authority.

This child is an integration overlay. It explicitly adopts:

- `ladon-declaration-source-evidence` as owner of declaration source rows and
  attachment fields;
- `ladon-elaborated-declaration-surface` as owner of Lean-confirmed declaration
  identity, dependency, trust, and toolchain evidence;
- `ladon-lean-audit-command-surface` as owner of audit command, resource, result,
  and nonclaim rows;
- `ladon-common-layer-and-facade-quality` as owner of facade subtype and
  implementation/facade ranking vocabulary; and
- `ladon-scope-and-join-integrity` as owner of selected-context joins,
  reachability applicability, and structural witness requirements.

The child extends those canonical rows and sequencing; it does not create
parallel declaration, audit, graph, or facade engines. All default text results
remain lexical candidates. No Matrix-Factorization build was used to establish
the motivating collisions or audit subjects.

Per the umbrella ledger, implementation starts after
`ladon-report-coverage-and-snapshot-integrity#coverage-foundation` and
`ladon-scope-and-join-integrity` have passed their portable exits.

## Goals / Non-Goals

**Goals:**

- Retain enough safe lexical scope state to form namespace-aware declaration
  identity candidates.
- Group exact-name, declaration-block, and source-file duplicate candidates with
  bounded canonical evidence.
- Route co-reachable collision pressure only when the scope/join owner supplies
  a structural module-graph witness.
- Parse supported multiline audit subjects while preserving stable command
  identity, diagnostics, and comment/string safety.
- Classify module roles after audit evidence exists.
- Attach unique lexical audit-subject owner candidates without upgrading Lean
  result status or authority.
- Preserve deterministic identities, coverage, and cache invalidation at large
  inventory scale.

**Non-Goals:**

- No Python implementation of Lean name resolution, namespace semantics, or
  elaboration.
- No claim that a lexical collision causes a compile error or that duplicate
  bytes represent equal theorems or proofs.
- No change to Lean helper protocols, trust-footprint semantics, finding
  taxonomy, or configured population provenance.
- No filename-based `Audit` convention, Matrix-Factorization theorem prefix, or
  repository-specific threshold.
- No required target build, sibling checkout, network access, or mutable live
  repository in CI.

## Decisions

### 1. Extend canonical source declarations under a versioned index schema

`LeanTextDeclaration` and its source-index representation will gain bounded
fields for:

- stable lexical row identity;
- namespace and section stacks;
- supported modifiers and privacy/locality;
- candidate fully qualified name plus parsed/unresolved status;
- normalized declaration-block hash and normalization version; and
- existing source range, kind, authority, confidence, and nonclaim.

The scope tracker consumes the same offset-preserving masked source used by the
current declaration scanner. Namespace commands change the candidate name stack;
sections remain context but do not become namespace segments. Ambiguous or
unsupported transitions mark candidate naming unresolved from that point until a
safe recovery boundary; they never synthesize a name. The initial recovery rule
accepts only an unambiguous `end` that matches a known open lexical frame.
Unmatched or unsupported scope syntax keeps candidate naming unresolved through
the remainder of the file.

The source-index schema and fingerprint version will change, so older cached
entries fail closed and rebuild. Compatibility decoders may read old rows as
scope-unavailable, but they cannot report namespace-aware completeness.

Alternative considered: compute fully qualified candidates only while rendering.
That would repeat parsing, bypass cache identity, and leave collision and audit
joins with different source authority.

### 2. Partition collision evidence instead of comparing every pair

Collision analysis indexes eligible non-private/non-local rows by safely derived
candidate fully qualified name. Exact declaration-block duplicates are indexed by
normalization-version plus hash, and exact file duplicates reuse source-index
content hashes. Each partition retains total membership and bounded deterministic
representatives.

The initial declaration-block normalizer removes comment and whitespace trivia
only. It preserves identifiers, literals, attributes, modifiers, and command
tokens. Any later token-level normalization requires a new explicit version and
separate evidence kind.

Equal basenames in different candidate namespaces never enter the same name
partition. Private/local rows remain inspectable but are excluded from public
cross-file collision promotion. Shape and hash groups remain separate from name
groups because they answer different questions.

Alternative considered: compare every raw local name or every declaration pair.
That reproduces the noisy MF lexical census and creates quadratic time and memory
pressure.

### 3. Delegate coexistence to typed scope-and-join witnesses

Inventory collision candidates are raw lexical navigation. A co-reachable
collision registration requires a canonical witness supplied through
`ladon-scope-and-join-integrity`, such as both module members occurring in one
selected closure or being imported by one selected facade. The producer row
stores:

- canonical declaration member references;
- graph member/path references;
- selected population and scope fingerprint;
- component authorities (`lexical_text` and `module_import_graph`);
- derived authority no stronger than those components; and
- visible/total/omitted/completeness state.

If graph evidence is absent, partial, or projected away, coexistence is
unavailable and no pressure row is promoted.

This child stops at the canonical producer row and inspection action key. It
does not emit the complete review-region object; the report child's
`snapshot-and-region-integration` milestone consumes these rows through the
existing review-region owner.

Alternative considered: promote every repository-wide duplicate candidate. That
would turn lexical inventory equality into an unsupported statement that both
declarations enter one Lean environment.

### 4. Make the existing audit scanner continuation-aware

The existing audit scanner remains the single audit-command owner. Its bounded
parser will consume a safe continuation only for documented bare-subject forms:

- `#check` followed by a supported bare declaration subject; and
- `#print axioms` followed by a supported bare declaration subject.

The command range spans keyword through subject, and stable identity continues to
use normalized module, command kind, start anchor, and complete untruncated
subject identity. Comment/string masking remains offset preserving. Unsupported
expressions retain an unparsed row and diagnostic rather than disappearing or
being guessed.

Alternative considered: concatenate arbitrary following lines. That risks
capturing the next command or declaration and makes command identity unstable.

### 5. Extract audit evidence before final module-role classification

The pipeline will invoke the existing audit extraction once per indexed module
before final module inventory classification. Canonical audit surfaces will be
retained in or referenced from the source-index entry so later calibration does
not reread and rescan the file.

The facade owner will receive audit facts as classification inputs:

1. configured/known generated aggregation retains its owning subtype;
2. every declaration-empty module with supported audit commands receives
   `audit_surface`;
3. it receives `command_only_audit_facade` only when independent import or
   public-aggregation evidence satisfies the existing facade predicate;
4. an audit facade is not simultaneously `pure_barrel`;
5. an isolated command-only audit surface without facade evidence is neither
   `command_only_audit_facade` nor `pure_barrel`;
6. modules with declarations and audit commands retain both surfaces but are not
   command-only; and
7. remaining modules use existing facade rules unchanged.

Readiness synthesis suppresses generic public-facade pressure for a command-only
audit facade unless an independent owning rule provides qualifying non-audit
evidence.

Alternative considered: infer the role from an `Audit` filename token. That is a
repository convention rather than source evidence.

### 6. Keep lexical owner candidates separate from Lean audit results

For a safely parsed bare audit subject, the overlay performs exact candidate-FQN
lookup in the fingerprint-matched lexical source index:

- one match produces a lexical referenced-owner candidate;
- zero matches remains unresolved;
- multiple matches remains ambiguous with bounded candidates; and
- no basename, path-order, or fan-in fallback is allowed.

Candidate identity, owner, status, and authority use fields distinct from the
existing Lean-resolved declaration/result fields. The text backend keeps
`resultStatus=unavailable`. Existing Lean enrichment may attach a
`lean_environment` result to the stable command row and does not erase the
lexical candidate.

Alternative considered: populate existing resolved-owner fields from a unique
text match. Their present consumers treat those fields as stronger resolution
evidence, so that would silently upgrade authority.

### 7. Centralize coverage and canonical evidence links

All new name-collision, duplicate-block, duplicate-file, ambiguous-owner, and
coexistence collections use the shared coverage contract:

- `visible`, exact or explicitly unknown `total`/`omitted`, `totalKnown`, observed
  lower bound, and `completeness`;
- selected population and scope;
- source-index and analysis fingerprints;
- canonical member references; and
- deterministic stable ordering.

Renderers and report-owned review-region synthesis link to canonical groups
rather than copying full payloads. A dangling required reference makes the
producer registration unavailable.

The additive rows enter canonical report v3 sections. Older v2 compatibility
serialization may report aggregate availability or omission, but it does not
overload resolved-owner fields or duplicate the new payload. The source-index
schema bump is independent and always invalidates incompatible cached rows.

Alternative considered: give each renderer its own first-N list. That caused the
current audit projection to erase entire evidence classes while still showing
global totals.

### 8. Gate the text contract without target execution

Required tests use tracked fixtures with positive and deliberate negative cases.
They monkeypatch subprocess creation so Lake, Lean, version control, target
initializers, and builds are fatal. Fake in-process Lean payloads may test
authority joins; the existing elaborated-surface owner retains its separate
non-skippable pinned-Lean acceptance.

The generated large-inventory gate exercises partitioning, cache invalidation,
coverage bounds, and deterministic output under the existing resource ceilings.
Optional MF observations remain read-only and record source/analyzer fingerprints
instead of fixed counts.

Alternative considered: require the live MF checkout as the regression fixture.
Its active dirty state and moving cardinalities cannot be portable test authority.

## Risks / Trade-offs

- **[Lexical scope recovery accepts unsupported Lean syntax]** → Mark candidate
  naming unresolved at the ambiguity boundary and require Lean authority for
  confirmed identity.
- **[Private/local parsing is incomplete]** → Exclude uncertain visibility from
  public collision promotion while retaining the raw row and reason.
- **[Normalized hashes hide meaningful differences]** → Version the normalizer,
  expose exact and normalized hashes separately, and make no semantic-equality
  claim.
- **[Continuation parsing consumes too much source]** → Support only bounded bare
  subjects and preserve every unsupported case as unparsed.
- **[Role ordering changes existing outputs]** → Keep stable module identity,
  document old/new subtype mapping, and gate JSON/text parity.
- **[Collision groups become large]** → Partition by indexed keys, bound
  representatives, and preserve complete counts and late lookup.
- **[Schema changes invalidate large caches]** → Bump the fingerprint version and
  fail closed rather than interpreting old rows as scope-aware.

## Migration Plan

1. Add the extended lexical declaration and cached audit shapes with new schema
   and fingerprint versions plus old-row unavailable adapters.
2. Implement namespace/section tracking, modifier/locality capture, and
   declaration-block normalization in the existing masked extraction path.
3. Add keyed collision/duplicate indexes and canonical coverage-bearing rows.
4. Make the existing audit parser continuation-aware and add exact lexical owner
   candidate joins.
5. Reorder final role classification to consume cached audit evidence and update
   readiness/review registration.
6. Update schemas, renderers, inspection adapters, and cache invalidation tests.
7. Run focused portable, installed, large-inventory, quality, and strict
   OpenSpec gates; record any live MF observation separately.

Rollback may disable the new derived collision and role projections while keeping
the additive cached evidence. It must not restore known false Lean authority or
classify command-only audit modules as generic API pressure when audit evidence
is available.

## Open Questions

None. The initial recovery, normalization, and report compatibility boundaries
are fixed above; broader parsing or normalization requires a later change.
