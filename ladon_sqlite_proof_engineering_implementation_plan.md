# Ladon SQLite Proof-Engineering Implementation Plan

## 1. Decision and scope

Ladon will retain SQLite as its canonical persistent store. No specialized graph database will be introduced.

The proof-engineering system will have three explicit layers:

1. **SQLite candidate and evidence index**
   - declaration names, modules, packages, source locations, scopes, aliases, binders, direct dependencies, structures, fields, fingerprints, search keys, coverage, and freshness;
   - fast deterministic shortlisting and reverse-consumer queries;
   - atomic publication and disposable rebuild semantics.

2. **Lean semantic verifier**
   - elaborates type patterns and goals;
   - checks theorem applicability with Lean metavariables, definitional equality, type-class synthesis, coercions, and explicit adapters;
   - returns substitutions, unresolved parameters, residual proof goals, and exact failure evidence;
   - remains the only authority for semantic applicability.

3. **Bounded Ladon planner and graph layer**
   - performs deterministic bounded traversal over already retrieved SQLite rows;
   - builds constructor coverage matrices and proof-route cards;
   - searches AND/OR proof states only through Lean-verified transitions;
   - never upgrades a structural or lexical candidate into a proof fact.

The first release covered by this plan must implement all three P0 areas from the Lean Proof-Engineering Discovery TODO:

- type-directed declaration search;
- premise and goal difference analysis;
- declaration consumers and constructor coverage.

It will also implement the previously identified correctness and performance fixes, including name normalization, verified freshness, duplicate traversal removal, N+1 query removal, a bounded graph module, a better dominator algorithm, and lower CLI startup overhead.

## 2. Non-goals

The initial P0 implementation will not:

- attempt to replace Lean's elaborator, unifier, simplifier, or type-class system in Python or SQL;
- treat pretty-printed type equality or expression fingerprints as semantic equality;
- search arbitrary unbounded proof spaces;
- claim that a suggested route compiles unless Lean has checked every transition or a generated scratch example has been replayed;
- silently run Lean during the existing lexical index build or lexical query commands;
- mutate the published proof-search database during read-only queries;
- promise source-level support for partially elaborated editor buffers before the later goal-capture phase.

## 3. Architectural invariants

Every implementation PR should preserve these invariants.

### 3.1 Authority is explicit

Use separate authority values throughout:

- `lexical_text`
- `lake_layout`
- `lean_environment`
- `lean_verified_application`
- `registered_adapter`
- `repository_semantic_registry`
- `heuristic_classification`
- `unavailable`

A result may combine evidence from several authorities, but each field must retain its owner. A lexical or structural shortlist is never labelled as a Lean match.

### 3.2 Complete internal index, bounded external result

The persistent semantic index should store complete binders, direct dependencies, structure fields, and constructor relationships whenever Lean successfully supplies them. User-facing query limits remain finite and explicit.

Truncation intended for report rendering must not silently truncate the internal semantic relation. If a safety cap is reached during extraction, the corresponding collection must be marked `partial`, include the observed count and cap, and be ineligible for completeness claims.

### 3.3 Atomic publication remains the default

Semantic extraction may be incremental, but publication remains generation-based:

1. capture repository, configuration, toolchain, helper, and cache identities;
2. reuse sound per-module extraction artifacts;
3. assemble a fresh temporary SQLite database;
4. run schema, integrity, foreign-key, coverage, and query-plan checks;
5. run `PRAGMA optimize` after population;
6. atomically replace the previous generation.

No interrupted semantic build may damage the previous database.

### 3.4 Semantic commands are explicit Lean execution

The current lexical index and lexical queries remain safe, no-Lean operations. Commands that load target environments must be visibly separate, document initializer risk, accept finite deadlines, and use the existing process supervisor.

### 3.5 Every expensive operation is bounded

All SQL results, candidate shortlists, Lean checks, residual-premise searches, route expansions, route depth, graph nodes, graph edges, output rows, and output bytes have explicit caps recorded in JSON.

### 3.6 Public contracts are versioned independently from private tables

The SQLite schema may change through disposable rebuilds. CLI result schemas must be versioned and retained through deliberate compatibility adapters.

## 4. Target public CLI

Keep the existing commands:

```text
ladon proof-search index build
ladon proof-search index status
ladon proof-search index query
ladon proof-search evidence ...
```

Add the following commands:

```text
ladon proof-search search name
ladon proof-search search type
ladon proof-search explain
ladon proof-search consumers
ladon proof-search constructor coverage
```

### 4.1 Semantic index build

```bash
ladon proof-search index build \
  --repo-root /path/to/project \
  --mode semantic \
  --lean-timeout 120 \
  --format json --output -
```

Modes:

- `lexical`: existing behaviour; never runs Lean;
- `semantic`: requires compiled state where appropriate and populates Lean-owned relations;
- `hybrid`: semantic where available, lexical fallback elsewhere, with per-module coverage.

Do not change the existing build's security behaviour silently. During the first compatibility period, omission of `--mode` continues to mean `lexical`.

### 4.2 Name search

```bash
ladon proof-search search name \
  --repo-root /path/to/project \
  --text fixedIndexPathExpression \
  --scope closure --root Project.Owner \
  --query-mode all \
  --format json --output -
```

Required semantics:

- exact names are case-insensitive by default;
- exact folded-name matches are always unioned into the result before FTS ranking;
- name segmentation is identical at index and query time;
- query mode is explicit: `all`, `any`, or `phrase`;
- exclusions use repeatable `--exclude`;
- exact-name refinement is monotone;
- project-owned declarations outrank dependency declarations when semantic quality is otherwise equal;
- result collection key is `results`.

`index query` remains a compatibility alias for `search name` during one result-contract transition.

### 4.3 Type search

