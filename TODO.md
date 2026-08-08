# Ladon TODO: Lean Proof-Engineering Discovery

This file records improvements that would make Ladon useful during active Lean
proof construction, in addition to its current architecture and review roles.
The motivating case is a large theorem repository where `rg` can find names but
cannot reliably answer questions about elaborated types, available adapters, or
the shortest route from existing declarations to a target field.

## P0: Type-Directed Declaration Search

- Add a fast command that searches declarations by an elaborated target type or
  partial type pattern, across the selected module's transitive import closure.
- Support metavariables/wildcards for parameters and propositions. A user should
  be able to ask for declarations shaped like:

  ```text
  Integrable (fun state => integral (releaseLaw ... state) ...) (stateLaw ... row)
  ```

  without knowing the declaration name or every implicit argument.
- Rank exact unification matches first, then matches requiring only symmetry,
  definitional unfolding, coercions, or a small number of standard adapters.
- Show the fully qualified name, owner module, elaborated type, source location,
  required imports, and the substitutions that matched the query.
- Allow restricting results to project-owned declarations, Mathlib, the current
  namespace, direct imports, or the complete transitive import closure.
- Keep a low-latency mode backed by a persistent declaration index. Interactive
  theorem discovery should normally return in a few seconds without rebuilding
  the target repository.

## P0: Premise and Goal Difference Analysis

- Given a goal type and a candidate declaration, report the unmatched premises
  instead of only saying that the theorem does not apply.
- Classify differences such as:
  - missing row or horizon inequalities;
  - all-state versus almost-everywhere hypotheses;
  - `StronglyMeasurable` versus `AEStronglyMeasurable`;
  - physical versus normalized state/law representations;
  - equality orientation or map/pushforward direction;
  - a field hidden behind a structure projection;
  - a result available only after unfolding a semantic alias.
- Suggest existing declarations that can discharge each unmatched premise.
- Detect when a candidate is stronger than the goal and when it is merely at a
  different indexing boundary.
- Emit a machine-readable proof-route card so review packets can preserve why a
  candidate was accepted or rejected.

## P0: Declaration Consumers and Constructor Coverage

- Add reverse declaration search: given a theorem or structure field, list the
  project-owned declarations that consume it, with source locations.
- For a structure such as `PathBounds`, report every field and classify it as:
  - already supplied by an in-scope declaration;
  - supplied only under stronger hypotheses;
  - supplied only for a restricted row range;
  - currently unmatched.
- For an attempted constructor, compare the local theorem inventory with the
  structure fields and generate a coverage matrix.
- Distinguish quantitative fields from measure-theoretic adapter fields. This
  matters when all-row integrability only needs existence while retained rows
  need a uniform numerical bound.
- Detect certificate leakage by showing when a proposed constructor still takes
  a field equivalent to the structure field it is meant to derive.

## P1: Semantic Name and Signature Search

- Add fuzzy search over declaration names, docstrings, namespaces, and elaborated
  signatures in one command.
- Normalize identifier queries consistently with the index. A fresh 2026-08-08
  index returned zero rows for the exact mixed-case names
  `fixedIndexPathExpression`, `scaleIndexedProducerAtIndex`, and
  `firstPrinciplesFixedStep_private_and_randomRowStationary_scaleIndexed`, but
  returned the expected declarations and signatures when the same query text
  was lowercased. Exact Lean names should be case-insensitive by default, or a
  zero-result query should automatically retry with the index normalization
  and report that rewrite.
- The same fresh generation returned zero rows for the exact structure name
  `DPAdamFixedBetaFirstPrinciplesPrivacyData` during stopped-region assembly,
  while a broad `trajectoryApproxDP` query returned many unrelated modules plus
  the desired terminal consumers. Structure declarations, nested namespace
  ownership, and exact-name retries should be first-class results so a simple
  missing `open` diagnosis does not require falling back to raw source search.
- Tokenize Lean names by semantic segments so searches for `all row corrector
  integrable` can find declarations such as
  `canonicalCorrector_release_integrable_all_state`.
- Support conjunctions and exclusions, not only OR substring filters.
- Rank project-local declarations above lexical collisions from unrelated
  modules and generated declarations.
- Group results by theorem family and indicate likely wrappers, mechanism-facing
  corollaries, generic authorities, and compatibility aliases.
- Integrate local failed-route evidence so rejected theorem routes are not
  repeatedly suggested without an explanation of what changed.
- Make token/ranking behavior stable under query refinement. In a fresh
  matrix-factorization index, the broad query `ActualFixedStepPoissonLedger
  PathBounds` returned the exact structure, while the exact follow-up query
  `PartialPathBounds` returned no rows even though a prior broader query had
  returned that declaration. Exact identifier fragments should be monotone:
  adding precision must not make a known exact-name candidate disappear.
- Document whether multi-token queries are AND, OR, phrase, or ranked-bag
  searches. The query `martingale bias energy lane integrable all row` returned
  no rows, while exact underscore queries found the martingale and bias owners.
  Agents cannot choose good query refinements without explicit semantics.
- Use one stable JSON collection key. Current query output stores candidates in
  `rows`; examples and ordinary expectations often suggest `results`. A compact
  schema reference or `jq` example would prevent successful searches from being
  mistaken for empty searches.

## P1: Proof Adapter Suggestions

- Recognize common Mathlib/Lean adapter patterns and suggest them with the exact
  candidate declarations involved:
  - `MeasurePreserving.integrable_comp` and map-integral transport;
  - `Kernel.integral_comp` / `Measure.integral_compProd`;
  - `Integrable.mono'`, finite-sum integrability, and constant majorants;
  - converting coordinatewise bounds to Euclidean norm bounds;
  - deriving outer integrability from a jointly integrable edge observable;
  - using equality almost everywhere to transport integrability;
  - normalizing arithmetic forms such as `E + E` versus `2 * E`.
