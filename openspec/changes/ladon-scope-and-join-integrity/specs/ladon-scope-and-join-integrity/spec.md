## ADDED Requirements

### Requirement: Integrity overlay preserves existing owners
The scope-and-join integrity capability SHALL consume the scope populations and
root metadata owned by `ladon-analysis-root-and-scope-contract`, the
missing-import classifications owned by `ladon-signal-correctness`, and the
component signals and finding kinds owned by `ladon-architecture-correlator`.
It MUST NOT define a second scope planner, project-ownership model, graph metric
engine, or composite-finding taxonomy.

#### Scenario: Existing scope output is checked
- **WHEN** the existing scope planner supplies a selected population, contextual population, full discovered inventory, and root metadata
- **THEN** the integrity overlay checks boundary and reachability claims against those registered rows without changing which modules the scope planner selected

#### Scenario: Existing finding identity is retained
- **WHEN** an existing composite finding satisfies the integrity requirements
- **THEN** Ladon retains its owning finding kind and stable identity while adding join evidence rather than emitting a parallel integrity finding

### Requirement: Full-inventory-aware import boundaries
Import classification SHALL compare every selected import target with the full
discovered target inventory, not only with the selected primary and contextual
populations. A target present in the full inventory but omitted from the
selected slice MUST be classified as a `known_inventory_boundary` and MUST NOT
be counted as a missing internal import.

#### Scenario: Existing module lies outside owner context
- **WHEN** an owner-scoped module imports a target that is absent from the owner slice but present as an unambiguous module in the full discovered target inventory
- **THEN** Ladon reports a known-inventory boundary with the import source anchor and target identity and emits no missing-internal-import row for that site

#### Scenario: Project-owned target is genuinely absent
- **WHEN** a selected module imports a project-owned module identity that is absent from the full discovered target inventory under the existing ownership rules
- **THEN** Ladon preserves the existing internal missing-import classification with its lexical authority and source anchor

#### Scenario: External target remains external
- **WHEN** a selected module imports a target outside the discovered or configured project ownership boundary
- **THEN** Ladon preserves the existing external-boundary classification and does not reclassify it as either known-inventory or missing-internal

### Requirement: Rootless full-inventory analysis
Full-inventory analysis without an explicitly resolved navigation root SHALL be
rootless for reachability purposes. Ladon MUST NOT use a report anchor, first
module, inferred facade, top-level namespace, or other fallback identity as an
analysis root, and root-relative metrics and findings SHALL be marked not
applicable with a structured reason.

#### Scenario: Inventory request has no navigation root
- **WHEN** inventory scope selects all discovered target modules and the caller supplied no navigation root
- **THEN** the report records an empty resolved navigation-root set and marks unreachable-module counts, root closure, root pressure, and other root-relative outputs not applicable

#### Scenario: Report anchor is available
- **WHEN** a rootless inventory report has a display or report anchor for deterministic navigation
- **THEN** Ladon keeps that anchor separate from analysis roots and does not derive reachability or root-pressure evidence from it

### Requirement: Explicit inventory navigation roots
An explicitly requested and resolved navigation root SHALL provide only
auxiliary root-relative views over an inventory population. It MUST NOT narrow
the inventory scope or be described as an inferred analysis root. Reports
SHALL separate the inventory population, requested navigation roots, resolved
navigation roots, and root-relative coverage.

#### Scenario: Inventory has an explicit navigation root
- **WHEN** a caller requests inventory scope and explicitly supplies a navigation root that resolves inside the inventory
- **THEN** Ladon keeps the full inventory as the analysis population and labels closure, reachability, and root-pressure rows as auxiliary views attributed to that root

#### Scenario: Navigation root does not resolve
- **WHEN** a requested inventory navigation root cannot be resolved unambiguously
- **THEN** Ladon emits the existing structured root-resolution diagnostic and does not substitute another module or produce root-relative findings

### Requirement: Structural joins for composite findings
Every promoted composite finding SHALL cite an inspectable structural join
connecting all required component signals. Supported joins MUST be explicit
graph or identity relationships such as a shared subject, shared population
member, import or declaration edge, containment relation, closure membership,
or deterministic witness path. Merely selecting independent global maxima or
co-occurring values from the same report MUST NOT constitute a join.