```bash
ladon proof-search search type \
  --repo-root /path/to/project \
  --module Project.ActiveOwner \
  --pattern 'Integrable (fun state => integral (releaseLaw _ state) _) _' \
  --scope closure \
  --limit 20 \
  --format json --output -
```

Initial pattern syntax uses ordinary Lean terms with `_` as an anonymous wildcard. Named holes may be added in a later compatible protocol version. The result still reports substitutions for the candidate declaration's binders.

Useful options:

```text
--module MODULE                 environment and scope anchor
--pattern TEXT                  Lean type or proposition pattern
--pattern-file PATH             avoids shell quoting for large patterns
--assume TEXT                   repeatable local assumption type
--scope module|imports|closure|project|dependency|repository
--package PACKAGE               repeatable package filter
--namespace PREFIX              repeatable namespace filter
--candidate-cap N               maximum Lean checks after SQL shortlisting
--limit N                       maximum returned verified candidates
--match-pass direct|symmetry|adapters|all
--freshness verify|stored       default verify for semantic commands
```

### 4.4 Premise and goal explanation

```bash
ladon proof-search explain \
  --repo-root /path/to/project \
  --module Project.ActiveOwner \
  --goal 'TargetType ...' \
  --candidate Project.Authority.candidateTheorem \
  --suggest-premises 5 \
  --format json --output -
```

The command must return residual premises even when the theorem does not close the goal. It must distinguish conclusion mismatch from successful application with unresolved premises.

### 4.5 Reverse consumers

```bash
ladon proof-search consumers \
  --repo-root /path/to/project \
  --declaration Project.PrimitivePathMoments \
  --dependency-kind all \
  --ownership project \
  --format json --output -
```

It returns type consumers and value consumers separately, with source locations and completeness state.

### 4.6 Constructor coverage

```bash
ladon proof-search constructor coverage \
  --repo-root /path/to/project \
  --module Project.ActiveOwner \
  --structure Project.PathBounds \
  --assume '0 < horizon' \
  --format json --output -
```

The first P0 version supports a structure plus explicit environment and assumptions. Later goal capture can feed an exact in-editor constructor goal into the same service without changing the coverage engine.

## 5. Result contracts

Introduce these schemas:

- `ladon-proof-search-name-result-v2`
- `ladon-proof-search-type-result-v1`
- `ladon-proof-difference-result-v1`
- `ladon-proof-consumers-result-v1`
- `ladon-constructor-coverage-result-v1`
- `ladon-proof-route-card-v1`

All search-style commands use `results` as the collection key. During compatibility, `index query` may also expose `rows` with a deprecation field, but new examples and code use only `results`.

### 5.1 Type-search result shape

```json
{
  "schema": "ladon-proof-search-type-result-v1",
  "operation": "type-search",
  "status": "available",
  "freshness": {
    "status": "verified-fresh",
    "indexGeneration": "...",
    "workerGeneration": "..."
  },
  "query": {
    "module": "Project.ActiveOwner",
    "patternText": "...",
    "scope": "closure"
  },
  "results": [
    {
      "declaration": {
        "name": "Project.Authority.someTheorem",
        "module": "Project.Authority",
        "path": "Project/Authority.lean",
        "line": 42,
        "renderedType": "..."
      },
      "verification": {
        "status": "verified",
        "authority": "lean_verified_application",
        "matchClass": "definitional-reducible",
        "substitutions": [],
        "residualPremises": [],
        "unresolvedInstances": [],
        "adapters": []
      },
      "ranking": {
        "vector": [0, 0, 0, 1, "Project.Authority.someTheorem"],
        "explanation": []
      }
    }
  ],
  "coverage": {},
  "truncated": false,
  "nonclaims": []
}
```

### 5.2 Difference result shape

The difference result includes:

- the elaborated goal;
- the candidate's elaborated type;
- conclusion-match attempts and transparency modes;
- candidate binder substitutions;
- residual premises;
- unresolved type-class or term metavariables;
- classified mismatches;
- one-level discharge suggestions for each residual premise;
- a proof-route card;
- freshness, authority, bounds, omissions, and nonclaims.

## 6. Package and module layout

Keep modules focused to satisfy Ladon's quality gates.

```text
src/ladon/
  entrypoint.py
  proof_search_contracts.py
  proof_search_scope.py
  proof_search_name_query.py
  proof_search_semantic_index.py
  proof_search_type_query.py
  proof_search_difference.py
  proof_search_consumers.py
  proof_search_constructor.py
  proof_search_ranking.py
  proof_search_route_cards.py
  semantic_registry.py
  lean_semantic_protocol.py
  lean_semantic_runtime.py
  bounded_graph.py
  dominators.py
  lean/
    ladon_semantic_helper.lean
    ladon_semantic_index_helper.lean
```

Refactor rather than duplicating:

- move current scope expansion from `proof_search_query.py` into `proof_search_scope.py`;
- keep `proof_search_query.py` as a temporary compatibility wrapper;
- reuse process supervision, cache primitives, path validation, output writing, and generation identity utilities;
- reuse current declaration surface normalization only where its bounded report model is appropriate;
- do not make the report-oriented bounded dataclasses the only representation of complete index extraction.

## 7. SQLite schema v4

Bump the private schema and generation identifiers. Old databases are reported as incompatible and rebuilt; do not implement an in-place migration for disposable index state.

Retain current ProofIR and theorem-lineage relations unless a change is required. Extend the declaration/index portion as follows.

### 7.1 Existing declaration table additions

Add or normalize these columns:

```text
name_casefold
name_segments
ownership                 project|dependency|generated|source-only|unknown
doc_text
rendered_type
rendered_type_fingerprint
conclusion_text
conclusion_fingerprint
conclusion_head
conclusion_arity
is_proposition
semantic_status
semantic_reason
semantic_helper_version
semantic_lean_version
```