- Keep suggestions explicitly advisory. Ladon should show the required side
  conditions and never present a text-level match as a compiled proof.

## P1: Better Scope Controls for Proof Work

- Add a theorem-discovery scope that includes the full transitive import closure,
  not only the root and direct context modules shown in the default owner report.
- Support an explicit set of roots for active proof work, including an unfinished
  owner plus likely authority modules.
- Show why a module or declaration was omitted from the effective scope.
- Provide a compact `proof-search` output mode that suppresses architecture
  smells and repository-wide lexical duplicate counts unless requested.
- Preserve architecture analysis as a separate mode rather than mixing module
  naming findings into a theorem-discovery query.

## P1: Lean-Aware Local Index

- Discover repository-owned `.lean` files from the source tree even when they
  are new, untracked, or not yet imported by a registered facade/module. Mark
  them as source-only candidates rather than omitting them. Active proof owners
  are often queried before their first consumer import exists.
- Provide an explicit omission row when a requested file root exists on disk but
  has no indexed module/declaration rows. A successful empty result currently
  looks indistinguishable from "the file contains no matching declaration."
- Corrected 2026-08-08 diagnosis: the apparently omitted untracked convergence
  owner was present after a fresh rebuild. Lowercased exact-name queries found
  declarations through line 1459, including newly added definitions and
  theorems. The misleading empty results came from query case normalization,
  not an extraction cutoff. Keep the requested-root omission diagnostics, but
  use a known lowercased exact identifier when testing untracked coverage.
- Materialize a versioned SQLite index containing:
  - fully qualified declaration names and kinds;
  - elaborated types and binder metadata;
  - owner modules and source ranges;
  - direct declaration dependencies when Lean can provide them;
  - namespace aliases and exported names;
  - structure fields and constructor relationships;
  - source and toolchain fingerprints.
- Incrementally refresh only modules whose source or imported declaration
  fingerprints changed.
- Mark index freshness honestly when indirect imports changed or when only a
  lexical fallback is available.
- Propagate verified freshness into query output. Immediately after a successful
  fresh build/status check, query responses still report `freshness:
  unchecked`; callers must manually correlate generation identities. Return
  `verified-fresh` when the query process has checked the same generation, or
  include the last verified status timestamp and identity explicitly.
- Expose the index through both CLI queries and a small JSON protocol suitable
  for coding agents and editor integrations.

## P2: Goal Capture and Interactive Queries

- Accept a Lean scratch file plus a line/column and extract the current goal and
  local context through Lean.
- Search candidates using both the goal and available local hypotheses.
- Report which local hypotheses satisfy which candidate binders.
- Support queries generated from a compiler error, especially type mismatches
  after simplification and unresolved field construction.
- Offer a command that emits a minimal scratch `example` importing the candidate
  owner and checking the proposed application. The scratch artifact must remain
  separate from production source.

## P2: Scale and Representation Awareness

- Let repositories register semantic representation pairs such as physical and
  normalized state, raw and centered temperature, or finite-row and stationary
  laws.
- Identify exact conjugacy/transport declarations between registered
  representations.
- Warn when a candidate controls a scaled object such as `chi / s` while the
  goal requires the physical object `chi`.
- Track whether a bound is fixed-index, finite-window uniform, or uniform over
  an unbounded parameter family.
- Surface hidden parameter growth rather than suggesting a common constant that
  would erase it.

## P2: Review-Packet Proof Frontier Output

- Generate a declaration-level frontier table containing:
  - compiled endpoints;
  - immediate consumers;
  - unmatched constructor fields;
  - theorem assumptions still entering from callers;
  - exact source and audit owners;
  - build/freshness status.
- Include accepted and rejected candidate routes with reasons.
- Compare two packet revisions and identify declaration-surface changes, not
  only module or file changes.
- Make this output consumable by the existing packet-evidence report without
  upgrading it to theorem authority.

## CLI and Documentation Contract

- Synchronize the installed CLI, `README.md`, `docs/CLI.md`, and the Codex Ladon
  skill. The current skill still recommends `--skip-build`, while the installed
  CLI rejects it and says that no-build analysis is now the default.
- Remove or clearly version deprecated `--output-json` / `--output-text` examples;
  the installed CLI recommends `--format` and `--output`.
- Make report-version selection explicit in examples. The current compatibility
  output warns that report v2 omits terminal phase dispositions and duplicates
  large payloads.
- Add one maintained proof-discovery example alongside the architecture examples.

## Acceptance Scenarios

Ladon should be considered materially more useful for active Lean proof work
when it can answer these queries from a large repository:

1. "Find every theorem in scope proving all-state release integrability for the
   four receiver lanes, and show which `PathBounds` fields remain unmatched."
2. "Find a theorem proving corrector-state norm integrability for every natural
   row, even if the quantitative logarithmic bound is only available through a
   retained horizon."
3. "Why does this retained-row bias integrability theorem not fill an all-row
   receiver field, and which lower-level declarations can remove the row guard?"
4. "Which declarations consume `PrimitivePathMoments`, and does the terminal
   constructor still expose any of its fields?"
5. "Find the exact normalized-to-physical transport theorem and warn if the
   available result bounds `chi / s` instead of `chi`."
6. "Given the current `PathBounds` constructor goal, produce a field coverage
   matrix with source links and unmatched assumptions."

These scenarios should use elaborated Lean information whenever available and
label lexical or heuristic fallbacks explicitly.
