## Context

Ladon's existing scope planner selects primary and contextual module
populations, while the module-DAG and architecture correlator derive boundary,
reachability, and composite-finding evidence. A large-repository trial exposed
three integrity failures at those seams:

- missing-import analysis compared targets only with the selected module map, so
  imports into known but out-of-slice modules appeared absent;
- inventory analysis used a deterministic report anchor as an implicit
  reachability root even though inventory selection had no resolved root; and
- composite correlators independently selected hot rows, promoted disconnected
  subjects, and summed measures with different units.

The child packet follows the umbrella dependency ledger. It starts after the
`ladon-report-coverage-and-snapshot-integrity#coverage-foundation` milestone and
integrates with
`ladon-analysis-root-and-scope-contract`, `ladon-signal-correctness`, and
`ladon-architecture-correlator`, and enables the declaration/audit integrity and
analysis-inspection packets. Those existing capabilities retain ownership of
scope selection, missing-import semantics, graph metrics, finding kinds, and
stable finding identity.

All evidence in this packet is graph or lexical navigation evidence. It does not
establish Lean resolution, elaboration, theorem truth, proof failure, or defect
confirmation.

## Goals / Non-Goals

**Goals:**

- Distinguish selected modules, known discovered inventory, and external or
  genuinely absent import targets.
- Make inventory reachability rootless by default and preserve explicitly
  requested navigation roots without narrowing inventory selection.
- Require inspectable structural joins and resolvable evidence pointers for
  every promoted composite.
- Give each composite measure one documented unit, population, scope, and
  denominator.
- Preserve the weakest required evidence authority through boundary and
  composite rows.
- Gate the behavior with small tracked positive and intentional negative
  fixtures.

**Non-Goals:**

- No second scope planner, module ownership model, module-DAG engine, finding
  taxonomy, or stable-identity scheme.
- No automatic import expansion, import rewriting, root-selection policy, or
  mathematical-relevance inference.
- No project-specific module names, thresholds, or Matrix-Factorization CI
  dependency.
- No new smell categories or Lean-semantic claims.

## Decisions

### 1. Retain full-inventory identity alongside the selected module map

The existing source index remains authoritative for discovered internal module
identities. Run-local analysis state will retain its normalized module-name set,
source-index fingerprint, and scope-plan identity alongside the backend-selected
module map. Module-DAG summarization will receive both populations explicitly.

The existing missing-import classifier continues to own the
`missing_internal_import` signal. The integrity layer adds the distinction needed
before that classifier runs:

- a target in the selected map is selected internal;
- a target absent from the slice but present in the fingerprint-matched source
  index is a `known_inventory_boundary`;
- a target outside configured/discovered ownership remains external; and
- only a project-owned target absent from the full inventory remains missing.

Boundary rows point to the import site, inventory identity, and selected scope.
The implementation will not expand owner scope merely to make imports visible,
because doing so would destroy the bounded-slice contract.

Alternative considered: infer inventory membership from top-level namespace
names. This repeats ownership logic and cannot distinguish an absent module from
an intentionally external namespace.

### 2. Separate selection roots, navigation roots, and report anchors

The scope owner will use its existing resolver and diagnostic vocabulary for an
optional inventory navigation root. Inventory primary population remains every
indexed module. The scope payload will expose requested and resolved navigation
roots separately from the population and from any deterministic report/display
anchor.

`analysis_module_roots` will return:

- the existing resolved roots for rooted scopes;
- explicitly resolved navigation roots for inventory auxiliary views; or
- an empty tuple for rootless inventory.

Module-DAG reachability will no longer substitute graph roots or a report anchor
when that tuple is empty. Root-relative output will use a structured
applicability envelope containing status, reason, roots, population, and
coverage. Root-derived findings are suppressed when the envelope is not
applicable. This makes “not requested” distinct from “zero unreachable”.

Alternative considered: retain the fallback and rename it a convenience root.
That still turns a display choice into architecture evidence and contradicts the
scope diagnostics.

### 3. Make import-boundary derivation a typed, evidence-linked result

Boundary classification will be a deterministic operation over canonical import
sites, selected identities, full-inventory identities, and the existing project
ownership predicate. It will return typed rows rather than encode all states as
absence from one mapping. Summary counts and renderers will preserve the row
types and bounded coverage independently.

Every row carries lexical authority and stable source/scope references. A stale
or mismatched source-index fingerprint makes inventory membership unavailable
rather than silently falling back to selected-slice semantics.

Alternative considered: pass only a set of additional “not missing” names into
the old function. That would remove the false positive but lose the
known-boundary evidence needed for inspection and coverage accounting.

### 4. Declare and evaluate structural join plans inside existing correlators