Do not store unbounded pretty-printed text. Store bounded navigation text plus structural fingerprints and retrieve authoritative current types from Lean during semantic verification.

### 7.2 Symbol dictionary

Direct dependency edges can be numerous, so avoid repeating long Lean names in every edge.

```sql
CREATE TABLE symbols (
    symbol_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    declaration_id TEXT,
    owner_module TEXT,
    kind TEXT,
    ownership TEXT NOT NULL,
    FOREIGN KEY(declaration_id) REFERENCES declarations(id) ON DELETE SET NULL
);
```

Every dependency target gets a symbol row, even when its declaration is not present in the current index. This preserves honest external-frontier evidence without raw-name duplication in edge indexes.

### 7.3 Complete declaration dependencies

Replace the text-heavy semantic edge representation with:

```sql
CREATE TABLE declaration_dependencies (
    source_declaration_id TEXT NOT NULL,
    target_symbol_id INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('type', 'value')),
    authority TEXT NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY(source_declaration_id, target_symbol_id, kind, authority),
    FOREIGN KEY(source_declaration_id) REFERENCES declarations(id) ON DELETE CASCADE,
    FOREIGN KEY(target_symbol_id) REFERENCES symbols(symbol_id) ON DELETE CASCADE
) WITHOUT ROWID;
```

Required indexes:

```text
(source_declaration_id, kind, target_symbol_id)
(target_symbol_id, kind, source_declaration_id)
```

### 7.4 Declaration shapes

```sql
CREATE TABLE declaration_shapes (
    declaration_id TEXT NOT NULL,
    role TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    key_version TEXT NOT NULL,
    head_symbol_id INTEGER,
    arity INTEGER,
    shape_hash TEXT NOT NULL,
    coarse_key BLOB NOT NULL,
    authority TEXT NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY(declaration_id, role, ordinal, key_version),
    FOREIGN KEY(declaration_id) REFERENCES declarations(id) ON DELETE CASCADE,
    FOREIGN KEY(head_symbol_id) REFERENCES symbols(symbol_id) ON DELETE SET NULL
) WITHOUT ROWID;
```

Roles:

- `full_type`
- `conclusion`
- `premise`
- `rewrite_lhs`
- `rewrite_rhs`
- `structure_field`

Fingerprints and keys are candidate-shortlisting evidence, not equality claims.

### 7.5 Complete binders

Extend `binders` with:

```text
type_fingerprint
type_head_symbol_id
is_instance
is_implicit
status
reason
authority
```

Store every leading binder supplied by Lean. User-facing limits apply only when rendering results.

### 7.6 Structures, constructors, and fields

Extend `structures`:

```text
constructor_symbol_id
parameter_count
parent_structure_count
status
reason
```

Extend `structure_fields`:

```text
projection_symbol_id
field_type_text
field_type_fingerprint
field_head_symbol_id
is_proposition
is_inherited
status
reason
authority
```

Add a constructor-to-field relation only if required for multiple constructors or inductive generality. For ordinary Lean structures, the structure and projection rows are sufficient.

### 7.7 Semantic module state

```sql
CREATE TABLE module_semantic_state (
    module TEXT PRIMARY KEY,
    source_sha256 TEXT NOT NULL,
    compiled_sha256 TEXT,
    import_fingerprint TEXT NOT NULL,
    declaration_surface_fingerprint TEXT NOT NULL,
    helper_identity TEXT NOT NULL,
    lean_identity TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT,
    declaration_count INTEGER NOT NULL,
    dependency_count INTEGER NOT NULL,
    field_count INTEGER NOT NULL,
    FOREIGN KEY(module) REFERENCES modules(name) ON DELETE CASCADE
);
```

### 7.8 FTS and exact-name indexes

Keep an ordinary B-tree index on `name_casefold` for exact lookup. Build FTS over pre-normalized columns:

```text
candidate_name
name_segments
namespace
module
package
doc_text
rendered_type
conclusion_text
```

The same `semantic_name_segments_v1` function must generate both indexed segments and query segments. Do not rely on FTS tokenization to split camel case.

### 7.9 Optional mutable route-history database

Do not mutate the canonical published index from interactive queries. If rejected-route memory is added, use a separate SQLite file:

```text
.ladon/index/proof-search-history.sqlite
```

Key every row by:

- index generation;
- Lean worker generation;
- goal fingerprint;
- local-context fingerprint;
- candidate name;
- adapter-registry fingerprint;
- matching-policy fingerprint.

Use WAL mode for this mutable sidecar. It is optional and comes after the P0 read-only route-card output.

## 8. Lean semantic protocols

Create a separate semantic protocol instead of overloading the existing extraction batch contract.

### 8.1 Protocol version

```text
ladon-lean-semantic-v1
```

Operations:

- `extract-modules`
- `elaborate-pattern`
- `check-candidates`
- `inspect-structure`
- `instantiate-constructor`
- `verify-route`

### 8.2 Transport

Use framed NDJSON with request IDs. Large extraction operations should emit chunked rows rather than one enormous module object:

```text
module-start
declaration
declaration-binder
declaration-dependency
structure
structure-field
module-end
summary
```

The Python collector validates:

- protocol version;
- operation;
- request ID;
- module identity;
- frame order;
- terminal counts;
- duplicate rows;
- completeness status.

Malformed or interrupted streams retain validated prefixes as partial evidence, but semantic index publication fails unless the requested completeness policy permits fallback.

### 8.3 Expression normalization

Implement versioned Lean-side expression encoders.

`exact_expr_fingerprint_v1`:

- alpha-normalizes binder names;
- encodes constants, applications, forall, lambda, let, projection, literal, sort, bound variables, and universe levels under a declared policy;
- does not pretty-print and reparse;
- does not imply definitional equality.

`search_shape_key_v1`:

- opens leading forall binders;
- indexes the conclusion separately;
- records head constant and arity;
- treats proof and selected instance arguments as coarse wildcards;
- optionally records reducible-head normalization;
- produces a compact key suitable for SQLite shortlisting.

Every result states the key version.

### 8.4 Module ownership

When extracting a source file or loaded environment, emit only declarations owned by the requested module, plus explicit external symbol references. Do not repeatedly emit the entire imported environment for every module.

### 8.5 Semantic query verification

For each candidate:

1. obtain the current `ConstantInfo` from the loaded Lean environment;
2. open candidate binders with fresh metavariables;
3. elaborate the user's pattern or goal in the requested module context;
4. attempt the configured match passes;
5. synthesize instances under finite heartbeats and recursion limits;
6. instantiate assigned metavariables;
7. return candidate-binder substitutions;
8. return unassigned proof metavariables as residual premises;
9. return unresolved instance and term metavariables separately;
10. return the exact match pass and authority.

All candidates for one query are checked in one helper invocation.

## 9. Matching passes and deterministic ranking

### 9.1 Match passes

Run explicit passes in this order:

1. `syntactic`
   - instantiated expressions are structurally identical after alpha normalization.

2. `definitional-reducible`
   - Lean `isDefEq` under reducible transparency.

3. `symmetry`
   - for `Eq` or `Iff`, retry with the candidate conclusion or target orientation reversed.

4. `definitional-semi`
   - optional, bounded, and separately labelled; never merged with the reducible result.

5. `registered-adapter`
   - apply one explicitly registered adapter theorem, then re-run direct matching.

P0 requires direct, reducible, symmetry, and one-step registered adapters. Multi-step adapter search comes after the direct P0 path is stable.

### 9.2 Ranking vector

Use a lexicographic vector rather than a single opaque score:

```text
match_class_cost
residual_proof_goal_count
unresolved_instance_count
unresolved_term_metavariable_count
adapter_count
import_distance
ownership_cost
namespace_distance
name_match_cost
fully_qualified_name
```

Suggested costs:

```text
syntactic                 0
definitional-reducible    1
symmetry                  2
definitional-semi         3
registered-adapter        4 + adapter cost
```

The JSON result includes the vector and a human-readable explanation. Tie-breaking by fully qualified name makes results deterministic.

## 10. Type-directed declaration search algorithm

Implement `search type` as this pipeline.

### 10.1 Resolve and verify scope

- validate the requested module against the index;
- compute module/import/closure scope from indexed module edges;
- preserve omissions and source-only modules;
- verify that the semantic index and Lean environment generation agree;
- fail closed on stale semantic data unless the user explicitly requests stored-only candidate output.

### 10.2 Elaborate the pattern

The Lean helper elaborates the pattern once in the requested module environment. `_` creates fresh pattern metavariables. Repeatable `--assume` values become local proof hypotheses.

Return:

- rendered elaborated pattern;
- exact fingerprint;
- search shape key;
- head constant and arity;
- pattern metavariables;
- environment identity.

### 10.3 SQLite shortlist

Combine candidates from these buckets in order:

1. exact conclusion fingerprint;
2. same conclusion head and arity;
3. compatible shape-key prefix;
4. overlapping conclusion constants;
5. semantic FTS fallback.

Apply scope and ownership filters in SQL before the candidate cap. Deduplicate by declaration ID. Record the matched shortlist bucket for diagnostics, but do not expose it as semantic authority.

### 10.4 Batch Lean verification

Send the elaborated query and all shortlisted names in one `check-candidates` request. A candidate that disappeared from the current environment is returned as stale/missing evidence, not silently dropped.

### 10.5 Render and rank

Return only verified applications by default. An optional diagnostic mode can include rejected shortlist candidates with concise reasons and caps.

### 10.6 Type-search definition of done

- wildcard patterns work;
- substitutions are reported;
- exact, reducible, symmetry, and one-step adapter matches are distinct;
- owner module, source location, rendered type, scope, and import availability are present;
- semantic commands do not rebuild the repository;
- one query performs at most one pattern elaboration and one batched candidate-verification invocation;
- warm SQLite shortlisting is a small fraction of end-to-end latency;
- end-to-end results normally satisfy the TODO's “few seconds” interactive objective on the large reference repository.

## 11. Premise and goal difference analysis

### 11.1 Candidate application result

Even when the candidate does not close the goal, return:

- which candidate binders were assigned;
- which local assumptions discharged binders;
- residual proof premises;
- unresolved type-class goals;
- unresolved non-proof parameters;
- whether the conclusion matched;
- which pass matched;
- any adapter used.

### 11.2 Structural mismatch analysis

When the conclusion does not match, produce a bounded expression-difference tree after each attempted normalization level.

Generic classifications:

- `head_constant_mismatch`
- `arity_mismatch`
- `equality_orientation`
- `definitionally_equal_after_unfolding`
- `coercion_boundary`
- `projection_boundary`
- `unresolved_instance`
- `unresolved_parameter`
- `missing_premise`
- `unclassified_expression_difference`

Do not invent a semantic explanation when only a structural mismatch is known.

### 11.3 Semantic classifier registry

Implement a versioned registry with two sources:

1. built-in generic Lean/Mathlib categories;
2. repository-provided JSON configuration.

Built-in categories may cover:

- `StronglyMeasurable` to `AEStronglyMeasurable` and reverse direction labels;
- equality and `Iff` orientation;
- map/pushforward direction;
- common coercion and projection boundaries;
- arithmetic normalization adapters that are verified through explicit theorems.

Repository configuration covers:

- physical versus normalized representations;
- raw versus centered quantities;
- fixed-index versus finite-window versus unbounded-family boundaries;
- repository-specific semantic aliases;
- designated adapter theorem families.

Every registry classification names its rule ID and authority.

