## ADDED Requirements

### Requirement: Canonical bounded lineage projections
Ladon SHALL project one SQL-selected lineage subgraph into canonical nodes, edges,
roots, routes, collapses, repeated references, bottlenecks, bounds, and omissions.
Every projection MUST retain its closure identity, authority, freshness, filters,
and selected-subgraph fingerprint.

#### Scenario: External package collapse
- **WHEN** an external-package projection collapses non-trust external declarations
- **THEN** each collapsed row identifies the package or owner boundary, member and edge counts, and omitted-detail reason while trust roots remain individually visible

#### Scenario: Generated nodes are hidden
- **WHEN** compiler-generated nodes are excluded
- **THEN** the projection records the exclusion and reconnects or summarizes boundaries without pretending the generated dependencies were absent from the complete graph

### Requirement: Representative dependency spines
The projection service SHALL expose deterministic shortest dependency spines from
each selected root to the exact target, including node names, edge kinds, owner
modules, and source locations where available.

#### Scenario: Two trust axioms reach the theorem
- **WHEN** two trust roots have routes to the theorem
- **THEN** at least one stable shortest spine per root is returned within route caps and both end at the exact theorem identity

#### Scenario: Equal shortest routes exist
- **WHEN** several equal-depth routes connect one root and target
- **THEN** the selected route follows documented stable ordering and alternates are represented only within the configured bound

### Requirement: Mandatory bottlenecks
Ladon SHALL identify declarations that dominate the target in the selected
root-to-target subgraph. Dominator computation MUST run only on a SQL-selected
bounded SCC-condensed graph and MUST record the exact projection parameters.

#### Scenario: Shared lemma is mandatory
- **WHEN** every selected root-to-target route crosses one project lemma
- **THEN** that lemma appears in the bottleneck chain with its source evidence and domination scope

#### Scenario: Filter changes the answer
- **WHEN** type edges or generated nodes are excluded and the selected subgraph changes
- **THEN** bottlenecks are recomputed for the new subgraph and are not reused under the prior fingerprint

### Requirement: Reference-preserving tree unfolding
The optional tree view SHALL unfold the selected DAG with deterministic child order,
cycle guards, shared-node references, and separate depth, child, node, and byte caps.
It MUST NOT duplicate shared subgraphs as if they were distinct proof evidence.

#### Scenario: Diamond dependency
- **WHEN** two branches share a downstream declaration
- **THEN** the first occurrence is expanded and subsequent occurrences refer to the same canonical node identity

#### Scenario: Tree cap is reached
- **WHEN** unfolding exceeds any configured cap
- **THEN** the tree stops deterministically and records the controlling cap and omitted lower bound

### Requirement: Actual-proof nonclaim
Every projection SHALL state that dependency routes describe one compiled theorem
value and its type dependencies. The service MUST NOT label routes as all possible
proofs, alternative proofs, mathematical explanations, or a unique proof tree.

#### Scenario: Route view is rendered
- **WHEN** a user requests routes, spines, tree, or bottlenecks
- **THEN** output identifies the view as a projection of the Lean-authoritative dependency DAG and includes the alternative-proof nonclaim