Each existing composite rule will state its required relationship using canonical
row identities and graph data already owned by its source analysis. Supported
relationships include same subject, membership in a root/import closure, an
import or declaration edge, containment, or a deterministic witness path.

Correlators will enumerate qualifying pairs in stable order and select the
strongest joined candidate; they will not independently select global maxima.
For import pressure, for example, a fan-in subject must be a member of the cited
root/direct-import closure. Full membership is checked against the canonical
graph before projection; a bounded sample is never treated as complete join
evidence.

Promoted findings retain their owning kind, subject rules, and stable identity.
They add a join record containing join kind, component references, witness
references, scope/population identity, and authority. If required rows or
pointers are unavailable, the correlator suppresses promotion or emits a
non-finding unavailable diagnostic.

Alternative considered: keep disconnected composites and add explanatory text.
The prioritization would still be unsupported, so a disclaimer would not repair
the evidence.

### 5. Replace synthetic sums with typed component measures

`component_signals` remain independently named measures. A headline `count` or
score is emitted only when the rule derives a deduplicated homogeneous
population with one unit, scope, population, and denominator. Otherwise the
finding renders the named components without adding them.

The finding workflow and renderers will tolerate a composite without a numeric
headline and display component units explicitly. Existing IDs remain stable
because the owning finding kind and canonical subject remain unchanged.

Alternative considered: choose one arbitrary component as the headline count.
That would preserve a numeric field but make its meaning vary by finding kind
without a declared measure contract.

### 6. Preserve evidence authority and validate pointers before promotion

Boundary and join rows keep typed references to canonical source-index,
scope-plan, module-DAG, declaration-graph, or finding rows. Promotion validates
that every required pointer resolves in the unprojected canonical report.
Overall authority is no stronger than the weakest component and join witness
required by the rule; individual component authorities remain visible.

Projection may omit display rows after a finding is formed, but it must retain
stable canonical references and truthful coverage. A partial input that cannot
prove its join is not sufficient to recreate the composite in an atlas or other
consumer.

Alternative considered: accept aggregate section pointers. They cannot prove
which subjects were joined and permit the same false correlation to recur.

### 7. Use portable positive and negative fixtures as release authority

A tracked target-neutral fixture will include:

- an owner slice importing both a known out-of-slice module and a genuinely
  absent project module;
- rootless inventory, explicitly rooted inventory, and unresolved navigation
  root cases;
- joined and disconnected hot signals;
- homogeneous and mixed-unit component measures; and
- valid and dangling evidence pointers with mixed authority levels.

Unit tests cover the pure classifiers and join predicates. Pipeline, report,
renderer, installed-candidate, and strict OpenSpec gates cover end-to-end
behavior. A live Matrix-Factorization rerun is optional, read-only, fingerprinted
observational evidence only.

## Risks / Trade-offs

- **[Risk] Existing consumers assume every composite has an integer `count`.**
  → Update the canonical finding schema and renderers together, retain named
  component measures, and add compatibility tests before removing synthetic
  sums.
- **[Risk] Full closure membership could increase correlator work.**
  → Reuse the existing adjacency map, cache deterministic reachability sets per
  root/direct-import pair for the analysis run, and project only bounded
  witnesses.
- **[Risk] Navigation-root terminology could be confused with selection.**
  → Expose separate fields and diagnostics and add invariants proving inventory
  primary population is unchanged.
- **[Risk] A stale inventory set could suppress a real missing import.**
  → Require matching source-index and scope fingerprints; on mismatch, mark
  classification unavailable rather than guessing.
- **[Risk] Suppressing formerly promoted findings changes calibration output.**
  → Update fixtures to include both a real joined positive and a disconnected
  negative, and version any persisted baseline that relies on the old false
  correlation.

## Migration Plan

1. Add full-inventory and navigation-root metadata to run-local and scope payloads
   while preserving selected populations and existing owner diagnostics.
2. Introduce typed boundary rows and root-applicability output, then update
   renderers and installed contracts.
3. Add structural join evaluation and evidence validation to the existing
   correlator functions; remove synthetic heterogeneous sums.
4. Update calibration fixtures and report consumers to require join evidence and
   tolerate composites without a headline count.
5. Run focused unit and pipeline suites, the installed-candidate gate, full test
   suite, lint/type checks, and strict OpenSpec validation.

Rollback consists of reverting the packet as one schema-and-consumer change.
Partially restoring implicit roots or disconnected composites is not a supported
compatibility mode because it would restore false evidence.

## Open Questions

None are blocking. Exact additive field names and report-schema placement will be
chosen during implementation against the existing report-contract helpers; the
normative separation, authority, and applicability semantics are fixed by the
specification.