### 11.4 Suggest declarations for residual premises

For each residual proof premise:

1. derive a shape key;
2. retrieve a bounded SQLite shortlist;
3. batch all premise/candidate pairs into one second Lean request;
4. return the top verified candidates per premise;
5. stop after one level in P0.

The multi-step planner later composes these transitions.

### 11.5 Stronger and boundary classifications

Use precise labels:

- `directly_applicable`
- `applicable_with_residual_premises`
- `candidate_conclusion_stronger_via_adapter`
- `candidate_requires_stronger_premise`
- `different_index_boundary`
- `different_representation_boundary`
- `not_applicable`

Avoid the ambiguous statement “the theorem is stronger” without indicating whether the stronger part is the conclusion, the premises, or a registered representation relation.

### 11.6 Proof-route card

Every `explain` result contains a route card with:

- goal fingerprint;
- module and local-context fingerprint;
- index and worker generations;
- candidate;
- substitutions;
- match pass;
- adapters;
- residual goals;
- discharge suggestions;
- accepted/rejected status;
- rejection reason;
- source anchors;
- bounds and omissions;
- replay status, initially `not-replayed`.

## 12. Declaration consumers

### 12.1 Extraction

Populate complete type and value dependency edges from Lean. The helper's current report caps must not determine index completeness.

For each declaration, retain:

- source declaration ID;
- target symbol ID;
- dependency kind `type` or `value`;
- target owner module when known;
- target ownership;
- authority and completeness status.

### 12.2 Query

The reverse query is a direct indexed lookup on `target_symbol_id` and then joins source declarations.

Return:

- consumer name and kind;
- source location;
- type/value dependency kind;
- project/dependency ownership;
- compiler-generated status;
- scope reason;
- completeness state.

### 12.3 Definition of done

- a declaration's immediate project-owned consumers are available without Lean execution;
- type-only and value/proof-body consumers are distinguishable;
- absence is reported only when dependency coverage is complete;
- partial modules produce omission evidence rather than a false empty result.

## 13. Constructor coverage

### 13.1 Structure extraction

The Lean helper extracts:

- structure name;
- constructor name;
- parameters;
- fields in declaration order;
- projection names;
- dependent field types;
- inherited fields;
- source locations when available.

### 13.2 Instantiate field goals

For a generic structure request, instantiate parameters from explicit command arguments and assumptions. For a later captured constructor goal, the goal-capture layer supplies exact local context and already assigned parameters.

The helper returns one field-goal record per unresolved constructor field.

### 13.3 Match fields

Run the type-search pipeline for each field, batching SQL shortlists and Lean checks across all fields.

Field status values:

- `supplied_in_scope`
- `supplied_with_residual_premises`
- `supplied_under_stronger_hypotheses`
- `supplied_at_restricted_index_boundary`
- `unmatched`
- `unavailable`

### 13.4 Quantitative versus adapter classification

Use registry-backed classification where possible. A conservative heuristic fallback may classify:

- inequalities, norm bounds, finite sums, and numerical estimates as `quantitative`;
- measurability, integrability, almost-everywhere transport, and measure maps as `measure_theoretic_adapter`.

Heuristic rows must say `heuristic_classification`; they cannot drive correctness-sensitive decisions without review.

### 13.5 Certificate leakage

Report three forms separately:

1. `equivalent_field_input`
   - a constructor/helper binder type is Lean-definitionally equal to the field type it claims to derive.

2. `direct_projection_dependency`
   - the proposed supplying declaration's value dependencies include the target field projection.

3. `alias_projection_dependency`
   - the dependency is revealed only after a registered semantic alias or reducible unfolding.

Each leakage finding includes the exact binder or dependency and Lean verification status.

### 13.6 Coverage output

The result includes:

- structure and constructor identity;
- instantiated parameters;
- one row per field;
- candidate matches and residual premises;
- classification and authority;
- leakage findings;
- summary counts;
- freshness and coverage;
- a route card per selected field candidate.

## 14. Bounded AND/OR proof planner

This follows P0 direct matching and one-level premise suggestions. It is part of the broader plan because it is the correct implementation of “shortest route.”

### 14.1 State model

```text
State = canonical multiset of unresolved goal fingerprints
```

### 14.2 Transition

```text
Transition = choose one goal + apply one Lean-verified candidate + replace it with residual premises
```

A theorem application is an AND transition because all residual premises must eventually be discharged. Competing theorems are OR alternatives.

### 14.3 Search

Use bounded best-first search with a deterministic cost vector:

```text
verified match-class cost
number of unresolved goals
adapter cost
sum of residual-goal structural sizes
unresolved instance count
import distance
ownership cost
route depth
stable route identity
```

Caps:

- maximum expanded states;
- maximum candidate checks per goal;
- maximum route depth;
- maximum unresolved goals per state;
- maximum Lean verification requests;
- maximum output routes and bytes.

### 14.4 Verification

Every transition comes from the Lean semantic verifier. A complete route should optionally generate and replay a scratch `example` before receiving `replayed` status.

## 15. Immediate name-search and freshness fixes

These changes should land before semantic P0 work.

### 15.1 Fix case and segmentation

- create `name_casefold` at index time;
- create `name_segments` using one shared normalization function;
- use a B-tree exact lookup before FTS;
- index normalized segments, not only the original camel-case token;
- add exact-name monotonicity tests;
- return `matchMode`: `exact-name`, `semantic-segments`, `signature`, or `fuzzy`;
- document AND/OR/phrase behaviour.

### 15.2 Stable collection key

- new result schema uses `results`;
- compatibility `index query` may retain `rows` for one transition;
- documentation and `jq` examples use `results` only.

### 15.3 Freshness

For semantic commands, default to full verification:

```text
index generation == current repository generation == Lean worker generation
```