#### Scenario: Components share a witnessed relationship
- **WHEN** component signals are connected by a registered subject identity, graph edge, closure membership, containment relation, or deterministic witness path required by the composite rule
- **THEN** Ladon SHALL promote the composite finding only with the join kind and resolvable component and witness references

#### Scenario: Global maxima are disconnected
- **WHEN** individually hot component signals concern subjects with no registered structural relationship required by the composite rule
- **THEN** Ladon retains the independent raw signals and emits no composite finding over them

#### Scenario: Join evidence is unavailable
- **WHEN** a projection or partial phase contains component summaries but lacks the rows needed to establish their required join
- **THEN** Ladon suppresses the composite or records it as an unavailable candidate and MUST NOT fabricate a relationship from names, ordering, or aggregate counts

### Requirement: Homogeneous composite aggregation
A composite headline count or score SHALL aggregate only values with the same
documented unit, population, scope, and denominator. Unlike measures SHALL
remain separate named component values, and Ladon MUST NOT add module counts,
edge counts, unreachable counts, source lines, declarations, or other
heterogeneous quantities into a synthetic evidence total.

#### Scenario: Homogeneous member count
- **WHEN** a composite rule counts distinct modules from one documented population and scope
- **THEN** Ladon SHALL report that deduplicated module count with its denominator and aggregation rule

#### Scenario: Component measures use different units
- **WHEN** a composite includes a closure-module count and a global fan-in edge count
- **THEN** Ladon preserves both named component measures separately and emits no summed headline count

#### Scenario: Component populations differ
- **WHEN** two component measures use different module populations or scopes even if both are integer counts
- **THEN** Ladon does not aggregate them unless an explicit homogeneous joined population is derived and exposed

### Requirement: Join evidence and authority preservation
Every boundary classification and composite join SHALL carry stable pointers to
the canonical source, scope, module-DAG, declaration-graph, or finding rows from
which it was derived. The resulting authority MUST be no stronger than the
required component evidence and join evidence, and graph correlation MUST NOT
be presented as Lean elaboration, theorem truth, proof failure, or defect
confirmation.

#### Scenario: Lexical boundary classification
- **WHEN** a text-backed import site is classified against a discovered inventory module identity
- **THEN** the boundary row points to the import site, inventory identity, and scope-population evidence and remains explicitly lexical and Ladon-derived

#### Scenario: Composite mixes authority levels
- **WHEN** a composite joins components with different evidence authorities
- **THEN** the composite preserves each component authority and reports an overall authority no stronger than the weakest evidence required for promotion

#### Scenario: Evidence pointer cannot resolve
- **WHEN** a required component or join pointer does not resolve in the canonical report
- **THEN** Ladon treats the composite as invalid or unavailable and does not promote it

### Requirement: Portable scope-and-join regression fixtures
Required regression gates SHALL use tracked, target-neutral fixtures containing
positive and intentional negative cases for inventory boundaries, rootless and
explicitly rooted inventory views, structural joins, homogeneous aggregation,
and evidence authority. Mutable external repositories MUST remain optional
observational evidence.

#### Scenario: Portable positive fixture
- **WHEN** the required fixture contains an out-of-slice known import, a rootless inventory, an inventory with an explicit navigation root, and structurally joined component signals
- **THEN** the gate verifies known-boundary classification, not-applicable root metrics, auxiliary rooted views, resolvable join pointers, homogeneous measures, and preserved authority

#### Scenario: Portable negative fixture
- **WHEN** the required fixture contains a genuinely absent internal import, disconnected global hotspots, mixed-unit component counts, an unresolved navigation root, and a dangling join pointer
- **THEN** the gate verifies truthful missing-import classification, no inferred root, no disconnected composite, no heterogeneous sum, and no promoted finding with unresolved evidence

#### Scenario: Optional live observation
- **WHEN** the same checks are repeated against a mutable large Lean repository
- **THEN** the result records repository and analyzer fingerprints and remains non-required observational evidence without introducing target-specific production rules
