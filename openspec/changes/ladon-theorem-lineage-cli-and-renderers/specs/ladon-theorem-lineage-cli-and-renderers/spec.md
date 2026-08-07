## ADDED Requirements

### Requirement: Ordinary theorem-lineage command
The installed CLI SHALL expose `ladon theorem lineage THEOREM` for people, scripts,
editors, and models with identical defaults and evidence. It SHALL accept repository,
index, view, boundary, root, edge-kind, generated-node, bound, refresh, resource,
format, and output options through documented parser choices.

#### Scenario: Common theorem-name query
- **WHEN** a user supplies a fully qualified theorem with no advanced view options
- **THEN** the command returns bounded representative routes from stored exact lineage using the ordinary documented defaults

#### Scenario: No caller-specific behavior
- **WHEN** the same argv and repository/index bytes are used by different callers
- **THEN** result identities, rows, bounds, exits, and nonclaims are identical

### Requirement: Explicit database refresh policy
The command SHALL query a compatible fresh stored closure first. `--refresh` MUST
support `missing`, `stale`, `always`, and `never`; any planner execution and database
ingestion MUST be visible in progress and result metadata.

#### Scenario: Fresh stored closure exists
- **WHEN** the default refresh policy finds a compatible fresh closure
- **THEN** the command starts no Lean/Lake process and answers from SQLite

#### Scenario: Closure is missing under default policy
- **WHEN** the base index is compatible but the theorem closure is absent and refresh is `missing`
- **THEN** the command runs the existing supervised theorem planner, validates and ingests the result, then performs the SQL query

#### Scenario: Stale closure with refresh disabled
- **WHEN** the closure is stale and refresh is `never` or `missing`
- **THEN** the command exits operationally with the stale class and a concrete refresh instruction without querying stale edges

### Requirement: Versioned text and JSON results
The command SHALL render one typed result as compact text or canonical versioned
JSON. Both representations MUST preserve theorem and closure identity, freshness,
authority, query parameters, bounds, routes, projection metadata, omissions,
truncation, timing split, source locations, and nonclaims.

#### Scenario: Text and JSON parity
- **WHEN** the same query is rendered in text and JSON
- **THEN** target, root, route, bottleneck, count, omission, and truncation facts agree

#### Scenario: Dense graph JSON is capped
- **WHEN** graph view exceeds node, edge, or report-byte limits
- **THEN** JSON remains valid, identifies the controlling caps, and does not silently drop rows

### Requirement: Stable process and stream behavior
Usage errors MUST exit 2, operational/index/planner failures MUST exit 1, and
completed queries MUST exit 0 even when bounded. Report bytes SHALL use the selected
output; progress, refresh, and diagnostics SHALL use stderr. Signals MUST supervise
and reap planner helpers.

#### Scenario: Invalid option combination
- **WHEN** a boundary requiring explicit roots receives none
- **THEN** the command emits a concise stderr usage error, writes no partial report, and exits 2

#### Scenario: Refresh is interrupted
- **WHEN** the process receives a termination signal while planning
- **THEN** the helper process group is terminated and reaped and no partial closure is activated

### Requirement: Honest command language
Help and output MUST call the result a theorem dependency lineage or bounded DAG
unfolding and MUST distinguish actual compiled-proof routes from possible alternative
proofs. No lexical edge may appear with Lean authority.

#### Scenario: Tree view help
- **WHEN** a user opens help for tree view
- **THEN** help explains shared-node references, finite caps, and that the view is not a unique or exhaustive proof tree