Return `verified-fresh` only when all three match.

For lexical name search:

- `--freshness verify` hashes current supported inputs and returns verified status;
- `--freshness stored` retains the cheap `unchecked` state;
- never infer freshness from a prior process without an identity-bearing verification record.

## 16. Existing graph and SQLite performance fixes

These are independent of semantic search and can be merged early.

### 16.1 Theorem lineage duplicate traversal

Current lineage query logic computes walk rows and then recomputes them while building routes. Change route materialization to consume the already fetched bounded walk or bounded adjacency result.

Acceptance test: a trace callback proves one traversal acquisition per query.

### 16.2 Boundary-check N+1

Load trust targets and node boundary metadata in set-oriented queries before route classification. Do not execute one SQL statement per candidate endpoint.

Acceptance test: SQL statement count remains constant as returned route count grows.

### 16.3 ProofIR route N+1

Collect every distinct node ID from selected paths, fetch all node rows once, build a dictionary, and restore path order in Python.

Acceptance test: one node query per route request, not one per node.

### 16.4 Pure bounded graph module

Create `bounded_graph.py` with:

- compact integer node mapping;
- forward and reverse adjacency;
- bounded BFS/frontier expansion;
- cycle-safe path enumeration;
- SCC calculation;
- DAG unfolding with shared and cycle references;
- deterministic ordering and explicit omissions.

SQLite retrieves bounded rows; the pure module owns algorithmic traversal. This module is reusable by theorem lineage, ProofIR routes, constructor coverage, and the proof planner.

### 16.5 Dominators

Replace the current repeated-set-intersection implementation with Lengauer-Tarjan or another well-tested near-linear dominator algorithm.

Testing:

- hand-written diamonds, chains, disconnected nodes, multiple roots, and cycles;
- deterministic generated small graphs compared with a brute-force dominator oracle;
- cap and malformed-edge tests.

### 16.6 Compact database identities

Do not block P0 on a whole-schema identity rewrite. Use integer symbol IDs immediately for high-cardinality semantic dependency edges. Benchmark a broader module/declaration integer-key migration after P0.

### 16.7 SQLite finishing and table layout

During schema v4 benchmarking:

- use `WITHOUT ROWID` for pure composite-key edge tables;
- run `PRAGMA optimize` after build;
- inspect `ANALYZE` effects through query plans;
- benchmark page size and mmap settings rather than hard-coding them;
- retain `DELETE` journal and `FULL` synchronous mode for unpublished atomic builds unless evidence supports a safer alternative.

## 17. CLI startup reduction

The installed script currently imports the general CLI before delegated subcommand dispatch. Introduce a lightweight `entrypoint.py` and point the console script at it.

`entrypoint.py` should:

1. inspect the first argument;
2. import only the selected subcommand module;
3. import the general analysis CLI only for ordinary analyzer invocations.

Also:

- make ProofIR imports in `proof_search_cli.py` lazy inside `evidence` dispatch;
- keep `from ladon import main` as a lazy compatibility wrapper rather than importing `cli.py` at package import time;
- optionally add `ladon-proof-search` as a direct entrypoint without removing `ladon proof-search`.

Acceptance gate on the same benchmark host:

- at least 50% reduction in one-shot proof-search CLI overhead;
- no change in exit codes, stdout/stderr separation, or installed command behaviour.

## 18. Incremental semantic extraction

### 18.1 First correctness implementation

Reuse the current sound conservative cache boundary:

- toolchain;
- Lean version;
- helper and protocol;
- source;
- Lake state;
- transitive local import closure;
- compiled artifacts.

A changed transitive import may invalidate more modules than necessary, but must not produce a false hit.

### 18.2 Later precision improvement

Compute two public-surface fingerprints per module:

- `type_surface_fingerprint`
  - declaration names, kinds, and normalized types;

- `value_dependency_fingerprint`
  - direct value dependencies and relevant trust facts.

Type search invalidates on type-surface changes. Consumer and lineage evidence also invalidates on value-dependency changes.

### 18.3 Source-only modules

Discover source files from configured Lean source roots even when untracked or not imported. Store them as `source-only` modules with lexical declarations. Semantic status is explicit:

- `available`
- `stale-compiled-state`
- `source-only`
- `elaboration-failed`
- `unavailable`

A requested source root with no rows produces an omission record.

### 18.4 Dependency indexes

Start with one environment database for simplicity. If repeated Mathlib indexing dominates build cost or disk use, split cached dependency and project-overlay databases later and attach them read-only. This split is benchmark-gated and is not required for P0 correctness.

## 19. Work package and PR order

The order below minimizes semantic risk and keeps each PR reviewable.

### PR 1: Baseline contracts and benchmarks

Files:

- add proof-search benchmark harness;
- add JSON contract fixtures;
- add SQL trace-count utilities;
- add regression fixtures for mixed-case names and exact-name refinement.

Done when:

- current behaviour is captured;
- known failures reproduce as expected failures;
- baseline CLI, SQL, build-size, and route-query metrics are recorded.

### PR 2: Name search v2 and freshness contract

Files:

- `proof_search_name_query.py`
- `proof_search_scope.py`
- schema and index population changes;
- CLI compatibility adapter;
- docs and tests.

Done when:

- mixed-case exact names work;
- exact-name refinement is monotone;
- query modes and exclusions are explicit;
- `results` is canonical;
- freshness options are correct and tested.

### PR 3: CLI bootstrap and existing query optimization

Files:

- `entrypoint.py`
- lazy import changes;
- theorem lineage query refactor;
- ProofIR route materialization refactor;
- SQL trace tests.

Done when:

- no duplicate lineage walk;
- no boundary or path-node N+1;
- one-shot startup overhead is materially lower;
- current results remain contract-equivalent.

### PR 4: Pure bounded graph module and dominators

Files:

- `bounded_graph.py`
- `dominators.py`
- theorem lineage and ProofIR adapters;
- algorithm tests.

Done when:

- SQL is responsible for bounded row acquisition only;
- algorithms are deterministic and independently tested;
- old route/tree/bottleneck result contracts still pass.

### PR 5: Semantic schema v4 scaffolding

Files:

- schema version/generation bump;
- symbol dictionary;
- shapes, module semantic state, complete binders/dependencies/fields;
- schema validation and query-plan tests;
- incompatible-old-index status behaviour.

Done when:

- an empty v4 database validates;
- every required index and foreign key has a test;
- old v3 databases fail with a rebuild instruction rather than obscure SQL errors.

### PR 6: Semantic extraction protocol and Lean helper

Files:

- `lean_semantic_protocol.py`
- `lean_semantic_runtime.py`
- `ladon_semantic_index_helper.lean`
- cache integration;
- module fixtures and integration tests.

Done when:

- complete declaration, binder, dependency, structure, and field rows are extracted for the pinned Lean fixture;
- owner-module filtering prevents duplicate imported declarations;
- partial and malformed streams are handled honestly;
- process timeouts and cancellation clean up all children.

### PR 7: Semantic index build mode

Files:

- proof-search index orchestration;
- cached module assembly;
- coverage population;
- atomic publication and size-limit tests;
- build/status rendering.

Done when:

- `--mode semantic` produces a validated v4 database;
- unchanged modules are cache hits;
- changed source/import state invalidates soundly;
- previous generations survive failed builds.

### PR 8: Lean pattern elaboration and candidate verification

Files:

- `ladon_semantic_helper.lean`
- semantic query protocol operations;
- pattern and candidate result models;
- direct/reducible/symmetry checks.

Done when:

- one request elaborates a wildcard pattern and checks a batch of candidates;
- substitutions and residual goals are stable JSON;
- missing/stale candidates are explicit;
- helper limits and diagnostics are tested.

### PR 9: P0 type-directed search

Files:

- `proof_search_type_query.py`
- `proof_search_ranking.py`
- CLI command and renderers;
- result schema and tests.

Done when:

- complete type-search result contract is available;
- scope and ownership filters work;
- exact and residual-premise candidates are ranked deterministically;
- large-repository benchmark meets the interactive objective without rebuilding.

### PR 10: P0 premise and goal difference

Files:

- `proof_search_difference.py`
- generic structural diff;
- semantic registry core;
- one-level premise suggestions;
- route-card creation.

Done when:

- a non-closing candidate returns unmatched premises;
- equality orientation, definitional alias, projection, instance, and generic missing-premise cases are classified;
- every residual premise can carry verified discharge suggestions;
- unclassified differences remain honest.

### PR 11: P0 reverse consumers

Files:

- `proof_search_consumers.py`
- reverse indexes and queries;
- source/ownership filtering;
- completeness tests.

Done when:

- project-owned consumers of an exact declaration are returned with type/value distinction;
- empty results are only complete when dependency coverage is complete.

### PR 12: P0 constructor coverage and leakage

Files:

- `proof_search_constructor.py`
- structure/constructor helper operations;
- coverage classification;
- leakage checks;
- result schema and tests.

Done when:

- every field appears exactly once;
- direct, premised, restricted-boundary, unmatched, and unavailable states work;
- field-equivalent premise and projection dependency leakage are reported;
- the result can answer the PathBounds acceptance scenarios.

### PR 13: One-step adapter registry

Files:

- built-in adapter manifest;
- repository registry schema;
- adapter verification and ranking;
- documentation and fixtures.

Done when:

- adapters are advisory until Lean verifies their application;
- side conditions appear as residual goals;
- adapter direction and cost are explicit.

### PR 14: Bounded multi-step planner

Files:

- AND/OR state model;
- bounded best-first search;
- route replay integration;
- optional history sidecar.

Done when:

- routes are composed only from Lean-verified transitions;
- caps and omissions are complete;
- accepted and rejected route cards are reusable under exact fingerprints.

### PR 15: Documentation and release contract

Synchronize:

- `README.md`
- `docs/CLI.md`
- proof-search index documentation;
- the Lean Proof-Engineering Discovery TODO;
- installed CLI help;
- Codex Ladon skill;
- examples and `jq` snippets.

Done when documentation commands run in installed-contract tests and no example uses removed options.

## 20. Testing strategy

### 20.1 Python unit tests

Add:

```text
test_proof_search_name_v2.py
test_lean_semantic_protocol.py
test_semantic_index_schema.py
test_semantic_index_build.py
test_type_search.py
test_premise_difference.py
test_declaration_consumers.py
test_constructor_coverage.py
test_proof_route_cards.py
test_bounded_graph.py
test_dominators.py
```

Use fake semantic-helper payloads for most Python tests so failure classification and ranking remain fast and deterministic.

### 20.2 Lean integration fixture

Create a compact pinned project containing:

- exact theorem application;
- wildcard substitution;
- reducible alias;
- equality symmetry;
- coercion insertion;
- type-class synthesis;
- unresolved instance;
- missing inequality premise;
- `StronglyMeasurable`/`AEStronglyMeasurable` adapter case;
- structure with dependent fields;
- direct type and value consumers;
- direct projection leakage;
- field-equivalent premise leakage;
- source-only module.

### 20.3 Contract tests

For every public result schema:

- required fields;
- stable collection names;
- deterministic ordering;
- authority values;
- freshness identity;
- bounds and truncation;
- omission semantics;
- nonclaims.

### 20.4 SQL query-count tests

Use `sqlite3.Connection.set_trace_callback` to assert:

- lineage traversal acquisition count is constant;
- boundary metadata is set-oriented;
- ProofIR path node fetching is set-oriented;
- consumers are one indexed query plus bounded joins;
- type shortlist query count does not grow per candidate.

### 20.5 Algorithm differential tests

Compare bounded graph algorithms against small brute-force oracles. Avoid adding a runtime dependency solely for tests unless kept in the development group.

### 20.6 Failure injection

Test:

- stale source;
- stale toolchain;
- helper timeout;
- helper cancellation;
- malformed frame;
- missing terminal summary;
- source change during build;
- index size overflow;
- active and stale build locks;
- unavailable compiled state;
- incomplete structure extraction;
- candidate missing from current Lean environment;
- output byte cap.

### 20.7 Performance gates

Record on the same reference checkout:

- lexical and semantic cold-build time;
- semantic cache-hit rebuild time;
- database bytes;
- peak RSS;
- name-query internal time;
- SQL shortlist time;
- Lean worker startup/environment-load time;
- candidate verification time by candidate count;
- end-to-end type search p50 and p95;
- constructor coverage by field count;
- CLI one-shot overhead;
- SQL statement count.

Use relative regression gates where host variation makes absolute limits unreliable.

## 21. Acceptance scenario mapping

### Scenario 1

“Find every theorem in scope proving all-state release integrability for the four receiver lanes, and show which PathBounds fields remain unmatched.”

Required components:

- semantic type search;
- closure scope;
- deterministic ranking;
- structure field extraction;
- constructor coverage;
- field-level residual premises.

### Scenario 2

“Find a theorem proving corrector-state norm integrability for every natural row, even if the quantitative logarithmic bound is only available through a retained horizon.”

Required components:

- wildcard type pattern;
- residual inequality premise;
- quantitative versus adapter classification;
- boundary registry.

### Scenario 3

“Why does this retained-row bias integrability theorem not fill an all-row receiver field, and which lower-level declarations can remove the row guard?”

Required components:

- `explain` candidate application;
- row-guard residual classification;
- one-level type search for the residual premise;
- proof-route card.

### Scenario 4

“Which declarations consume PrimitivePathMoments, and does the terminal constructor still expose any of its fields?”

Required components:

- complete reverse type/value dependencies;
- project ownership filter;
- constructor binder and field extraction;
- certificate leakage analysis.

### Scenario 5

“Find the exact normalized-to-physical transport theorem and warn if the available result bounds chi / s instead of chi.”

Required components:

- repository semantic registry;
- one-step adapter verification;
- scale/representation mismatch classification.

This may land immediately after core P0 if repository-specific configuration is needed, but the architecture must support it from the first semantic-registry version.

### Scenario 6

“Given the current PathBounds constructor goal, produce a field coverage matrix with source links and unmatched assumptions.”

P0 supports explicit module, structure, arguments, and assumptions. Later goal capture supplies the exact editor context to the same constructor coverage engine.

## 22. Risks and mitigations

### Lean API instability

Mitigation:

- keep Lean code behind versioned helper protocols;
- pin an integration fixture;
- avoid exposing helper-internal expression encodings as public contracts;
- include Lean and helper identities in every cache and result.

### Semantic index size

Mitigation:

- integer symbol dictionary for dependency edges;
- bounded navigation text plus structural fingerprints;
- `WITHOUT ROWID` for composite edge tables;
- no duplicate imported declarations per module;
- benchmark before changing the default 512 MiB cap.

### Query latency dominated by Lean startup

Mitigation:

- one batched helper invocation per verification phase;
- lower Python CLI startup;
- cache semantic extraction;
- optional long-lived foreground session for editor/agent integrations after P0;
- do not run one Lean process per candidate.

### Misleading mismatch classifications

Mitigation:

- separate generic structural classes from registry classes;
- attach rule IDs and authority;
- retain `unclassified_expression_difference`;
- require Lean verification for adapter claims.

### Search explosion

Mitigation:

- SQL shortlist before Lean;
- explicit candidate caps;
- one-level premise suggestions in P0;
- bounded AND/OR search later;
- stable omission records.

### Stale index and current environment disagreement

Mitigation:

- semantic commands compare repository, index, and worker generation identities;
- fail closed by default;
- return missing/stale candidate rows rather than silently dropping them.

### Untrusted repository execution

Mitigation:

- lexical operations remain no-Lean;
- semantic operations are explicit;
- retain the existing initializer-execution warning;
- supervise process groups with finite limits;
- do not market semantic mode as safe untrusted-code analysis.

## 23. Final definition of done for P0

P0 is complete when all of the following hold:

1. A semantic SQLite generation stores complete Lean-owned declaration binders, direct dependencies, structures, fields, aliases, source links, and explicit coverage.
2. Type patterns with anonymous wildcards are elaborated in a selected module environment.
3. SQLite produces bounded candidates and Lean verifies them in batches.
4. Results report substitutions, residual premises, unresolved instances, owner modules, source locations, required scope/import information, match class, authority, freshness, and ranking rationale.
5. `explain` reports why a candidate fails or what remains after application, and suggests verified declarations for residual premises.
6. `consumers` reports complete reverse type/value consumers when coverage permits.
7. Constructor coverage emits one row per field, distinguishes direct/premised/restricted/unmatched states, and detects certificate leakage.
8. Mixed-case exact names and semantic-name refinement are correct and monotone.
9. Semantic results are `verified-fresh` only when repository, SQLite, and Lean worker generations agree.
10. Theorem lineage and ProofIR route queries no longer repeat traversals or issue per-node/per-boundary SQL queries.
11. Graph traversal and dominator algorithms are pure, bounded, deterministic, and independently tested.
12. The proof-search CLI starts materially faster without changing its process contract.
13. README, CLI documentation, installed help, examples, and the agent skill agree.
14. The six acceptance scenarios have executable fixtures or repository-backed acceptance scripts, with explicit omissions for any capability intentionally deferred beyond P0.
